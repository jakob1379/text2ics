import asyncio
from datetime import date, datetime, timedelta
from hashlib import blake2s
from importlib.metadata import version
from typing import Any
from zoneinfo import ZoneInfo

import icalendar
from dotenv import load_dotenv
from nooa.unifiedllm.registry import (
    get_llm_client,  # pyright: ignore[reportUnknownVariableType,reportMissingTypeStubs]
)

from text2ics.agent import Event, EventExtractor

load_dotenv()

DEFAULT_TZ = "Europe/Copenhagen"
DEFAULT_DURATION = timedelta(hours=1)


def _uid(event: Event, taken: set[str]) -> str:
    """Stable UID so re-importing the same event updates rather than duplicates.

    Hashed over the fields that distinguish one event from another, so the UID does
    not depend on the order the model happened to list them in. Two events sharing
    only a title and start (the same talk in two rooms) get different UIDs and stay
    separate entries on import.

    ``description`` is deliberately excluded: it is free prose that gets reworded
    between runs, and including it would hand the same event a new UID every time.

    Events identical in all these fields are interchangeable, so the ordinal
    fallback below cannot produce a misleading result.
    """
    identity = "\x1f".join(
        [
            event.summary,
            event.start.isoformat(),
            event.end.isoformat() if event.end else "",
            event.location or "",
            str(event.all_day),
        ]
    )
    digest = blake2s(identity.encode(), digest_size=8).hexdigest()
    uid = f"{digest}@text2ics"
    collision = 1
    while uid in taken:
        collision += 1
        uid = f"{digest}-{collision}@text2ics"
    taken.add(uid)
    return uid


def _end_of(event: Event) -> datetime:
    """Resolve the end time, handling missing and past-midnight ends."""
    if event.end is None:
        return event.start + DEFAULT_DURATION
    if event.end <= event.start:
        # "17.00-01.00" means the end lands on the following day.
        return event.end + timedelta(days=1)
    return event.end


def build_calendar(events: list[Event], tz: str = DEFAULT_TZ) -> icalendar.Calendar:
    """Build a valid ICS calendar from extracted events.

    All the fiddly ICS parts -- escaping, line folding, CRLF, UID, DTSTAMP -- are
    handled here by the icalendar library, so the LLM never has to.

    >>> cal = build_calendar([Event(summary="Ferry", start=datetime(2025, 7, 18, 11, 5))])
    >>> b"SUMMARY:Ferry" in cal.to_ical()
    True
    """
    zone = ZoneInfo(tz)
    calendar = icalendar.Calendar()
    calendar.add("prodid", f"-//jgalabs//text2ics {version('text2ics')}//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-timezone", tz)

    now = datetime.now(ZoneInfo("UTC"))
    taken: set[str] = set()
    for event in events:
        vevent = icalendar.Event()
        vevent.add("uid", _uid(event, taken))
        vevent.add("dtstamp", now)
        vevent.add("summary", event.summary)
        if event.all_day:
            start: date = event.start.date()
            end: date = event.end.date() if event.end else start
            vevent.add("dtstart", start)
            vevent.add("dtend", end + timedelta(days=1))  # DTEND is exclusive
        else:
            vevent.add("dtstart", event.start.replace(tzinfo=zone))
            vevent.add("dtend", _end_of(event).replace(tzinfo=zone))
        if event.location:
            vevent.add("location", event.location)
        if event.description:
            vevent.add("description", event.description)
        calendar.add_component(vevent)
    return calendar


def extract_events(
    content: str, api_key: str, model: str, language: str | None = None
) -> list[Event]:
    """Run the nooa agent to pull events out of free text."""
    llm = get_llm_client(model, api_key=api_key, num_retries=3)
    agent = EventExtractor(language=language, llm=llm)
    return asyncio.run(agent.extract(content))


def process_content(
    content: str,
    api_key: str,
    model: str,
    language: str | None = None,
    tz: str = DEFAULT_TZ,
) -> tuple[icalendar.Calendar, dict[str, Any]]:
    """Convert free text into an ICS calendar plus debug info for the UI."""
    events = extract_events(content, api_key, model, language)
    calendar = build_calendar(events, tz)
    debug_info = {
        "raw_output": "\n".join(e.model_dump_json() for e in events),
        "model": model,
        "event_count": len(events),
        "success": True,
    }
    return calendar, debug_info
