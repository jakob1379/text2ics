"""The preview silently dropped events that were present in the ICS.

The widget was configured with ``listMonth`` and an emptied ``headerToolbar``,
so it rendered only the month it opened on and offered no way to navigate. A
demo whose events spanned August and September showed 3 of 8, which read as an
extraction failure but was purely a display one.
"""

from datetime import datetime
from typing import Any

from ui import CALENDAR_OPTIONS, calendar_options_for
from utils import ical_to_streamlit_calendar

from text2ics.agent import Event
from text2ics.converter import build_calendar

SPANNING_MONTHS = [
    Event(summary="Team meeting", start=datetime(2026, 8, 10, 14, 0)),
    Event(summary="Conference call", start=datetime(2026, 8, 12, 15, 0)),
    Event(summary="Team Meeting", start=datetime(2026, 9, 24, 14, 0)),
    Event(summary="Dentist", start=datetime(2026, 9, 25, 10, 0)),
    Event(summary="Gym Session", start=datetime(2026, 9, 28, 18, 0)),
]


def _widget_events() -> list[dict[str, Any]]:
    return ical_to_streamlit_calendar(build_calendar(SPANNING_MONTHS))


def test_every_extracted_event_reaches_the_widget():
    assert len(_widget_events()) == len(SPANNING_MONTHS)


def test_preview_opens_on_the_first_event_not_on_today():
    options = calendar_options_for(_widget_events())
    assert options["initialDate"] == "2026-08-10"


def test_view_is_not_limited_to_a_single_month():
    """listMonth is what hid the September events; a year view shows them all."""
    assert CALENDAR_OPTIONS["initialView"] != "listMonth"
    assert CALENDAR_OPTIONS["initialView"] == "listYear"


def test_navigation_controls_are_present():
    """With an emptied toolbar there was no way to reach another month at all."""
    toolbar = CALENDAR_OPTIONS["headerToolbar"]
    assert isinstance(toolbar, dict)
    assert "prev" in toolbar["left"] and "next" in toolbar["left"]


def test_options_are_not_mutated_between_renders():
    before = dict(CALENDAR_OPTIONS)
    calendar_options_for(_widget_events())
    assert CALENDAR_OPTIONS == before, "calendar_options_for must not mutate the shared dict"


def test_empty_event_list_does_not_set_a_date():
    assert "initialDate" not in calendar_options_for([])
