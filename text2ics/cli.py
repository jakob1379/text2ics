import os
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from text2ics.models import DEFAULT_MODEL, env_var_for_model

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
        str | None,
        typer.Option(
            # Deliberately not a list of envvars: typer takes the first one that
            # is set, so exporting OPENAI_API_KEY and then asking for a Claude
            # model would send the OpenAI key to Anthropic. The key is resolved
            # from the model's own provider below instead.
            envvar="TEXT2ICS_API_KEY",
            help="API key. Defaults to the variable for the chosen model's provider.",
        ),
    ] = None,
    model: Annotated[
        str,
        typer.Option(help="Model to use. Any litellm model id works; see text2ics/models.py."),
    ] = DEFAULT_MODEL,
    language: Annotated[
        str | None,
        typer.Option(
            help="Specify the output language for the ICS file. Defaults to autodetection"
        ),
    ] = None,
):
    """
    Reads input text from a file, processes it to generate an ICS calendar, and prints the result.
    """
    from .converter import process_content

    if api_key is None:
        variable = env_var_for_model(model)
        api_key = os.environ.get(variable) if variable else None
    if not api_key:
        expected = env_var_for_model(model) or "the provider's API key variable"
        raise typer.BadParameter(f"No API key for {model!r}. Export {expected}, or pass --api-key.")

    with open(text_file, "r", encoding="utf-8") as f:
        text_from_file = f.read()

    ics_calendar, _ = process_content(
        content=text_from_file, api_key=api_key, model=model, language=language
    )
    # Raw stdout, not rich.print: ICS is machine-readable and must not be wrapped.
    sys.stdout.write(ics_calendar.to_ical().decode("utf-8"))
