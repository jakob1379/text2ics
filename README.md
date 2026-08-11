# text2ics

A Python tool to convert unstructured text into an ICS calendar file using an LLM.
It provides both a command-line interface (CLI) and a Streamlit web application.

![Preview](https://github.com/jakob1379/text2ics/blob/main/preview.gif)

## How it works

The LLM does one job: extract events into a typed schema. Everything else is plain
Python.

```text
text ──▶ EventExtractor (nooa agent) ──▶ list[Event] ──▶ icalendar ──▶ .ics
             LLM, ~6 line prompt          Pydantic       deterministic
```

Because the model never writes ICS itself, the prompt needs no rules about UIDs,
`DTSTAMP`, CRLF, escaping or line folding — the `icalendar` library handles those,
and the output is valid by construction. That is what keeps the prompt short enough
for small models to follow. Timezones, default durations and past-midnight end
times are also resolved in Python rather than asked of the model.

Extraction is built on [nooa](https://github.com/NVIDIA-NeMo/labs-OO-Agents)
(NVIDIA-labs OO Agents), where the method docstring *is* the prompt and the return
annotation *is* the output contract — see `text2ics/agent.py`.

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

`poe test` is offline and free. To check the prompt against real models, run the
eval harness — it scores extraction against the fixtures in `tests/data` and
**costs API credits**, so it is a script rather than a test:

```bash
uv run python tests/eval_models.py                 # default small-model set
uv run python tests/eval_models.py gpt-4o-mini     # specific models
EVAL_REPEAT=5 uv run python tests/eval_models.py   # repeat to measure flakiness
```

Repeat runs matter: weak models fail intermittently, so a single green run says
little. Change the prompt in `text2ics/agent.py`, then re-run this before and
after — wording that reads like an improvement often measures as a regression.
