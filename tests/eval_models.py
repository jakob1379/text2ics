"""Score the extraction prompt across models. Costs real API credits, so it is a
script rather than a pytest test.

    uv run python tests/eval_models.py                    # default small-model set
    uv run python tests/eval_models.py gpt-4o-mini o4-mini
    EVAL_REPEAT=5 uv run python tests/eval_models.py      # measure flakiness
"""

import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from text2ics.agent import Event
from text2ics.converter import extract_events

DATA = Path(__file__).parent / "data"
Expected = tuple[datetime, "datetime | None", bool]
DEFAULT_MODELS = ["gpt-4o-mini", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-5-nano", "gpt-5-mini"]


def next_occurrence(month: int, day: int, today: date | None = None) -> date:
    """The rule the prompt asks for: nearest future date with that month/day."""
    today = today or date.today()
    candidate = date(today.year, month, day)
    return candidate if candidate >= today else date(today.year + 1, month, day)


def _julefest_expected() -> list[Expected]:
    party = next_occurrence(12, 12)
    market = party + timedelta(days=1)  # the text says "dagen efter"
    start = datetime.combine(party, datetime.min.time())
    return [
        # Overnight party: 17.00 -> 01.00. The prompt asks for times as written, so the
        # end comes back on the start date; build_calendar rolls it to the next day.
        (start.replace(hour=17), start.replace(hour=1), False),
        # All-day market, no clock time given.
        (datetime.combine(market, datetime.min.time()), None, True),
    ]


CASES: list[tuple[str, str, list[Expected]]] = [
    (
        # The mail states departure times only, so extraction has no end to report:
        # the one-hour default is build_calendar's job (see tests/test_calendar.py).
        "ferry",
        "ferry_mail.txt",
        [
            (datetime(2025, 7, 18, 11, 5), None, False),
            (datetime(2025, 7, 20, 17, 30), None, False),
        ],
    ),
    ("julefest", "julefest.txt", _julefest_expected()),
]


def matches(expected: Expected, events: list[Event]) -> bool:
    """An expected event is found if some extracted event shares its start, end and kind.

    An expected end of ``None`` means the text stated no end, so an extracted end is
    wrong -- inventing one (the ferry's one-hour default) is build_calendar's job.
    """
    want_start, want_end, want_all_day = expected
    return any(
        e.start.replace(tzinfo=None) == want_start
        and e.all_day == want_all_day
        and (e.end.replace(tzinfo=None) if e.end else None) == want_end
        for e in events
    )


def run_case(model: str, api_key: str, filename: str, expected: list[Expected]) -> dict[str, Any]:
    text = (DATA / filename).read_text(encoding="utf-8")
    started = time.monotonic()
    try:
        events = extract_events(text, api_key, model)
    except Exception as exc:  # a model may be unavailable or refuse the schema
        return {"error": f"{type(exc).__name__}: {exc}"[:90], "seconds": time.monotonic() - started}
    found = sum(matches(e, events) for e in expected)
    return {
        "found": found,
        "wanted": len(expected),
        "extracted": len(events),
        "seconds": time.monotonic() - started,
    }


def main(models: list[str]) -> int:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set (put it in .env)")
        return 2

    raw_repeat = os.environ.get("EVAL_REPEAT", "1")
    repeat = int(raw_repeat) if raw_repeat.lstrip("-").isdecimal() else 0
    if repeat < 1:
        print(f"EVAL_REPEAT must be a positive integer, got {raw_repeat!r}")
        return 2

    # "extracted" lists the event count per run: more than wanted is a failed run too.
    print(f"{'model':<16} {'case':<10} {'runs ok':>9} {'found':>7} {'extracted':>10} {'sec':>6}")
    print("-" * 56)
    failures = 0
    for model in models:
        for name, filename, expected in CASES:
            runs = [run_case(model, api_key, filename, expected) for _ in range(repeat)]
            errors = [r for r in runs if "error" in r]
            done = [r for r in runs if "error" not in r]
            # A run only passes if it found everything and invented nothing extra;
            # a run that errored never got that far, so it counts as a failure too.
            ok = sum(r["found"] == r["wanted"] == r["extracted"] for r in done)
            failures += repeat - ok
            extracted = "/".join(str(r["extracted"]) for r in done) or "-"
            found = "/".join(str(r["found"]) for r in done) or "-"
            wanted = done[0]["wanted"] if done else len(expected)
            seconds = sum(r["seconds"] for r in runs) / repeat
            mark = " " if ok == repeat else "  <-- MISS"
            print(
                f"{model:<16} {name:<10} {ok}/{repeat:>7} {found:>5}/{wanted} "
                f"{extracted:>10} {seconds:>6.1f}{mark}"
            )
            if errors:
                print(f"{'':<16} {'':<10} {len(errors)} errored: {errors[0]['error']}")
    print("-" * 56)
    print(f"{failures} failing run(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or DEFAULT_MODELS))
