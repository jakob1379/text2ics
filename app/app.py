import streamlit as st
from state import init_session_state
from ui import (
    load_bmac_button,
    load_custom_css,
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
        layout="centered",
        menu_items={
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
        # If importing fails, try adding the project root to sys.path so the local package can be imported
        import sys
        import os

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

    # Main content area with guided steps
    api_key, model, language = render_config_section()
    text_content, uploaded_file = render_input_section()

    # Show next steps only if previous steps are completed
    if st.session_state.app_state.config_completed and st.session_state.app_state.input_completed:
        if text_content:
            render_conversion_section(text_content, api_key, model, language, process_content)
    elif not st.session_state.app_state.config_completed:
        st.info("👆 Please complete Step 1 to continue")
    elif not st.session_state.app_state.input_completed:
        st.info("👆 Please complete Step 2 to continue")

    # Footer
    st.markdown("---")
    st.markdown(
        (
            "<div style='text-align: center; color: #64748b; font-size: 0.9rem;'>"
            "Built with ❤️ using Streamlit •"
            "AI-powered calendar conversion •"
            "text2ics v{version('text2ics')}"
            "</div><br>"
        ),
        unsafe_allow_html=True,
    )

    load_bmac_button()


if __name__ == "__main__":
    main()
