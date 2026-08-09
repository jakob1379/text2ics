import base64
import hashlib
import os
import time
from typing import Any

import streamlit as st
from streamlit_calendar import calendar
from style import bmac_html, css
from utils import (
    get_file_content,
    ical_to_streamlit_calendar,
    process_content_cached,
    qr_png,
    validate_api_key,
)

from text2ics.models import DEFAULT_PROVIDER, KEY_URLS, PROVIDERS

CALENDAR_OPTIONS: dict[str, Any] = {
    "editable": "true",
    "navLinks": "true",
    "selectable": "true",
    # listMonth only renders the month it is currently on, and the toolbar was
    # emptied, so there were no prev/next buttons: events in any other month were
    # in the ICS but invisible in the preview. listYear plus navigation shows the
    # whole set.
    "initialView": "listYear",
    "height": "auto",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "listYear,listMonth",
    },
}


def calendar_options_for(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Open the preview on the first event, not on today.

    Events are frequently months ahead, and a view anchored to today would start
    on an empty page even with navigation available.
    """
    options = dict(CALENDAR_OPTIONS)
    starts = sorted(e["start"] for e in events if e.get("start"))
    if starts:
        options["initialDate"] = starts[0][:10]  # YYYY-MM-DD
    return options


def get_image_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Custom CSS for professional styling
def load_custom_css():
    st.markdown(css, unsafe_allow_html=True)


def load_bmac_button():
    st.markdown(bmac_html, unsafe_allow_html=True)


def render_header():
    """Render welcoming banner header"""
    st.markdown(
        """
        <div class="welcome-header">
            <h1>📅 Text to ICS Converter</h1>
            <p>Transform your event descriptions into calendar files</p>
            <p style="margin-top: 1rem; font-size: 1rem; opacity: 0.9;">
                Add your event below to get started
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_step_status(
    step_num: int,
    config_completed: bool,
    input_completed: bool,
    conversion_started: bool,
) -> str:
    """Get the status of a step"""
    if step_num == 1:
        return "step-completed" if config_completed else "step-active"
    elif step_num == 2:
        if not config_completed:
            return "step-pending"
        return "step-completed" if input_completed else "step-active"
    else:  # step 3
        if not config_completed or not input_completed:
            return "step-pending"
        # Step 3 is active when ready to generate
        return "step-completed" if conversion_started else "step-active"


def render_step_indicator(
    step_num: int,
    title: str,
    config_completed: bool,
    input_completed: bool,
    conversion_started: bool,
):
    """Render step indicator"""
    status = get_step_status(step_num, config_completed, input_completed, conversion_started)

    if status == "step-completed":
        icon = "✅"
    elif status == "step-active":
        icon = "🔄"
    else:
        icon = "⏳"

    st.markdown(
        f'<div class="step-indicator {status}">{icon} Step {step_num}: {title}</div>',
        unsafe_allow_html=True,
    )


def render_config_section():
    """Render user-friendly settings section as sidebar"""
    with st.sidebar:
        st.subheader("⚙️ Settings")

        # API Key section with friendly guidance
        st.markdown("### 🔑 API Key")
        st.markdown("To use this tool, you'll need an AI service API key.")

        with st.expander("❓ What's an API key? How do I get one?", expanded=False):
            # Built from KEY_URLS so this list cannot drift from the picker.
            services = "\n".join(
                f"               - [{name}]({url})" for name, url in KEY_URLS.items()
            )
            st.markdown(f"""
            **An API key is like a password that lets this tool use AI services.**

            **Getting one is free and takes 2 minutes:**
            1. **Choose a service** (any will work):
{services}
            2. **Create an account** (if you don't have one)
            3. **Generate an API key** in the settings
            4. **Copy and paste it here**, then pick the matching provider below

            **Don't worry about costs** - extracting events is cheap, and the
            default model costs a fraction of a cent per calendar.
            Most services offer free credits to start.
            """)

        api_key = st.text_input(
            "Your API Key",
            type="password",
            help="Paste your API key here. It's required to generate calendars.",
            value=os.environ.get("TXT2ICS_API_KEY", ""),
            key="api_key_input",
        )

        if api_key:
            if validate_api_key(api_key):
                st.success("✅ API Key looks good!")
            else:
                st.warning("⚠️ Key seems too short. Make sure it's complete.")
        else:
            st.info("👆 Paste your API key above to get started")

        st.markdown("---")

        # Advanced settings (collapsed by default)
        with st.expander("⚙️ Advanced Settings", expanded=False):
            # Model selection - simplified for non-technical users
            st.markdown("**AI Model** (optional)")
            providers = list(PROVIDERS)
            provider = st.selectbox(
                "Provider:",
                options=providers,
                index=providers.index(DEFAULT_PROVIDER),
                help="Pick the service your API key is for.",
                key="provider_select",
            )
            st.caption(f"[Get a {provider} key]({KEY_URLS[provider]})")

            # Only this provider's models, so the choice always matches the key.
            choices = list(PROVIDERS[provider])
            model = st.selectbox(
                "Model:",
                options=choices,
                index=0,  # cheapest first
                help="Extracting events is easy, so the cheapest model usually suffices.",
                key=f"model_select_{provider}",
            )
            model = PROVIDERS[provider][model]

            # Language
            language = st.text_input(
                "Calendar Language (optional)",
                placeholder="e.g., 'en' for English, 'es' for Spanish",
                help="Leave blank to auto-detect from your text",
                key="language_input",
            )

        # Update completion status (for backward compatibility)
        if api_key and validate_api_key(api_key):
            st.session_state.app_state.config_completed = True
        else:
            st.session_state.app_state.config_completed = False

    return api_key, model, language


def render_input_section():
    """Render simplified input section with example text"""

    # Verified end to end: gpt-5-mini and gpt-5.4-mini both extract all 8 events
    # from this text, framing lines included. The events that went missing from
    # the preview were a calendar-view problem, not an extraction one.
    example_text = """Example events (edit or replace with your own):

24/9 - Team Meeting: Weekly sync at 14:00-15:00 in Conference Room A
25/9 - Dentist Appointment: 10:00-11:00 at Dental Clinic
26/9 - Project Deadline: Submit final report by EOD
27/9 - Dinner with Friends: 19:00 at Italian Restaurant
28/9 - Gym Session: 18:00-19:30

Or enter your own events in any format:
- Team meeting tomorrow at 2pm
- Conference call on Wednesday 3-4pm
- Birthday party Saturday 7pm"""

    # File upload option
    uploaded_file = st.file_uploader(
        "📁 Upload a text file (optional)",
        type=["txt"],
        help="Upload a .txt file containing event details",
        key="file_uploader",
    )

    # Determine initial text area content
    text_area_content = ""

    if uploaded_file is not None:
        file_hash = hashlib.md5(uploaded_file.read()).hexdigest()
        uploaded_file.seek(0)  # Reset file pointer

        if st.session_state.file_hash != file_hash:
            st.session_state.file_hash = file_hash
            text_area_content = get_file_content(uploaded_file.read())
            st.info("📁 File loaded! You can edit the text below.")
        else:
            text_area_content = st.session_state.get("manual_text", example_text)
    else:
        text_area_content = st.session_state.get("manual_text", example_text)

    # Main text area
    manual_text = st.text_area(
        "📝 Your Events",
        value=text_area_content,
        height=300,
        help=(
            "Type or paste your event details here. "
            "The AI will automatically find dates, times, and locations."
        ),
        key="manual_text",
    )

    # Tips
    with st.expander("💡 Tips for best results", expanded=False):
        st.markdown("""
        - **Be specific**: Include dates, times, and locations when possible
        - **Natural language**: "Meeting on Tuesday at 2pm" works well
        - **Multiple events**: List events one per line or in paragraphs
        - **Time formats**: 14:00, 2pm, 2:00 PM all work
        - **Date formats**: 24/9, 24-09, September 24, tomorrow, next Tuesday
        """)

    # Update completion status (for backward compatibility)
    if manual_text and len(manual_text.strip()) > 10:
        st.session_state.app_state.input_completed = True
    else:
        st.session_state.app_state.input_completed = False

    return manual_text, uploaded_file


def render_conversion_section(
    text_content: str,
    api_key: str,
    model: str,
    language: str,
    process_content_func,
) -> None:
    """Render conversion section"""
    # Validation checks
    ready_to_convert = True
    issues: list[str] = []

    if not api_key:
        issues.append("🔑 Please enter your API key to continue")
        ready_to_convert = False
    elif not validate_api_key(api_key):
        issues.append("❌ API key seems incomplete. Please check and try again.")
        ready_to_convert = False

    if not text_content or len(text_content.strip()) < 10:
        issues.append("📝 Please enter some event details (at least 10 characters)")
        ready_to_convert = False

    if issues:
        for issue in issues:
            st.warning(issue)

    # conversion button
    if st.button(
        "🚀 Generate ICS Calendar",
        disabled=not ready_to_convert,
        use_container_width=True,
        key="convert_button",
        type="primary" if not st.session_state.app_state.conversion_started else "secondary",
    ):
        # Mark conversion as started - this will cause section 2 to collapse
        st.session_state.app_state.conversion_started = True

        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("🔄 Initializing conversion...")
            progress_bar.progress(25)
            time.sleep(0.5)

            status_text.text("🤖 Processing...")
            progress_bar.progress(50)

            # Track timing for cache feedback
            start_time = time.time()

            ics_calendar, debug_info = process_content_cached(
                text_content,
                api_key,
                model,
                language if language else None,
                process_content_func,
            )
            st.session_state["ics_content"] = ics_calendar
            st.session_state["debug_info"] = debug_info
            processing_time = time.time() - start_time

            # Update debug info
            st.session_state.app_state.last_processing_time = processing_time
            if processing_time < 1.0:
                st.session_state.app_state.last_cache_status = "⚡ Cache Hit"
            else:
                st.session_state.app_state.last_cache_status = "🔄 New Generation"

            progress_bar.progress(75)
            status_text.text("📅 Generating calendar...")
            time.sleep(0.5)

            progress_bar.progress(100)
            status_text.text("✅ Conversion complete!")

        except Exception as e:
            st.error(f"❌ Conversion failed: {str(e)}")
            st.info("💡 Try checking your API key or simplifying the input text")
            st.markdown("</div>", unsafe_allow_html=True)
            return

    if ics_content := st.session_state.get("ics_content"):
        # Display results with calendar preview
        st.subheader("📋 Generated Calendar")
        with st.expander("📅 Preview of generated calendar", expanded=True):
            json_events = ical_to_streamlit_calendar(ics_content)
            calendar(
                events=json_events,
                options=calendar_options_for(json_events),
                key="calendarview",
            )
            st.caption(f"{len(json_events)} event{'s' if len(json_events) != 1 else ''} extracted")
            st.subheader(
                "Download file or scan QR to get the event"
                f"{'s' if len(ics_content.events) > 1 else ''}"
            )

            st.download_button(
                label="💾 Download Calendar File",
                data=ics_content.to_ical(),
                help="Open the downloaded file to quickly add it to your calendar",
                file_name=f"calendar_{int(time.time())}.ics",
                mime="text/calendar",
                use_container_width=True,
                type="primary",
            )
            st.image(
                qr_png(ics_content.to_ical()),
                caption="Scan to add these events to your phone",
            )

        # Success message
        st.success("🎉 Calendar generated successfully!")

        # Debug panel
        if debug_info := st.session_state.get("debug_info"):
            with st.expander("🤖 Debug Output", expanded=False):
                st.subheader("Model Output")
                st.code(debug_info.get("raw_output", ""), language="text")
                st.subheader("Debug Info")
                st.json(debug_info)
    st.markdown("</div>", unsafe_allow_html=True)
