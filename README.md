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

Requires Python 3.13 (`nooa` does not yet support 3.14).

```bash
# using pip
pip install text2ics

# or run directly with uv
uvx text2ics
```

You will also need an API key from one of the supported providers.

## Providers

One key is all you need — pick the provider it belongs to. Extraction is an easy
task, so the cheapest model in each row is usually enough; the default is
**GPT-5.6 Luna**.

| Provider | Cheapest model | Environment variable | Get a key |
| --- | --- | --- | --- |
| OpenAI | `gpt-5.6-luna` | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/settings/organization/api-keys) |
| Anthropic | `claude-haiku-4-5` | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| DeepSeek | `deepseek/deepseek-v4-flash` | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| Kimi | `moonshot/kimi-k2.5` | `MOONSHOT_API_KEY` | [platform.moonshot.ai](https://platform.moonshot.ai/console/api-keys) |
| GLM | `zai/glm-4.5-flash` (free) | `ZAI_API_KEY` | [z.ai](https://z.ai/manage-apikey/apikey-list) |
| Grok | `xai/grok-4-1-fast-non-reasoning` | `XAI_API_KEY` | [console.x.ai](https://console.x.ai/) |

The full list lives in `text2ics/models.py` and is shared by the CLI and the web
app, so the two cannot drift apart. `tests/test_models.py` checks every id against
litellm's registry — a model id that does not exist fails the test suite rather
than failing at call time in front of a user.

## Usage

### Command-Line Interface (CLI)

Convert a text file straight to ICS. Set the key for your provider first:

```bash
export OPENAI_API_KEY="your-api-key"          # or any variable from the table above
text2ics path/to/your/textfile.txt > events.ics
```

Pick a different model with `--model`, which accepts any litellm model id. The
key is looked up from *that model's* provider, so several can be exported at once
without them being confused for one another:

```bash
export OPENAI_API_KEY="..." ANTHROPIC_API_KEY="..."
text2ics notes.txt                                > openai.ics   # uses OPENAI_API_KEY
text2ics notes.txt --model claude-haiku-4-5       > claude.ics   # uses ANTHROPIC_API_KEY
text2ics notes.txt --language da                  > danish.ics
```

`--api-key` overrides the lookup, and `TEXT2ICS_API_KEY` works as a
provider-agnostic fallback.

For more options, run `text2ics --help`.

### Streamlit Web App

The web app provides an interactive way to convert text.

```bash
streamlit run app/app.py
```

Paste your API key in the sidebar, choose the matching provider under **Advanced
Settings**, then paste your text. The generated calendar is previewed, and can be
downloaded as `.ics` or scanned as a QR code.

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

`poe test` is offline, free, and needs no API key.

### Evaluating the prompt

Two harnesses score extraction against the fixtures in `tests/data`. Both are
scripts rather than tests, because they call real models.

```bash
# Paid providers — costs API credits
uv run python tests/eval_models.py                  # default small-model set
uv run python tests/eval_models.py gpt-5.6-luna     # specific models
EVAL_REPEAT=5 uv run python tests/eval_models.py    # repeat to measure flakiness

# Free models via the opencode CLI — no API cost, requires `opencode auth login`
uv run python tests/eval_opencode.py
```

Both print `found/wanted` alongside the per-run event count, so a failure tells
you *which* way it failed: missing events and invented extras are different bugs.
A run only passes if it finds everything and invents nothing.

**Read this before editing the prompt in `text2ics/agent.py`.** Its brevity is
measured, not accidental. Adding a plausible-sounding line — "read the whole
text, events are often mentioned in prose" — made the weakest model *worse*
(4/8 vs 7/8). A line that stopped one model over-splitting a timetable made
another collapse events across dates and lose one entirely. Weak models also fail
intermittently, so a single green run tells you nothing: re-run at
`EVAL_REPEAT>=5` before and after any change.
