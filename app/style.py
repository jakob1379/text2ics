bmc_slug = "FYmB2qPIYv"

# Set a desired height, let the browser calculate width based on aspect ratio
# This will prevent distortion and likely work better.

bmac_html = f"""
<p style="text-align: center;">
    <a href="https://www.buymeacoffee.com/{bmc_slug}" target="_blank" rel="noopener noreferrer">
        <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&slug={bmc_slug}&button_colour=FF5F5F&font_colour=FFFFFF&font_family=Lato&coffee_colour=FFDD00&for_wp=true&point_colour=40A4ED"
             alt="Buy Me A Coffee"
             style="height: 0 !important; width: auto !important; display: block; margin: 0 auto; border: 0px solid #000000; "
        >
    </a>
</p>
"""

css = """
    <style>
        /* Simplified CSS - Focus on essential improvements */
        .stApp {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Welcome banner header */
        .welcome-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2.5rem 1rem;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 20px 20px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .welcome-header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .welcome-header p {
            font-size: 1.2rem;
            margin: 0;
            opacity: 0.95;
            font-weight: 400;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
            line-height: 1.5;
        }
        
        /* Make inputs a bit nicer */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 6px;
        }
        
        /* Improve file uploader appearance */
        .stFileUploader > div {
            border-radius: 8px;
            border: 2px dashed #e0e0e0;
        }
        
        /* Hide default Streamlit elements for cleaner look */
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Step indicators */
        .step-indicator {
            display: block;
            padding: 8px 16px;
            margin: 4px auto;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.9rem;
            text-align: center;
            width: fit-content;
            min-width: 120px;
        }
        /* Colours chosen for >= 4.5:1 contrast (WCAG AA, normal text) */
        .step-completed {
            background-color: #047857;
            color: white;
        }
        .step-active {
            background-color: #2563eb;
            color: white;
        }
        .step-pending {
            background-color: #e5e7eb;
            color: #4b5563;
        }
    </style>
"""
