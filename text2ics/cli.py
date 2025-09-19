from pathlib import Path

import typer
from rich import print  # noqa A004
from typing_extensions import Annotated

app = typer.Typer()

@app.command()
def main(
    text_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Path to the input text file.",
        ),
    ],
    api_key: Annotated[
        str,
        typer.Option(
            ...,
            envvar=[f"{vendor}_API_KEY" for vendor in ["OPENAI", "CLAUDE", "GEMINI", "TEXT2ICS"]],
            help="API key for the LLM service.",
        ),
    ],
    model: Annotated[str, typer.Option(help="What model to use.")] = "gpt-5",
    language: Annotated[
        str,
        typer.Option(
            help="Specify the output language for the ICS file. Defaults to autodetection"
        ),
    ] = None,
):
    """
    Reads input text from a file, processes it to generate an ICS calendar, and prints the result.
    """
    from .converter import process_content

    with open(text_file, "r", encoding="utf-8") as f:
        text_from_file = f.read()

    ics_calendar = process_content(
        content=text_from_file, api_key=api_key, model=model, language=language
    )
    print(ics_calendar.to_ical().decode("utf-8"))

