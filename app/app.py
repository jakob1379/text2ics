from importlib.metadata import version

import streamlit as st
from state import init_session_state
from style import bmac_html
from ui import (
    load_custom_css,
    render_config_section,
    render_conversion_section,
    render_header,
    render_input_section,
    render_step_indicator,
)


def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Text to ICS Converter",
        page_icon="📅",
        layout="centered",
        # Streamlit accepts this at runtime; its MenuItems TypedDict is stricter
        # about key casing than the implementation.
        menu_items={  # pyright: ignore[reportArgumentType]
            "Report a Bug": "https://github.com/jakob1379/text2ics/issues",
            "About": "https://github.com/jakob1379/text2ics",
        },
    )

    # Initialize app
    init_session_state()
    load_custom_css()

    # Check dependencies
    try:
        # Prefer importing the converter directly so the local package works without installation
        from text2ics.converter import process_content
    except Exception:
        # If importing fails, try adding the project root to sys.path so the local package can be
        # imported
        import os
        import sys

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        try:
            from text2ics.converter import process_content
        except Exception:
            st.error("❌ Missing dependency: 'text2ics' package not found")
            st.info("💡 To install, run: `pip install -e .` from the project root.")
            st.stop()

    # Render UI
    render_header()

    # Show progress steps
    app_state = st.session_state.app_state
    col1, col2, col3 = st.columns(3)
    with col1:
        render_step_indicator(
            1,
            "API Key",
            app_state.config_completed,
            app_state.input_completed,
            app_state.conversion_started,
        )
    with col2:
        render_step_indicator(
            2,
            "Enter Events",
            app_state.config_completed,
            app_state.input_completed,
            app_state.conversion_started,
        )
    with col3:
        render_step_indicator(
            3,
            "Generate",
            app_state.config_completed,
            app_state.input_completed,
            app_state.conversion_started,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content area with simplified flow
    api_key, model, language = render_config_section()
    text_content, uploaded_file = render_input_section()

    # Always show conversion section (button disabled if not ready)
    if text_content:
        render_conversion_section(text_content, api_key, model, language, process_content)
    else:
        st.info("✍️ Enter event text above to generate a calendar")

    # Footer
    st.markdown("---")
    st.markdown(
        (
            "<div style='text-align: center; color: #64748b; font-size: 0.9rem;'>"
            "Built with ❤️ using Streamlit •"
            "AI-powered calendar conversion •"
            f"text2ics v{version('text2ics')}"
            "</div><br>"
            f"{bmac_html}"
        ),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
