import os
import typer
from rich import print
from promptic import Promptic
from pathlib import Path
from typing_extensions import Annotated
from dotenv import load_dotenv
from system_prompt import prompt as sys_prompt
import icalendar
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from litellm.exceptions import RateLimitError
from importlib.metadata import version

load_dotenv()

app = typer.Typer()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff
    stop=stop_after_attempt(5),  # Retry up to 5 times
    retry=retry_if_exception_type(RateLimitError),  # Retry on rate limit errors
)
def call_llm_with_retry(promptic: Promptic, content: str, language: str = None) -> str:
    """
    Call the LLM with retry logic for handling rate limits.
    """
    output_language = (
        language
        if language is not None
        else "Output language must be the same as the dominant language of the event content"
    )

    response = promptic.completion(
        messages=[
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": f"Extract events from the following content and generate an ICS calendar file:\n{output_language}",
            },
        ]
    )
    return response.choices[0].message.content


def process_content(content: str, api_key: str, language: str = None) -> str:
    """
    Process the content using the LLM and ensure the generated ICS calendar is valid.
    Retries until a valid calendar is produced.
    """
    # Initialize a Promptic instance with the dynamic API key and model
    promptic = Promptic(model="gpt-4.1-nano", api_key=api_key)
    complete = False
    ics_calendar = ""

    while not complete:
        try:
            # Call the LLM with retry logic
            ics_calendar = call_llm_with_retry(promptic, content, language)

            # Validate the generated ICS calendar
            calendar = icalendar.Calendar.from_ical(ics_calendar)
            complete = True
        except ValueError:
            print(
                f"The produced calendar event is not valid, retrying: {ics_calendar}"
            )
        except RateLimitError as e:
            print(f"Rate limit error encountered: {e}, retrying...")

    calendar["PRODID"] = f"-//jgalabs//text2ics {version('text2ics')}//EN"
    return calendar.to_ical()


def check_config() -> bool:
    """
    Check if any of the required API keys are set in the environment.
    """
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    key_is_set = any(os.environ.get(key) for key in api_keys)
    return key_is_set


@app.command()
def main(
    input: Annotated[Path, typer.Argument()],
    api_key: Annotated[str, typer.Option(..., envvar="TXT2ICS_API_KEY")],
    language: Annotated[
        str, typer.Option(None, help="Specify the output language for the ICS file.")
    ] = None,
):
    """
    Main entry point for the application. Reads input text, processes it, and prints the generated ICS calendar.
    """
    with open(input) as f:
        text_from_file = f.read()

    ics_calendar = process_content(text_from_file, api_key, language)
    print(ics_calendar)


if __name__ == "__main__":
    app()
