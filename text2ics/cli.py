import typer
from pathlib import Path
from typing_extensions import Annotated
from rich import print


app = typer.Typer()


@app.command()
def main(
    input: Annotated[
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
            envvar="TXT2ICS_API_KEY",
            help="API key for the LLM service.",
        ),
    ],
    language: Annotated[
        str,
        typer.Option(help="Specify the output language for the ICS file. is not set language is guessed from content"),
    ] = None,
):
    """
    Reads input text from a file, processes it to generate an ICS calendar, and prints the result.
    """
    from .converter import process_content

    with open(input, "r", encoding="utf-8") as f:
        text_from_file = f.read()

    ics_calendar = process_content(text_from_file, api_key, language)
    print(ics_calendar)


if __name__ == "__main__":
    app()
