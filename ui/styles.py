"""
UI Styles: ui/styles.py
Purpose: Centralized CSS styles for the Streamlit application.
"""

MAIN_STYLES = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styling with compact spacing */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
        margin: 0 auto;
    }

    /* Typography hierarchy with compact spacing */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        margin-top: 1.4rem !important;
        margin-bottom: 1rem !important;
        line-height: 1.3 !important;
    }

    p {
        margin-bottom: 1rem !important;
        line-height: 1.6 !important;
    }

    /* Consistent glass morphism card styling - darker glass effect */
    .glass-card {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Modern input styling with professional orange theme */
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 16px 20px;
        border-radius: 16px;
        border: 2px solid rgba(230, 126, 34, 0.3);
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        color: #1a1a1a !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #E67E22;
        box-shadow: 0 0 0 4px rgba(230, 126, 34, 0.1);
        background: rgba(255, 255, 255, 0.95);
        color: #1a1a1a !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #6b7280 !important;
        opacity: 0.7;
    }

    /* Modern button styling with orange to purple gradient - v3 FORCE UPDATE */
    .stButton > button {
        background: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
        background-color: #E67E22 !important;
        background-image: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 32px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 20px rgba(230, 126, 34, 0.3) !important;
        height: 58px !important;
        min-height: 58px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 30px rgba(230, 126, 34, 0.4) !important;
        background: linear-gradient(135deg, #F39C12 0%, #B965F7 100%) !important;
        background-color: #F39C12 !important;
        background-image: linear-gradient(135deg, #F39C12 0%, #B965F7 100%) !important;
    }

    /* Additional button selectors to override any cached styles */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
        background-color: #E67E22 !important;
        background-image: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
        background-color: #E67E22 !important;
        background-image: linear-gradient(135deg, #E67E22 0%, #A855F7 100%) !important;
    }

    /* Citation cards with consistent darker glass morphism */
    .citation-card {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        min-height: 80px;
    }

    /* AI Answer card with distinct styling to prevent conflicts */
    .ai-answer-card {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        min-height: 80px;
    }

    /* Sidebar styling - compact */
    .css-1d391kg {
        padding: 1.5rem 1rem;
    }

    /* Success/warning/error message styling */
    .stAlert {
        border-radius: 16px;
        border: none;
        margin: 1rem 0;
    }

    /* Main header with adjusted spacing */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #E67E22, #A855F7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }

    /* Progress bar enhancement */
    .stProgress .st-bp {
        background: linear-gradient(135deg, #E67E22, #A855F7);
        border-radius: 10px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Column spacing adjustments */
    .stColumn {
        margin: 0 0.5rem;
    }

    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.8rem !important;
    }

    /* Compact spacing for metrics */
    .metric {
        margin-bottom: 0.5rem !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #E67E22, #A855F7);
        color: white;
    }

    /* Spinner customization */
    .stSpinner {
        text-align: center;
        margin: 2rem 0;
    }

    /* Code block styling for citations */
    code {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        padding: 0.5rem !important;
        border-radius: 8px !important;
    }

    /* File uploader styling */
    .stFileUploader {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        border: 2px dashed rgba(230, 126, 34, 0.3);
    }

    /* Multiselect styling */
    .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        border: 2px solid rgba(230, 126, 34, 0.3);
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        border: 2px solid rgba(230, 126, 34, 0.3);
    }

    /* Slider styling */
    .stSlider > div > div > div {
        background: linear-gradient(135deg, #E67E22, #A855F7);
    }

    /* Enhanced table styling */
    .stDataFrame {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Chart styling */
    .stPlotlyChart {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Reduced whitespace globally */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
"""

ANIMATION_STYLES = """
    <style>
    @keyframes pulse {
        0% { background: rgba(168, 85, 247, 0.4); }
        50% { background: rgba(168, 85, 247, 0.1); }
        100% { background: rgba(168, 85, 247, 0.2); }
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    </style>
"""
