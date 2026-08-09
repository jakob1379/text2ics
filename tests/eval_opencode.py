"""Score the extraction prompt against opencode's free models. No API cost.

These are genuinely small, weak models, which is exactly what the prompt has to
survive -- see tests/eval_models.py for the paid providers.

    uv run python tests/eval_opencode.py                    # all free models
    uv run python tests/eval_opencode.py ling-3.0-tiny-free
    EVAL_REPEAT=3 uv run python tests/eval_opencode.py      # measure flakiness

The prompt is read from EventExtractor.extract.__doc__ rather than copied, so
this cannot drift from what the app actually sends. nooa/litellm do not route
opencode models, so the call goes through the `opencode run` CLI and the JSON is
validated against the same Event schema.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Any

from eval_models import CASES, Expected, matches

from text2ics.agent import Event, EventExtractor

FREE_MODELS = [
    "deepseek-v4-flash-free",
    "laguna-s-2.1-free",
    "ling-3.0-tiny-free",
    "longcat-2.0-free",
    "mimo-v2.5-free",
    "nemotron-3-ultra-free",
    "north-mini-code-free",
]
DATA = Path(__file__).parent / "data"
FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


# A compact shape rather than Event.model_json_schema(): the real schema is ~700
# characters of JSON, and these models time out trying to read it. nooa sends the
# real one to providers that support structured output natively.
SHAPE = (
    '{"summary": "text", "start": "YYYY-MM-DDTHH:MM:SS", '
    '"end": "YYYY-MM-DDTHH:MM:SS or null", "all_day": true/false, '
    '"location": "text or null", "description": "text or null"}'
)


def build_prompt(text: str) -> str:
    """The agent's own docstring, so this cannot drift from what the app sends."""
    doc = EventExtractor.extract.__doc__ or ""
    instructions = doc.format(
        self=type("_", (), {"today": date.today(), "language": "the input's language"})()
    )
    return (
        f"{instructions}\n"
        "Reply with ONLY a JSON array, no prose, no code fences, no tool calls.\n"
        f"Each element: {SHAPE}\n\n"
        f"TEXT:\n{text}"
    )


def parse_events(raw: str) -> list[Event]:
    """Pull the JSON array out of whatever the model wrapped it in."""
    candidate = raw.strip()
    if fenced := FENCE.search(candidate):
        candidate = fenced.group(1).strip()
    start, end = candidate.find("["), candidate.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON array in output: {raw[:120]!r}")
    return [Event.model_validate(item) for item in json.loads(candidate[start : end + 1])]


def run_case(model: str, filename: str, expected: list[Expected]) -> dict[str, Any]:
    text = (DATA / filename).read_text(encoding="utf-8")
    started = time.monotonic()
    # A scratch dir, never the repo: opencode is a coding agent with file access.
    with tempfile.TemporaryDirectory(prefix="oc-eval-") as scratch:
        try:
            proc = subprocess.run(
                [
                    "opencode",
                    "run",
                    "--dir",
                    scratch,
                    "-m",
                    f"opencode/{model}",
                    build_prompt(text),
                ],
                capture_output=True,
                text=True,
                timeout=150,
                cwd=scratch,
            )
            events = parse_events(proc.stdout)
        except Exception as exc:
            return {
                "error": f"{type(exc).__name__}: {exc}"[:90],
                "seconds": time.monotonic() - started,
            }
    found = sum(matches(e, events) for e in expected)
    return {
        "found": found,
        "wanted": len(expected),
        "extracted": len(events),
        "seconds": time.monotonic() - started,
    }


def main(models: list[str]) -> int:
    raw_repeat = os.environ.get("EVAL_REPEAT", "1")
    repeat = int(raw_repeat) if raw_repeat.lstrip("-").isdecimal() else 0
    if repeat < 1:
        print(f"EVAL_REPEAT must be a positive integer, got {raw_repeat!r}")
        return 2

    print(f"{'model':<24} {'case':<10} {'runs ok':>9} {'found':>7} {'extracted':>10} {'sec':>6}")
    print("-" * 64)
    failures = 0
    for model in models:
        for name, filename, expected in CASES:
            runs = [run_case(model, filename, expected) for _ in range(repeat)]
            errors = [r for r in runs if "error" in r]
            done = [r for r in runs if "error" not in r]
            ok = sum(r["found"] == r["wanted"] == r["extracted"] for r in done)
            failures += repeat - ok
            extracted = "/".join(str(r["extracted"]) for r in done) or "-"
            found = "/".join(str(r["found"]) for r in done) or "-"
            wanted = done[0]["wanted"] if done else len(expected)
            seconds = sum(r["seconds"] for r in runs) / repeat
            mark = " " if ok == repeat else "  <-- MISS"
            print(
                f"{model:<24} {name:<10} {ok}/{repeat:>7} {found:>5}/{wanted} "
                f"{extracted:>10} {seconds:>6.1f}{mark}"
            )
            if errors:
                print(f"{'':<24} {'':<10} {len(errors)} errored: {errors[0]['error']}")
    print("-" * 64)
    print(f"{failures} failing run(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or FREE_MODELS))
