import os
import typer
from rich import print
from promptic import llm, Promptic
from pydantic import Field, BaseModel, field_validator
from datetime import datetime
from typing import Optional
from pathlib import Path
from typing_extensions import Annotated
from dotenv import load_dotenv
from system_prompt import prompt as sys_prompt
from litellm import litellm

load_dotenv()

app = typer.Typer()


@llm(model="gpt-4.1-nano", system=sys_prompt)
def ics_from_text(text: str) -> str:
    """
    Extract events from the following content and generate an ICS calendar file:
    {text}
    """


def process_email(content: str, api_key: str):
    # Initialize a Promptic instance with the dynamic API key and model
    promptic = Promptic(model="gpt-4.1-nano", api_key=api_key)

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
    return response.choices[0].message.content


def check_config() -> bool:
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    key_is_set = any(os.environ.get(key) for key in api_keys)
    return key_is_set


@app.command()
def main(
    input: Annotated[Path, typer.Argument()],
    api_key: Annotated[str, typer.Option(..., envvar="TXT2ICS_API_KEY")],
):
    with open(input) as f:
        text_from_file = f.read()

    ics_calendar = process_email(text_from_file, api_key)
    print(ics_calendar)


if __name__ == "__main__":
    app()
