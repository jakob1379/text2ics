"""The CLI used to hand whichever key was exported first to whatever model was
asked for.

typer's ``envvar=[A, B]`` takes the first variable that is set, so with both
OPENAI_API_KEY and ANTHROPIC_API_KEY exported, ``--model claude-haiku-4-5`` was
given the OpenAI key and failed to authenticate. The key is now resolved from the
selected model's provider, which is also what makes the README example -- both
keys exported at once -- correct.
"""

from pathlib import Path
from typing import Any

import icalendar
import pytest
from typer.testing import CliRunner

from text2ics import cli

runner = CliRunner()


@pytest.fixture
def note(tmp_path: Path) -> Path:
    path = tmp_path / "note.txt"
    path.write_text("24/9 - Team Meeting 14:00-15:00", encoding="utf-8")
    return path


@pytest.fixture
def captured_key(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the key the CLI would send, without calling any model."""
    seen: list[str] = []

    def fake_process_content(**kwargs: Any) -> tuple[icalendar.Calendar, dict[str, Any]]:
        seen.append(kwargs["api_key"])
        from text2ics.converter import build_calendar

        return build_calendar([]), {}

    monkeypatch.setattr("text2ics.converter.process_content", fake_process_content)
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MOONSHOT_API_KEY", "TEXT2ICS_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    return seen


def test_openai_model_uses_the_openai_key(
    note: Path, captured_key: list[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    result = runner.invoke(cli.app, [str(note), "--model", "gpt-5.6-luna"])
    assert result.exit_code == 0, result.output
    assert captured_key == ["openai-key"]


def test_claude_model_uses_the_anthropic_key_even_when_openai_is_also_set(
    note: Path, captured_key: list[str], monkeypatch: pytest.MonkeyPatch
):
    """The exact regression: both exported, Claude requested."""
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    result = runner.invoke(cli.app, [str(note), "--model", "claude-haiku-4-5"])
    assert result.exit_code == 0, result.output
    assert captured_key == ["anthropic-key"], "Claude must not be handed the OpenAI key"


def test_explicit_api_key_overrides_the_environment(
    note: Path, captured_key: list[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    result = runner.invoke(cli.app, [str(note), "--api-key", "explicit-key"])
    assert result.exit_code == 0, result.output
    assert captured_key == ["explicit-key"]


def test_missing_key_names_the_variable_to_export(note: Path, captured_key: list[str]):
    result = runner.invoke(cli.app, [str(note), "--model", "claude-haiku-4-5"])
    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output
    assert captured_key == []
