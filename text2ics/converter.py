from importlib.metadata import version
from typing import TYPE_CHECKING

import icalendar
from dotenv import load_dotenv
from litellm.exceptions import RateLimitError
from promptic import Promptic
from rich import print  # noqa A004
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from text2ics.system_prompt import prompt as sys_prompt

if TYPE_CHECKING:
    from icalendar import Component

load_dotenv()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff
    stop=stop_after_attempt(5),  # Retry up to 5 times
    retry=retry_if_exception_type(RateLimitError),  # Retry on rate limit errors
)
def call_llm_with_retry(promptic: Promptic, content: str, language: str|None = None) -> str:
    """
    Call the LLM with retry logic for handling rate limits.
    """
    output_language = (
        f"the produced calendar content language must be in {language}"
        if language is not None
        else "Output language must be the same as the dominant language of the event content"
    )

    response = promptic.completion(
        messages=[
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": (
                    f"""Extract the events from the <INPUT>...</INPUT> section and output as a raw ICS text block containing all event described in the text

                    OUTPUT_LANGUAGE: {output_language}

                    <INPUT>{content}</INPUT>"""
                ),
            },
        ]
    )

    combined_content = "\n".join(choice.message.content for choice in response.choices)
    return combined_content


def process_content(content: str, api_key: str, model: str, language: str|None = None) -> "Component":
    """
    Process the content using the LLM and ensure the generated ICS calendar is valid.
    Retries until a valid calendar is produced.
    """
    # Initialize a Promptic instance with the dynamic API key and model
    promptic = Promptic(model=model, api_key=api_key)
    complete = False
    ics_calendar_str = ""
    while not complete:
        try:
            # Call the LLM with retry logic
            ics_calendar_str = call_llm_with_retry(promptic, content, language)

            # Validate the generated ICS calendar by parsing it.
            icalendar.Calendar.from_ical(ics_calendar_str)
            complete = True
        except ValueError:
            print("The produced calendar event is not valid, retrying...")
        except RateLimitError as e:
            print(f"Rate limit error encountered: {e}, retrying...")

    calendar = icalendar.Calendar.from_ical(ics_calendar_str)
    calendar["PRODID"] = f"-//jgalabs//text2ics {version('text2ics')}//EN"
    return calendar
