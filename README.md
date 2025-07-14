# text2ics

A Python tool to convert unstructured text into an ICS calendar file using an LLM.
It provides both a command-line interface (CLI) and a Streamlit web application.

![Preview](https://github.com/jakob1379/text2ics/blob/main/preview.gif)

## Installation
Ensure you have Python installed, then clone the repository and install the dependencies.

```bash
# using pip
pip install text2ics

# or run directly with uv
uvx text2ics
```

You will also need an API key for a compatible LLM service (like OpenAI).

## Usage

### Command-Line Interface (CLI)

The CLI allows you to convert a text file to an ICS file directly. Set your API key as an environment variable first.

```bash
export <OPENAI|CLAUDE|GEMINI>_API_KEY="your-api-key"
text2ics path/to/your/textfile.txt > events.ics
```

For more options, run `text2ics --help`.

### Streamlit Web App

The web app provides an interactive way to convert text.

```bash
streamlit run app/app.py
```

Open your browser to the URL provided by Streamlit to use the application.

## Development
This project uses `uv` for dependency management and `poethepoet` for running tasks.

Install all dependencies, including for development:
```bash
uv sync --all-extras
```

Run common development tasks:
```bash
Configured tasks:
poe fmt                   Formats the code using Ruff.
poe lint                  Checks the code for linting issues and fixes them using Ruff.
poe check                 Performs type checking using Pyright.
poe test                  Runs the test suite using Pytest.
poe all                   Runs all tasks: fmt, lint, check, and test.
poe ci:fmt                Checks if the code is properly formatted using Ruff.
poe ci:lint               Checks the code for linting issues without fixing them.
poe app                   Runs the Streamlit app with live reload enabled.
```

