import os
import typer
from rich import print
from promptic import Promptic
from pathlib import Path
from typing_extensions import Annotated
from dotenv import load_dotenv
from system_prompt import prompt as sys_prompt
import icalendar

load_dotenv()

app = typer.Typer()


def process_content(content: str, api_key: str) -> str:
    """
    Process the content using the LLM and ensure the generated ICS calendar is valid.
    Retries until a valid calendar is produced.
    """
    # Initialize a Promptic instance with the dynamic API key and model
    promptic = Promptic(model="gpt-4.1-nano", api_key=api_key)
    complete = False
    ics_calendar = ""

    while not complete:
        # Call the LLM function dynamically
        response = promptic.completion(
            messages=[
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": f"Extract events from the following content and generate an ICS calendar file:\n{content}",
                },
            ]
        )
        ics_calendar = response.choices[0].message.content

        # Validate the generated ICS calendar
        try:
            icalendar.Calendar.from_ical(ics_calendar)
            complete = True
        except ValueError:
            print(f"The produced calendar event is not valid, retrying: {ics_calendar}")

    return ics_calendar


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
):
    """
    Main entry point for the application. Reads input text, processes it, and prints the generated ICS calendar.
    """
    with open(input) as f:
        text_from_file = f.read()

    ics_calendar = process_content(text_from_file, api_key)
    print(ics_calendar)


if __name__ == "__main__":
    app()
