import os
from rich import print
from promptic import Promptic
from dotenv import load_dotenv
from text2ics.system_prompt import prompt as sys_prompt
import icalendar
from icalendar import Calendar
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from litellm.exceptions import RateLimitError
from importlib.metadata import version

load_dotenv()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff
    stop=stop_after_attempt(5),  # Retry up to 5 times
    retry=retry_if_exception_type(RateLimitError),  # Retry on rate limit errors
)
def call_llm_with_retry(
    promptic: Promptic, content: str, language: str = None
) -> str:
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
                "content": f"Extract events from the following content and generate an ICS calendar file:\n{content}\n{output_language}",
            },
        ]
    )
    return response.choices[0].message.content


def process_content(
    content: str, api_key: str, model: str, language: str = None
) -> Calendar:
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
