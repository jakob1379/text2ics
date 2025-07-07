import streamlit as st
from pathlib import Path
from typing import Optional
import os

# Assuming text2ics.converter is an installed package
try:
    from text2ics.converter import process_content
except ImportError:
    st.error(
        "Could not import 'process_content' from 'text2ics'. Make sure the 'text2ics' package is installed or 'converter.py' is in the same directory."
    )
    st.stop()

# Initialize session state for input_text if it doesn't exist
if "input_text_area" not in st.session_state:
    st.session_state.input_text_area = ""


def main():
    st.set_page_config(
        page_title="Text to ICS Converter", layout="wide"
    )  # Changed to wide for better layout
    st.title("📄 Text to ICS Converter")
    st.write(
        "Provide event text by uploading a file OR by pasting text directly. Then, provide your API key to convert the content into an ICS calendar."
    )

    with st.container():
        col1, col2 = st.columns(2)
        api_key: Optional[str] = col1.text_input(
            "LLM Service API Key",
            type="password",
            help="Enter your API key for the LLM service. You can also set it as an environment variable TXT2ICS_API_KEY.",
            value=os.environ.get("TXT2ICS_API_KEY", ""),
        )
        # Model selection
        model: str = col2.selectbox(
            "Select Model",
            options=["gpt-4.1-nano", "gpt-3.5-turbo", "gpt-4"],
            index=0,
            help="Choose the LLM model to use for conversion.",
        )

    st.markdown("---")  # Separator for better visual grouping

    # Create two columns for input options
    st.subheader("Option 1: Upload a Text File")
    uploaded_file = st.file_uploader(
        "Upload Text File",
        type=["txt"],
        help="Select a text file (.txt) containing event details.",
    )

    st.subheader("Option 2: Paste Event Text Directly")
    # Use a key to ensure this widget's state is managed separately
    # Use session state to manage the value for clearer behavior
    # Add a callback to clear the file uploader if text is entered manually
    input_text_manual = st.text_area(
        "Paste Event Text Here",
        key="manual_input_text_area",
        height=300,  # Increased height for better user experience
        help="Type or paste your event text here. This will override any uploaded file content.",
        value=st.session_state.input_text_area,
        on_change=lambda: st.session_state.__setitem__(
            "uploaded_file_cleared", True
        ),
        disabled=True if uploaded_file else False,
    )

    # --- Determine the final text to process ---
    text_to_process = ""
    input_source_message = ""

    if uploaded_file is not None and not st.session_state.get(
        "uploaded_file_cleared", False
    ):
        text_to_process = uploaded_file.read().decode("utf-8")
        input_source_message = "Content sourced from **uploaded file**."
        # Update text area with file content for display, but keep it editable if user wishes
        # This will re-run, so `uploaded_file_cleared` is important
        if st.session_state.input_text_area != text_to_process:
            st.session_state.input_text_area = text_to_process
            st.rerun()  # Rerun to update the text_area's displayed value

    elif input_text_manual:
        text_to_process = input_text_manual
        input_source_message = "Content sourced from **manual text input**."
        # If user types after uploading, clear the "uploaded_file_cleared" flag
        if st.session_state.get("uploaded_file_cleared", False):
            st.session_state.uploaded_file_cleared = (
                False  # Reset for next interaction
            )

    else:
        st.info("Please upload a text file OR paste event text above to begin.")

    st.markdown("---")  # Separator before model/language options

    # Language selection
    language: Optional[str] = st.text_input(
        "Output Language (Optional)",
        help="Specify the output language for the ICS file (e.g., 'en' for English, 'es' for Spanish). If left blank, the language will be guessed from the content.",
        value="",
    )

    st.markdown("---")  # Separator before conversion button

    if text_to_process and api_key:
        st.subheader("Text for Conversion:")
        st.info(input_source_message)
        st.text_area(
            "Review Content", text_to_process, height=135, disabled=True
        )

        if st.button(
            "Generate ICS Calendar", use_container_width=True
        ):  # Button fills width
            if not api_key:
                st.warning("Please enter your API key to proceed.")
                return

            with st.spinner(
                "Converting text to ICS... This may take a moment."
            ):
                try:
                    ics_calendar = process_content(
                        content=text_to_process,
                        api_key=api_key,
                        model=model,
                        language=language if language else None,
                    )
                    st.subheader("Generated ICS Calendar:")
                    st.code(ics_calendar, language="markup")

                    st.download_button(
                        label="Download ICS File",
                        data=ics_calendar.encode("utf-8"),
                        file_name="calendar.ics",
                        mime="text/calendar",
                        use_container_width=True,
                    )
                    st.success("ICS calendar generated successfully!")
                except Exception as e:
                    st.error(f"An error occurred during conversion: {e}")
                    st.info(
                        "Please check your API key, input text format, or try a different model."
                    )
    elif not text_to_process and st.session_state.get(
        "uploaded_file_cleared", False
    ):
        st.warning(
            "Please provide input text either by uploading a file or pasting text manually."
        )
    elif not api_key and text_to_process:
        st.info("Please provide your API key to generate the calendar.")


if __name__ == "__main__":
    main()
