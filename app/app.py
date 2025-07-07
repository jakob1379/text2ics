import streamlit as st
from typing import Optional
import os
import hashlib
import time
from dataclasses import dataclass
from style import css


# Custom CSS for professional styling
def load_custom_css():
    st.markdown(css, unsafe_allow_html=True)


@dataclass
class AppState:
    """Application state management"""

    api_key: str = ""
    model: str = "gpt-4.1-nano"
    language: str = ""
    config_completed: bool = False
    input_completed: bool = False
    conversion_started: bool = (
        False  # New state to track if generate button was clicked
    )
    last_cache_status: str = ""  # Track cache status for debug panel
    last_processing_time: float = 0.0  # Track processing time


def init_session_state():
    """Initialize session state variables"""
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()
    else:
        # Handle existing session state that might not have the new field
        if not hasattr(st.session_state.app_state, "conversion_started"):
            st.session_state.app_state.conversion_started = False
        if not hasattr(st.session_state.app_state, "last_cache_status"):
            st.session_state.app_state.last_cache_status = ""
        if not hasattr(st.session_state.app_state, "last_processing_time"):
            st.session_state.app_state.last_processing_time = 0.0

    if "file_hash" not in st.session_state:
        st.session_state.file_hash = None


@st.cache_data(ttl=3600)
def get_file_content(file_bytes: bytes) -> str:
    """Cache file content reading"""
    return file_bytes.decode("utf-8")


def validate_api_key(api_key: str) -> bool:
    """Basic API key validation"""
    return len(api_key.strip()) > 10


