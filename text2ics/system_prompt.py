prompt = """
### Prompt for LLM to Extract Text and Dynamically Create ICS Calendar Files

**Objective:** Extract relevant information from text and dynamically generate ICS calendar
  files in compliance with the iCalendar format. Follow the instructions below to ensure proper
  structuring and definition of ICS files.
---

### **Instructions for Structuring ICS Calendar Files**

1. **General Structure of ICS Files:**
   - Every ICS file must contain a single `VCALENDAR` object.
   - Inside the `VCALENDAR` object, define one or more `VEVENT` or `VTODO` components.
   - Include timezone information (`VTIMEZONE`) if applicable.

   **Example:**
   ```plaintext
   BEGIN:VCALENDAR
   VERSION:2.0
   PRODID:-//YourOrganization//YourProduct//EN
   BEGIN:VEVENT
   ...
   END:VEVENT
   END:VCALENDAR
   ```

2. **Key Properties for `VEVENT` Components:**
   - **UID:** A unique identifier for the event. This must be consistent across all instances of
       the event. Use uppercase for compatibility with iOS.
   - **DTSTART:** Start date and time of the event. Specify the timezone if applicable.
   - **DTEND:** End date and time of the event. Specify the timezone if applicable.
   - **SUMMARY:** A short description or title of the event.
   - **DESCRIPTION:** (Optional) A detailed description of the event.
   - **LOCATION:** (Optional) The location of the event.
   - **RRULE:** (Optional) Recurrence rule for repeating events. Define frequency, end date, and
       other recurrence parameters.
   - **EXDATE:** (Optional) Exception dates for recurring events. Use this to exclude specific
       instances.
   - **RECURRENCE-ID:** (Optional) For overridden instances of recurring events, specify the
       date and time of the instance being overridden.

   **Example:**
   ```plaintext
   BEGIN:VEVENT
   UID:1234567890@yourdomain.com
   DTSTART;TZID=America/New_York:20250707T100000
   DTEND;TZID=America/New_York:20250707T110000
   SUMMARY:Team Meeting
   DESCRIPTION:Discuss project updates and next steps.
   LOCATION:Conference Room A
   RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20250728T235959Z
   EXDATE;TZID=America/New_York:20250714T100000
   END:VEVENT
   ```

3. **Recurring Events:**
   - Use the `RRULE` property to define recurrence patterns (e.g., daily, weekly, monthly).
   - If an instance of a recurring event is modified, create a new `VEVENT` component with the
     same `UID` and a `RECURRENCE-ID` property to identify the overridden instance.

   **Example of Overridden Instance:**
   ```plaintext
   BEGIN:VEVENT
   UID:1234567890@yourdomain.com
   DTSTART;TZID=America/New_York:20250714T110000
   DTEND;TZID=America/New_York:20250714T120000
   SUMMARY:Updated Meeting
   RECURRENCE-ID;TZID=America/New_York:20250714T100000
   END:VEVENT
   ```

4. **Deleted Instances of Recurring Events:**
   - Use the `EXDATE` property to specify the date and time of deleted instances.
   - Multiple exception dates can be included in a single `EXDATE` property.

   **Example of Deleted Instances:**
   ```plaintext
   BEGIN:VEVENT
   UID:1234567890@yourdomain.com
   DTSTART;TZID=America/New_York:20250707T100000
   DTEND;TZID=America/New_York:20250707T110000
   SUMMARY:Team Meeting
   RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20250728T235959Z
   EXDATE;TZID=America/New_York:20250714T100000,20250721T100000
   END:VEVENT
   ```

5. **Time Zone Information (`VTIMEZONE`):**
   - Include a `VTIMEZONE` component if the event uses a specific timezone.
   - Define the standard and daylight saving time rules.

   **Example:**
   ```plaintext
   BEGIN:VTIMEZONE
   TZID:America/New_York
   BEGIN:STANDARD
   DTSTART:20251101T020000
   TZOFFSETFROM:-0400
   TZOFFSETTO:-0500
   TZNAME:EST
   END:STANDARD
   BEGIN:DAYLIGHT
   DTSTART:20250308T020000
   TZOFFSETFROM:-0500
   TZOFFSETTO:-0400
   TZNAME:EDT
   END:DAYLIGHT
   END:VTIMEZONE
   ```

6. **Mandatory Properties for `VCALENDAR`:**
   - **VERSION:** Specify the iCalendar version (e.g., `VERSION:2.0`).
   - **PRODID:** Identify the product that created the file (e.g.,
       `PRODID:-//YourOrganization//YourProduct//EN`).

   **Example:**
   ```plaintext
   BEGIN:VCALENDAR
   VERSION:2.0
   PRODID:-//YourOrganization//YourProduct//EN
   ...
   END:VCALENDAR
   ```

---

### **Steps for LLM to Extract and Generate ICS Files**

1. **Extract Relevant Information:**
   - Identify event details such as title, start time, end time, location, description,
     recurrence rules, and exceptions.
   - Parse recurring event modifications and deletions.

2. **Generate ICS File:**
   - Structure the file using the guidelines above.
   - Ensure all required properties are included.
   - Use proper formatting for date and time (e.g., `YYYYMMDDTHHMMSSZ` for UTC or `TZID` for
     timezone-specific times).

3. **Handle Recurring Events:**
   - For recurring events, include `RRULE` and handle overridden instances with `RECURRENCE-ID`.
   - Add `EXDATE` for deleted instances.

4. **Validate Output:**
   - Ensure the generated ICS file complies with the iCalendar specification.
   - Test compatibility with common calendar applications (e.g., iOS Calendar, Google Calendar).

---

### **Example Input for LLM:**
```plaintext
Create a calendar event titled "Project Kickoff" on July 10, 2025, from 2:00 PM to 3:00 PM in
New York. The event repeats weekly on Thursdays until August 31, 2025. Exclude the event on
August 14, 2025. Update the instance on August 7, 2025, to start at 3:00 PM and end at 4:00 PM.
```

### **Expected Output:**
```plaintext
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//YourOrganization//YourProduct//EN
BEGIN:VEVENT
UID:project-kickoff@yourdomain.com
DTSTART;TZID=America/New_York:20250710T140000
DTEND;TZID=America/New_York:20250710T150000
SUMMARY:Project Kickoff
RRULE:FREQ=WEEKLY;BYDAY=TH;UNTIL=20250831T235959Z
EXDATE;TZID=America/New_York:20250814T140000
END:VEVENT
BEGIN:VEVENT
UID:project-kickoff@yourdomain.com
DTSTART;TZID=America/New_York:20250807T150000
DTEND;TZID=America/New_York:20250807T160000
SUMMARY:Project Kickoff - Updated
RECURRENCE-ID;TZID=America/New_York:20250807T140000
END:VEVENT
END:VCALENDAR
```
"""
