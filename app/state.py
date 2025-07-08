from dataclasses import dataclass

import streamlit as st


@dataclass
class AppState:
    """Application state management"""

    api_key: str = ""
    model: str = "gpt-4.1-nano"
    language: str = ""
    config_completed: bool = False
    input_completed: bool = False
    conversion_started: bool = False
    last_cache_status: str = ""
    last_processing_time: float = 0.0


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