def render_header():
    """Render professional header"""
    st.markdown(
        """
    <div class="main-header">
        <h1>📅 Text to ICS Converter</h1>
        <p>Transform your event descriptions into calendar files with AI precision</p>
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
        return (
            "step-completed"
            if input_completed and conversion_started
            else "step-active"
        )
    else:  # step 3
        if not config_completed or not input_completed:
            return "step-pending"
        return "step-active"


def render_step_indicator(
    step_num: int,
    title: str,
    config_completed: bool,
    input_completed: bool,
    conversion_started: bool,
):
    """Render step indicator"""
    status = get_step_status(
        step_num, config_completed, input_completed, conversion_started
    )

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
    """Render configuration section"""
    config_completed = st.session_state.app_state.config_completed
    input_completed = st.session_state.app_state.input_completed
    conversion_started = getattr(
        st.session_state.app_state, "conversion_started", False
    )

    render_step_indicator(
        1,
        "Configuration",
        config_completed,
        input_completed,
        conversion_started,
    )

    # Expander is open if the configuration is not yet completed.
    with st.expander("🔧 Setup API Configuration", expanded=not config_completed):
        st.markdown('<div class="section-container">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            api_key = st.text_input(
                "LLM Service API Key",
                type="password",
                help="Enter your API key for the LLM service",
                value=os.environ.get("TXT2ICS_API_KEY", ""),
                key="api_key_input",
            )

            if api_key:
                if validate_api_key(api_key):
                    st.markdown(
                        '<div class="status-indicator status-success">✅ API Key Valid</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="status-indicator status-warning">⚠️ API Key Too Short</div>',
                        unsafe_allow_html=True,
                    )

        with col2:
            model = st.selectbox(
                "Select Model",
                options=["gpt-4.1-nano", "gpt-3.5-turbo", "gpt-4"],
                index=0,
                help="Choose the LLM model for conversion",
                key="model_select",
            )

            language = st.text_input(
                "Output Language (Optional)",
                help="e.g., 'en', 'es', 'fr' - leave blank for auto-detection",
                key="language_input",
            )

        # Update completion status
        if api_key and validate_api_key(api_key):
            st.session_state.app_state.config_completed = True
        else:
            st.session_state.app_state.config_completed = False

        st.markdown("</div>", unsafe_allow_html=True)

    return api_key, model, language


def render_input_section():
    """Render input section with file upload and text area"""
    config_completed = st.session_state.app_state.config_completed
    input_completed = st.session_state.app_state.input_completed
    conversion_started = getattr(
        st.session_state.app_state, "conversion_started", False
    )

    render_step_indicator(
        2,
        "Input Content",
        config_completed,
        input_completed,
        conversion_started,
    )

    # Only allow expansion if config is completed
    if not config_completed:
        with st.expander("📝 Add Event Content", expanded=False):
            st.info("⚠️ Please complete Step 1 (Configuration) first")
        return "", None

    # Determine if this expander should be expanded - stay expanded until conversion starts
    expand_input = config_completed and not conversion_started

    with st.expander("📝 Add Event Content", expanded=expand_input):
        st.markdown('<div class="section-container">', unsafe_allow_html=True)

        # File upload
        st.subheader("Option 1: Upload Text File")
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=["txt"],
            help="Upload a .txt file containing event details",
            key="file_uploader",
        )

        # Text area
        st.subheader("Option 2: Direct Text Input")

        # Determine initial text area content
        text_area_content = ""
        input_source = ""

        if uploaded_file is not None:
            file_hash = hashlib.md5(uploaded_file.read()).hexdigest()
            uploaded_file.seek(0)  # Reset file pointer

            if st.session_state.file_hash != file_hash:
                st.session_state.file_hash = file_hash
                text_area_content = get_file_content(uploaded_file.read())
                input_source = "📁 Content loaded from file"
            else:
                text_area_content = st.session_state.get("manual_text", "")
                input_source = "📁 File content available"
        else:
            text_area_content = st.session_state.get("manual_text", "")
            input_source = (
                "✍️ Manual input"
                if text_area_content
                else "💡 Enter text or upload file"
            )

        manual_text = st.text_area(
            "Event Text",
            value=text_area_content,
            height=250,
            help="Type or paste your event text here",
            key="manual_text",
        )

        # Show input source indicator
        if input_source:
            st.markdown(
                f'<div class="status-indicator status-info">{input_source}</div>',
                unsafe_allow_html=True,
            )

        # Update completion status
        if manual_text and len(manual_text.strip()) > 10:
            st.session_state.app_state.input_completed = True
        else:
            st.session_state.app_state.input_completed = False

        st.markdown("</div>", unsafe_allow_html=True)

    return manual_text, uploaded_file


@st.cache_data(ttl=3600)
def process_content_cached(
    content: str,
    api_key: str,
    model: str,
    language: Optional[str],
    _process_content_func,
):
    """Cache expensive API calls"""
    result = _process_content_func(
        content=content, api_key=api_key, model=model, language=language
    )
    return result


def render_cache_controls():
    """Add cache management controls to sidebar"""
    with st.sidebar:
        st.markdown("### 🔧 Debug Panel")
        
        # Cache controls
        st.markdown("**Cache Management**")
        if st.button("🗑️ Clear Cache", help="Clear all cached API responses"):
            process_content_cached.clear()
            st.session_state.app_state.last_cache_status = ""
            st.session_state.app_state.last_processing_time = 0.0
            st.success("✅ Cache cleared!")
            st.rerun()
        
        # Show last operation info
        if st.session_state.app_state.last_cache_status:
            st.markdown("**Last Operation**")
            st.markdown(
                f'<div class="status-indicator status-info">'
                f'{st.session_state.app_state.last_cache_status}'
                f'</div>',
                unsafe_allow_html=True,
            )
            
            if st.session_state.app_state.last_processing_time > 0:
                st.metric(
                    "Processing Time", 
                    f"{st.session_state.app_state.last_processing_time:.2f}s"
                )
        
        # Show cache stats
        st.markdown("**Cache Info**")
        st.info("Cache TTL: 1 hour")
        
        # Show current session state for debugging
        with st.expander("🔍 Session Debug", expanded=False):
            st.write("**App State:**")
            st.json({
                "config_completed": st.session_state.app_state.config_completed,
                "input_completed": st.session_state.app_state.input_completed,
                "conversion_started": st.session_state.app_state.conversion_started,
            })


def render_conversion_section(
    text_content: str,
    api_key: str,
    model: str,
    language: str,
    process_content_func,
):
    """Render conversion section"""
    if not text_content or not api_key:
        return

    # Validation checks
    ready_to_convert = True
    issues = []

    if not validate_api_key(api_key):
        issues.append("❌ Invalid API key")
        ready_to_convert = False

    if len(text_content.strip()) < 10:
        issues.append("❌ Text content too short")
        ready_to_convert = False

    if issues:
        for issue in issues:
            st.markdown(
                f'<div class="status-indicator status-warning">{issue}</div>',
                unsafe_allow_html=True,
            )

    # conversion button
    if st.button(
        "🚀 Generate ICS Calendar",
        disabled=not ready_to_convert,
        use_container_width=True,
        key="convert_button",
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
            
            ics_content = process_content_cached(
                text_content,
                api_key,
                model,
                language if language else None,
                process_content_func,
            )
            
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

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Conversion failed: {str(e)}")
            st.info("💡 Try checking your API key or simplifying the input text")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Display results
        st.subheader("📋 Generated ICS Calendar")

        # Show calendar preview
        with st.expander("View Calendar Content", expanded=True):
            st.code(ics_content, language="text")

        # Download button
        st.download_button(
            label="💾 Download Calendar File",
            data=ics_content.encode("utf-8"),
            help="Open the downloaded file to quickly add it to you calender",
            file_name=f"calendar_{int(time.time())}.ics",
            mime="text/calendar",
            use_container_width=True,
        )

        # Success message
        st.success("🎉 Calendar generated successfully!")

        # Statistics
        event_count = ics_content.count("BEGIN:VEVENT")
        if event_count > 0:
            st.info(f"📊 Generated {event_count} calendar event(s)")

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Text to ICS Converter",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded",  # Changed to show debug panel
    )

    # Initialize app
    init_session_state()
    load_custom_css()

    # Check dependencies
    try:
        from text2ics import process_content
    except ImportError:
        st.error("❌ Missing dependency: 'text2ics' package not found")
        st.info("💡 To install, run: `pip install -e .` from the project root.")
        st.stop()

    # Add debug panel to sidebar
    render_cache_controls()

    # Render UI
    render_header()

    # Main content area with guided steps
    api_key, model, language = render_config_section()
    text_content, uploaded_file = render_input_section()

    # Show next steps only if previous steps are completed
    if (
        st.session_state.app_state.config_completed
        and st.session_state.app_state.input_completed
    ):
        if text_content:
            render_conversion_section(
                text_content, api_key, model, language, process_content
            )
    elif not st.session_state.app_state.config_completed:
        st.info("👆 Please complete Step 1 to continue")
    elif not st.session_state.app_state.input_completed:
        st.info("👆 Please complete Step 2 to continue")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.9rem;'>"
        "Built with ❤️ using Streamlit • AI-powered calendar conversion"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
