import streamlit as st
from importlib.metadata import version

from state import init_session_state
from ui import (
    load_custom_css,
    render_cache_controls,
    render_config_section,
    render_conversion_section,
    render_header,
    render_input_section,
)


def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Text to ICS Converter",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="collapsed",
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
        f"Built with ❤️ using Streamlit • AI-powered calendar conversion • text2ics v{version('text2ics')}"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
