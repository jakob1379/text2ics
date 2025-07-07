# text2ics

A Python tool to convert unstructured text into an ICS calendar file using an LLM.
It provides both a command-line interface (CLI) and a Streamlit web application.

## 💾 Installation
Ensure you have Python installed, then clone the repository and install the dependencies.

```bash
# using pip
pip install text2ics

# or run directly with uv
uvx text2ics
```

You will also need an API key for a compatible LLM service (like OpenAI).

## 🚀 Usage

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

## 🧱 Development
This project uses `uv` for dependency management and `poethepoet` for running tasks.

Install all dependencies, including for development:
```bash
uv sync --all-extras
```

Run common development tasks:
```bash
uv run poe fmt   # Format code
uv run poe lint  # Lint and fix
uv run poe check # Type-check
uv run poe test  # Run tests
uv run poe all   # Run all checks
```

## 🦺 CI/CD
The repository is set up with GitHub Actions to automate checks on pull requests and to handle releases.
- **[pr.yml](.github/workflows/pr.yml):** Validates pull requests.
- **[release.yml](.github/workflows/release.yml):** Manages releases to PyPI.
