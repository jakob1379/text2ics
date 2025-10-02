# Largely adopted from:
# https://en.wikipedia.org/wiki/ICalendar
# https://www.webdavsystem.com/server/creating_caldav_carddav/calendar_ics_file_structure/
prompt = """Prompt: Extract events from INPUT and output a raw iCalendar (ICS) file

RULES
- Use only text inside <INPUT>...</INPUT>.
- Output raw ICS only: a single VCALENDAR with one VEVENT per detected event.
- Do not add explanations or JSON. Examples are illustrative; do not copy their
  counts or content.

DETECTION
- Danish locale (da-DK). Dates like 24/9 mean DD/MM; also accept D.M or DD.MM.
- An event line begins with a date, then a separator (" - ", "-", "–", "—"),
  then a title. Example: "24/9 - Session 1: Intro".
- Times like "kl. 19–21" or "19:00-21:00" indicate start–end. "kl." means time.

NORMALIZATION
- Timezone: Europe/Copenhagen for local date-times.
- Missing year: use the next occurrence relative to now in Europe/Copenhagen;
  if a listed month/day has already passed this year, roll to next year.
- Missing time: make an all-day event using DATE values:
  - DTSTART;VALUE=DATE: YYYYMMDD
  - DTEND;VALUE=DATE: YYYYMMDD (exclusive; set to next day)
- Start time only: default DURATION:PT1H.

ICS REQUIREMENTS (per VEVENT)
- UID: unique and stable (e.g., slug+date@yourdomain).
- DTSTAMP: current UTC timestamp, e.g., 20250919T080000Z.
- DTSTART: DATE (all-day) or DATE-TIME (with TZID=Europe/Copenhagen).
- DTEND (or DURATION): match DATE vs DATE-TIME choice and TZ usage.
- SUMMARY: from the line text after the date separator.
- Optional: LOCATION, DESCRIPTION, RRULE, EXDATE (match value type/TZ to DTSTART).

OUTPUT FORMAT (raw ICS only)
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//YourTool//ICS//EN
CALSCALE:GREGORIAN
X-WR-TIMEZONE:Europe/Copenhagen
... one VEVENT per detected event ...
END:VCALENDAR
"""
