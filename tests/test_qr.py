"""The QR code was built into a BytesIO inside a `with` block and the stream was
handed to st.image directly. Two things went wrong at once: after `save()` the
stream is at EOF so a reader gets zero bytes, and the `with` block closed the
buffer before Streamlit served the file. The browser then asked for a media file
that held nothing, and Streamlit raised

    MediaFileStorageError: Bad filename '...jpg'. (No media file with id '...')

Returning bytes sidesteps both.
"""

import io

import pytest
from utils import qr_png

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_returns_a_non_empty_png():
    data = qr_png(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")
    assert data.startswith(PNG_MAGIC)
    assert len(data) > 100, "an exhausted stream used to yield zero bytes here"


def test_result_is_plain_bytes_not_a_stream():
    """A stream can be closed or exhausted before Streamlit reads it; bytes cannot."""
    assert isinstance(qr_png(b"x"), bytes)


def test_survives_a_realistic_calendar_payload():
    from datetime import datetime

    from text2ics.agent import Event
    from text2ics.converter import build_calendar

    ical = build_calendar([Event(summary="Ferry", start=datetime(2026, 9, 24, 11, 5))]).to_ical()
    assert qr_png(ical).startswith(PNG_MAGIC)


def test_reading_the_buffer_after_save_is_why_bytes_are_returned():
    """Documents the underlying trap so the fix is not 'simplified' back."""
    import qrcode

    buffer = io.BytesIO()
    qrcode.make(b"x").save(buffer, format="PNG")  # pyright: ignore[reportCallIssue]
    assert buffer.read() == b"", "stream is at EOF after save()"
    assert buffer.getvalue() != b""


def test_closed_buffer_cannot_be_read():
    """The `with` block closed the stream before Streamlit served it."""
    buffer = io.BytesIO()
    with buffer:
        pass
    with pytest.raises(ValueError):
        buffer.getvalue()
