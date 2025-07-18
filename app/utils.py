from datetime import date, datetime, timedelta
from typing import Optional

import icalendar as ical
import streamlit as st


def ical_to_streamlit_calendar(ical_obj: ical.Calendar) -> list[dict]:
    """
    Converts an icalendar.cal.Calendar object into a list of dictionaries
    compatible with streamlit-calendar.

    Args:
        ical_obj (Calendar): An icalendar.cal.Calendar object.

    Returns:
        list[dict]: A list of dictionaries, each representing an event
                    in the streamlit-calendar format.
    """
    streamlit_events = []

    for component in ical_obj.walk():
        if component.name == "VEVENT":
            event = {}
            # Title
            if "SUMMARY" in component:
                event["title"] = str(component.get("SUMMARY"))

            # Start and End Times
            start_dt = component.get("DTSTART")
            end_dt = component.get("DTEND")

            if start_dt:
                # Handle different types of datetime objects from icalendar
                if isinstance(start_dt.dt, datetime):
                    event["start"] = start_dt.dt.isoformat()
                    # FullCalendar's end is exclusive. If the icalendar event is all-day
                    # and ends on a specific day, FullCalendar expects the end
                    # to be the *next* day at midnight.
                    if (
                        end_dt
                        and isinstance(end_dt.dt, date)
                        and not isinstance(end_dt.dt, datetime)
                    ):
                        event["end"] = (end_dt.dt + timedelta(days=1)).isoformat()
                    elif end_dt:
                        event["end"] = end_dt.dt.isoformat()
                elif isinstance(start_dt.dt, date):
                    event["start"] = start_dt.dt.isoformat()
                    event["allDay"] = True
                    if end_dt and isinstance(end_dt.dt, date):
                        # For all-day events, FullCalendar end is exclusive of the end day.
                        # So, if an all-day event ends on 2023-08-01, FullCalendar needs 2023-08-02.
                        event["end"] = (end_dt.dt + timedelta(days=1)).isoformat()
                    else:
                        # If no end date for all-day, FullCalendar expects start date + 1 day
                        event["end"] = (start_dt.dt + timedelta(days=1)).isoformat()

            # Optional properties
            if "UID" in component:
                event["id"] = str(component.get("UID"))
            if "LOCATION" in component:
                event["extendedProps"] = {"location": str(component.get("LOCATION"))}
            if "DESCRIPTION" in component:
                if "extendedProps" not in event:
                    event["extendedProps"] = {}
                event["extendedProps"]["description"] = str(component.get("DESCRIPTION"))
            if "URL" in component:
                event["url"] = str(component.get("URL"))

            streamlit_events.append(event)
    return streamlit_events


@st.cache_data(ttl=3600)
def get_file_content(file_bytes: bytes) -> str:
    """Cache file content reading"""
    return file_bytes.decode("utf-8")


@st.cache_data(ttl=3600)
def validate_api_key(api_key: str) -> bool:
    """Basic API key validation"""
    return len(api_key.strip()) > 10


@st.cache_data(ttl=3600)
def process_content_cached(
    content: str,
    api_key: str,
    model: str,
    language: Optional[str],
    _process_content_func,
):
    """Cache expensive API calls"""
    result = _process_content_func(content=content, api_key=api_key, model=model, language=language)
    return result
