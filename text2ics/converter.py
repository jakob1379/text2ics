import os
import typer
from rich import print
from promptic import llm
from pydantic import Field, BaseModel, field_validator
from datetime import datetime
from typing import Optional
from pathlib import Path
from typing_extensions import Annotated
from dotenv import load_dotenv
from system_prompt import prompt
load_dotenv()

app = typer.Typer()


@llm(model="gpt-4.1-nano", system=prompt)
def ics_from_text(text: str) -> str:
    """convert the text to a ics calendar event: {text}"""


def check_config() -> bool:
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    key_is_set = any(os.environ.get(key) for key in api_keys)
    return key_is_set


@app.command()
def main(
    input: Annotated[Path, typer.Argument()],
):
    with open(input) as f:
        text_from_file = f.read()

    event = ics_from_text(text_from_file)
    print(event)


if __name__ == "__main__":
    app()
