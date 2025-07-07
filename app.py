import streamlit as st
from pathlib import Path
from typing import Optional
import os
import hashlib
import time
from dataclasses import dataclass

# Custom CSS for professional styling
def load_custom_css():
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global styling */
        .stApp {
            font-family: 'Inter', sans-serif;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 0;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 20px 20px;
            color: white;
            text-align: center;
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .main-header p {
            font-size: 1.1rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .streamlit-expanderContent {
            background: white;
            border: 1px solid #e2e8f0;
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 1.5rem;
            margin-top: -1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Section styling */
        .section-container {
            background: transparent;
            padding: 0;
            margin: 0;
        }
        
        .section-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.5rem;
        }
        
        /* Step indicators */
        .step-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        .step-active {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        
        .step-completed {
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #bfdbfe;
        }
        
        .step-pending {
            background: #f1f5f9;
            color: #64748b;
            border: 1px solid #e2e8f0;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status-success {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        
        .status-warning {
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }
        
        .status-info {
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #bfdbfe;
        }
        
        /* Button styling */
        .stButton > button {
            border: true;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.15s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Input styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            transition: border-color 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* File uploader styling */
        .stFileUploader > div {
            border-radius: 8px;
            border: 2px dashed #e2e8f0;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stFileUploader > div:hover {
            border-color: #667eea;
            background: #f8fafc;
        }
        
        /* Progress bar */
        .progress-container {
            background: #f1f5f9;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

@dataclass
class AppState:
    """Application state management"""
    input_text: str = ""
    uploaded_file_content: str = ""
    api_key: str = ""
    model: str = "gpt-4.1-nano"
    language: str = ""
    processing: bool = False
    config_completed: bool = False
    input_completed: bool = False

def init_session_state():
    """Initialize session state variables"""
    if 'app_state' not in st.session_state:
        st.session_state.app_state = AppState()
    
    if 'file_hash' not in st.session_state:
        st.session_state.file_hash = None
    
    if 'result_cache' not in st.session_state:
        st.session_state.result_cache = {}
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1

@st.cache_data(ttl=3600)
def get_file_content(file_bytes: bytes) -> str:
    """Cache file content reading"""
    return file_bytes.decode("utf-8")

@st.cache_data(ttl=3600)
def validate_api_key(api_key: str) -> bool:
    """Basic API key validation"""
    return len(api_key.strip()) > 10

def create_file_hash(content: str) -> str:
    """Create hash for content caching"""
    return hashlib.md5(content.encode()).hexdigest()

def render_header():
    """Render professional header"""
    st.markdown("""
    <div class="main-header">
        <h1>📅 Text to ICS Converter</h1>
        <p>Transform your event descriptions into calendar files with AI precision</p>
    </div>
    """, unsafe_allow_html=True)

def get_step_status(step_num: int, config_completed: bool, input_completed: bool) -> str:
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
        return "step-active"

def render_step_indicator(step_num: int, title: str, config_completed: bool, input_completed: bool):
    """Render step indicator"""
    status = get_step_status(step_num, config_completed, input_completed)
    
    if status == "step-completed":
        icon = "✅"
    elif status == "step-active":
        icon = "🔄"
    else:
        icon = "⏳"
    
    st.markdown(f'<div class="step-indicator {status}">{icon} Step {step_num}: {title}</div>', 
                unsafe_allow_html=True)

def render_config_section():
    """Render configuration section"""
    config_completed = st.session_state.app_state.config_completed
    input_completed = st.session_state.app_state.input_completed
    
    render_step_indicator(1, "Configuration", config_completed, input_completed)
    
    # Determine if this expander should be expanded
    expand_config = not config_completed or st.session_state.current_step == 1
    
    with st.expander("🔧 Setup API Configuration", expanded=expand_config):
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "LLM Service API Key",
                type="password",
                help="Enter your API key for the LLM service",
                value=os.environ.get("TXT2ICS_API_KEY", ""),
                key="api_key_input"
            )
            
            if api_key:
                if validate_api_key(api_key):
                    st.markdown('<div class="status-indicator status-success">✅ API Key Valid</div>', 
                               unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-indicator status-warning">⚠️ API Key Too Short</div>', 
                               unsafe_allow_html=True)
        
        with col2:
            model = st.selectbox(
                "Select Model",
                options=["gpt-4.1-nano", "gpt-3.5-turbo", "gpt-4"],
                index=0,
                help="Choose the LLM model for conversion",
                key="model_select"
            )
            
            language = st.text_input(
                "Output Language (Optional)",
                help="e.g., 'en', 'es', 'fr' - leave blank for auto-detection",
                key="language_input"
            )
        
        # Update completion status
        if api_key and validate_api_key(api_key):
            if not st.session_state.app_state.config_completed:
                st.session_state.app_state.config_completed = True
                st.session_state.current_step = 2
                st.rerun()
        else:
            st.session_state.app_state.config_completed = False
            st.session_state.current_step = 1
        
        if st.session_state.app_state.config_completed:
            st.success("✅ Configuration complete! Proceed to Step 2.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return api_key, model, language

def render_input_section():
    """Render input section with file upload and text area"""
    config_completed = st.session_state.app_state.config_completed
    input_completed = st.session_state.app_state.input_completed
    
    render_step_indicator(2, "Input Content", config_completed, input_completed)
    
    # Only allow expansion if config is completed
    if not config_completed:
        with st.expander("📝 Add Event Content", expanded=False):
            st.info("⚠️ Please complete Step 1 (Configuration) first")
        return "", None
    
    # Determine if this expander should be expanded
    expand_input = not input_completed or st.session_state.current_step == 2
    
    with st.expander("📝 Add Event Content", expanded=expand_input):
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        
        # File upload
        st.subheader("Option 1: Upload Text File")
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=["txt"],
            help="Upload a .txt file containing event details",
            key="file_uploader"
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
                text_area_content = st.session_state.get('manual_text', '')
                input_source = "📁 File content available"
        else:
            text_area_content = st.session_state.get('manual_text', '')
            input_source = "✍️ Manual input" if text_area_content else "💡 Enter text or upload file"
        
        manual_text = st.text_area(
            "Event Text",
            value=text_area_content,
            height=250,
            help="Type or paste your event text here",
            key="manual_text"
        )
        
        # Show input source indicator
        if input_source:
            st.markdown(f'<div class="status-indicator status-info">{input_source}</div>', 
                       unsafe_allow_html=True)
        
        # Update completion status
        if manual_text and len(manual_text.strip()) > 10:
            if not st.session_state.app_state.input_completed:
                st.session_state.app_state.input_completed = True
                st.session_state.current_step = 3
                st.rerun()
        else:
            st.session_state.app_state.input_completed = False
            if config_completed:
                st.session_state.current_step = 2
        
        if st.session_state.app_state.input_completed:
            st.success("✅ Content added! Ready for Step 3.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return manual_text, uploaded_file

def render_preview_section(text_content: str):
    """Render content preview section"""
    if not text_content:
        return
    
    config_completed = st.session_state.app_state.config_completed
    input_completed = st.session_state.app_state.input_completed
    
    render_step_indicator(3, "Generate Calendar", config_completed, input_completed)
    
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">👀 Content Preview</div>', unsafe_allow_html=True)
    
    # Show content stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Characters", len(text_content))
    with col2:
        st.metric("Words", len(text_content.split()))
    with col3:
        st.metric("Lines", len(text_content.split('\n')))
    
    # Show preview
    preview_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
    st.text_area("Content Preview", preview_text, height=150, disabled=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def process_content_cached(content: str, api_key: str, model: str, language: Optional[str]):
    """Cache expensive API calls"""
    try:
        from text2ics.converter import process_content
        return process_content(
            content=content,
            api_key=api_key,
            model=model,
            language=language
        )
    except ImportError:
        raise ImportError("text2ics package not found")

def render_conversion_section(text_content: str, api_key: str, model: str, language: str):
    """Render conversion section"""
    if not text_content or not api_key:
        return
    
    # st.markdown('<div class="section-container">', unsafe_allow_html=True)
    # st.markdown('<div class="section-header">🔄 Convert to Calendar file</div>', unsafe_allow_html=True)
    
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
            st.markdown(f'<div class="status-indicator status-warning">{issue}</div>', 
                       unsafe_allow_html=True)
    # else:
    #     st.markdown('<div class="status-indicator status-success">✅ Ready to convert</div>', 
    #                unsafe_allow_html=True)
    
    # conversion button
    if st.button("🚀 Generate ICS Calendar", 
                 disabled=not ready_to_convert,
                 use_container_width=True,
                 key="convert_button"):
        
        # Create content hash for caching
        content_hash = create_file_hash(f"{text_content}{api_key}{model}{language}")
        
        # Check cache first
        if content_hash in st.session_state.result_cache:
            st.success("📋 Using cached result")
            ics_content = st.session_state.result_cache[content_hash]
        else:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Initializing conversion...")
                progress_bar.progress(25)
                time.sleep(0.5)
                
                status_text.text("🤖 Processing...")
                progress_bar.progress(50)
                
                ics_content = process_content_cached(
                    text_content, api_key, model, language if language else None
                )
                
                progress_bar.progress(75)
                status_text.text("📅 Generating calendar...")
                time.sleep(0.5)
                
                progress_bar.progress(100)
                status_text.text("✅ Conversion complete!")
                
                # Cache the result
                st.session_state.result_cache[content_hash] = ics_content
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Conversion failed: {str(e)}")
                st.info("💡 Try checking your API key or simplifying the input text")
                st.markdown('</div>', unsafe_allow_html=True)
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
            file_name=f"calendar_{int(time.time())}.ics",
            mime="text/calendar",
            use_container_width=True
        )
        
        # Success message
        st.success("🎉 Calendar generated successfully!")
        
        # Statistics
        event_count = ics_content.count('BEGIN:VEVENT')
        if event_count > 0:
            st.info(f"📊 Generated {event_count} calendar event(s)")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Text to ICS Converter",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize app
    init_session_state()
    load_custom_css()
    
    # Check dependencies
    try:
        from text2ics.converter import process_content
    except ImportError:
        st.error("❌ Missing dependency: 'text2ics' package not found")
        st.info("💡 Install with: `pip install text2ics`")
        st.stop()
    
    # Render UI
    render_header()
    
    # Main content area with guided steps
    api_key, model, language = render_config_section()
    text_content, uploaded_file = render_input_section()
    
    # Show next steps only if previous steps are completed
    if st.session_state.app_state.config_completed and st.session_state.app_state.input_completed:
        if text_content:
            render_preview_section(text_content)
            render_conversion_section(text_content, api_key, model, language)
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
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
