"""Event extraction agent built on nooa (NVIDIA-labs OO Agents).

The LLM only extracts events into a typed schema. Building valid ICS is Python's
job (see :mod:`text2ics.converter`), which is why the prompt below can stay this
short and still work on small models.
"""

from datetime import date, datetime
from typing import Any

# nooa ships no py.typed marker; these are third-party stub gaps, not our types.
from nooa import Agent, PredictStrategy, strategy  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, Field, field_validator


class Event(BaseModel):
    """One calendar event extracted from free text."""

    summary: str = Field(description="Short event title")
    start: datetime = Field(description="Local wall-clock start, ISO 8601, no timezone")
    end: datetime | None = Field(default=None, description="Local wall-clock end, if stated")
    all_day: bool = Field(default=False, description="True when no clock time was given")
    location: str | None = None
    description: str | None = Field(
        default=None,
        description="Everything else: this event's programme of times, price, practical details",
    )

    @field_validator("start", "end")
    @classmethod
    def _keep_clock_face(cls, value: datetime | None) -> datetime | None:
        """Drop any timezone the model attached, keeping the clock face it printed.

        The prompt asks for local wall-clock with no timezone, but models tack one
        on anyway -- gpt-4.1-nano routinely returns a correct wall-clock time
        stamped ``+00:00``. Converting such a value would shift a 17:00 event to
        18:00 or 19:00; taking the clock face as written is what the prompt asked
        for, so the offset is discarded rather than applied.

        >>> Event(summary="x", start="2026-08-20T13:00Z").start
        datetime.datetime(2026, 8, 20, 13, 0)
        >>> Event(summary="x", start="2026-08-20T13:00-05:00").start
        datetime.datetime(2026, 8, 20, 13, 0)
        """
        return value.replace(tzinfo=None) if value is not None else value


class EventExtractor(Agent):
    """You extract calendar events from text."""

    def __init__(
        self, today: date | None = None, language: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.today = today or date.today()
        self.language = language or "the dominant language of the input text"

    @strategy(PredictStrategy())
    async def extract(self, text: str) -> list[Event]:
        """List every event in the text.

        Today is {self.today}. Numeric dates are day-first: 24/9 is 24 September.
        If a year is missing, pick the next occurrence that is not in the past.
        Give times exactly as written, as local wall-clock, with no timezone.
        Set all_day when no clock time is given.
        Write summary, location and description in {self.language}.
        Return an empty list if the text contains no events.
        """
        ...
