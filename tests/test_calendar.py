"""Checks for the deterministic half: everything Python does after extraction."""

from datetime import datetime

import icalendar
import pytest

from text2ics.agent import Event
from text2ics.converter import build_calendar


def _events(cal: icalendar.Calendar) -> list[icalendar.Component]:
    return cal.walk("VEVENT")


def test_timed_event_gets_timezone_and_default_hour():
    cal = build_calendar([Event(summary="Ferry", start=datetime(2025, 7, 18, 11, 5))])
    (vevent,) = _events(cal)
    assert vevent["DTSTART"].dt == datetime(2025, 7, 18, 11, 5, tzinfo=vevent["DTSTART"].dt.tzinfo)
    assert vevent["DTSTART"].dt.tzname() == "CEST"
    # No end given -> one hour.
    assert vevent["DTEND"].dt - vevent["DTSTART"].dt == (
        datetime(2025, 7, 18, 12, 5) - datetime(2025, 7, 18, 11, 5)
    )


def test_end_past_midnight_rolls_to_next_day():
    cal = build_calendar(
        [
            Event(
                summary="Julefest",
                start=datetime(2025, 12, 12, 17, 0),
                end=datetime(2025, 12, 12, 1, 0),  # "17.00-01.00"
            )
        ]
    )
    (vevent,) = _events(cal)
    assert vevent["DTEND"].dt.date() == datetime(2025, 12, 13).date()
    assert vevent["DTEND"].dt.hour == 1


def test_all_day_uses_date_values_with_exclusive_end():
    cal = build_calendar(
        [Event(summary="Julemarked", start=datetime(2025, 12, 13, 0, 0), all_day=True)]
    )
    (vevent,) = _events(cal)
    assert vevent["DTSTART"].dt == datetime(2025, 12, 13).date()
    assert vevent["DTEND"].dt == datetime(2025, 12, 14).date()  # exclusive


def test_uid_is_stable_across_runs():
    event = Event(summary="Ferry", start=datetime(2025, 7, 18, 11, 5))
    assert _events(build_calendar([event]))[0]["UID"] == _events(build_calendar([event]))[0]["UID"]


def test_events_sharing_title_and_start_get_distinct_uids():
    # Same talk in two rooms: identical summary and start, but two real entries.
    # A shared UID would collapse them into one on import.
    same = [
        Event(summary="Keynote", start=datetime(2025, 7, 18, 11, 5), location="Room A"),
        Event(summary="Keynote", start=datetime(2025, 7, 18, 11, 5), location="Room B"),
    ]
    uids = [str(v["UID"]) for v in _events(build_calendar(same))]
    assert len(set(uids)) == 2, uids


def test_uid_does_not_depend_on_extraction_order():
    """Models list events in whatever order they like; a UID must not follow that."""
    a = Event(summary="Keynote", start=datetime(2025, 7, 18, 11, 5), location="Room A")
    b = Event(summary="Keynote", start=datetime(2025, 7, 18, 11, 5), location="Room B")
    forward = {
        str(v["SUMMARY"]) + str(v["LOCATION"]): str(v["UID"])
        for v in _events(build_calendar([a, b]))
    }
    reverse = {
        str(v["SUMMARY"]) + str(v["LOCATION"]): str(v["UID"])
        for v in _events(build_calendar([b, a]))
    }
    assert forward == reverse, (forward, reverse)


def test_uid_survives_a_reworded_description():
    """description is prose that drifts between runs; it must not change the UID."""
    base = dict(summary="Ferry", start=datetime(2025, 7, 18, 11, 5))
    first = build_calendar([Event(**base, description="Bring the booking")])  # pyright: ignore[reportArgumentType]
    second = build_calendar([Event(**base, description="Remember your booking")])  # pyright: ignore[reportArgumentType]
    assert str(_events(first)[0]["UID"]) == str(_events(second)[0]["UID"])


@pytest.mark.parametrize("raw", ["2026-08-20T13:00", "2026-08-20T13:00Z", "2026-08-20T13:00-05:00"])
def test_model_supplied_timezone_does_not_shift_the_clock_face(raw: str):
    """The prompt asks for wall-clock; models attach an offset anyway.

    gpt-4.1-nano returns correct wall-clock times stamped +00:00, so the offset is
    dropped rather than applied -- converting would move a 13:00 event to 14:00.
    """
    cal = build_calendar([Event(summary="Møde", start=raw)])  # pyright: ignore[reportArgumentType]
    (vevent,) = _events(cal)
    assert vevent["DTSTART"].dt.hour == 13
    assert vevent["DTSTART"].dt.tzname() == "CEST"


def test_output_is_parseable_ics():
    cal = build_calendar(
        [
            Event(
                summary="Møde med æ, ø, å",
                start=datetime(2025, 7, 18, 11, 5),
                description="Line one\nline two, with; specials",
            )
        ]
    )
    reparsed = icalendar.Calendar.from_ical(cal.to_ical().decode())
    (vevent,) = reparsed.walk("VEVENT")
    assert str(vevent["SUMMARY"]) == "Møde med æ, ø, å"
    assert "line two, with; specials" in str(vevent["DESCRIPTION"])


def test_empty_input_still_produces_valid_calendar():
    cal = build_calendar([])
    assert _events(cal) == []
    assert icalendar.Calendar.from_ical(cal.to_ical().decode())
