"""UI: ui/app.py
Purpose: Streamlit UI for AI File Search with ask & cite functionality
Features: Question input, AI answers, citations, performance stats, modern design
Usage: streamlit run ui/app.py
"""

# Import our core functionality
import re
import sys
import time
from pathlib import Path

import streamlit as st
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))
from core.ask import answer_question


def load_welcome_text():
    """Load the welcome text from prompts/ui_welcome.md"""
    try:
        welcome_path = Path(__file__).parent.parent / "prompts" / "ui_welcome.md"
        with open(welcome_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "# AI File Search\nWelcome to your local AI-powered document search!"


def format_citations(citations):
    """Format citations for display with clean, professional formatting - no emojis, bullet points"""
    if not citations:
        return "No citations available."

    formatted = []
    for i, cite in enumerate(citations):
        # Clean up the file path for better display
        file_display = cite["file"].replace("\\", "/")

        # Better content processing for bullet points - DISPLAY ALL CONTENT
        content = cite["chunk"]

        # Enhanced content splitting to preserve ALL content
        bullet_points = []

        if ". " in content and len(content.split(". ")) > 2:
            # Split by sentences - NO LIMIT, show all sentences
            sentences = re.split(r"(?<=\.)\s+", content)
            parts = [s.strip() for s in sentences if s.strip()]

            for part in parts:  # Remove [:3] limit - show ALL parts
                # Clean up and ensure proper punctuation
                part = part.strip()
                if (
                    part
                    and not part.endswith(".")
                    and not part.endswith("!")
                    and not part.endswith("?")
                ):
                    part += "."
                if part:  # Only add non-empty parts
                    bullet_points.append(f"• {part}")

        elif " - " in content and len(content.split(" - ")) > 2:
            # Split by dashes - NO LIMIT, show all parts
            parts = [s.strip() for s in content.split(" - ") if s.strip()]
            for part in parts:  # Remove [:3] limit
                part = part.strip()
                # For dash-separated content, ensure each part is complete
                if (
                    part
                    and not part.endswith(".")
                    and not part.endswith("!")
                    and not part.endswith("?")
                ):
                    if len(part) > 20:  # Only add period for substantial content
                        part += "."
                if part:  # Only add non-empty parts
                    bullet_points.append(f"• {part}")

        elif "\n" in content:
            # Split by line breaks
            parts = [s.strip() for s in content.split("\n") if s.strip()]
            bullet_points = [f"• {part}" for part in parts]

        else:
            # Fallback: Split into logical chunks of 15-20 words to preserve readability
            words = content.split()
            chunk_size = 20  # Fixed reasonable size instead of dividing by 3

            for j in range(0, len(words), chunk_size):
                chunk = " ".join(words[j : j + chunk_size])
                if chunk.strip():
                    bullet_points.append(f"• {chunk}")

        # If no bullet points created, use the full content as one bullet
        if not bullet_points:
            bullet_points = [f"• {content}"]

        # Convert bullet points to HTML for proper rendering
        bullet_html = "<br>".join(bullet_points)

        # Enhanced styling with better spacing and typography
        formatted.append(
            f'<div class="citation-card" style="'
            f"background: linear-gradient(135deg, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.3) 100%); "
            f"backdrop-filter: blur(20px); "
            f"color: #ffffff; "
            f"padding: 2rem; "
            f"border-radius: 16px; "
            f"margin: 1.5rem 0; "
            f"border: 1px solid rgba(255, 255, 255, 0.15); "
            f"box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); "
            f"position: relative; "
            f"overflow: hidden;"
            f'">'
            f'<div style="'
            f"color: #ffffff; "
            f"font-size: 14px; "
            f"line-height: 1.8; "
            f"font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; "
            f"font-weight: 400;"
            f'">'
            f'<div style="color: #E67E22; font-weight: 600; font-size: 16px; margin-bottom: 1rem;">SOURCE {i+1}</div>'
            f'<div style="margin-bottom: 0.5rem;"><strong>File:</strong> <code style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">{file_display}</code></div>'
            f'<div style="margin-bottom: 0.5rem;"><strong>Score:</strong> {cite.get("score", 0):.3f} | <strong>Page:</strong> {cite["page"]}</div>'
            f'<div style="margin-top: 1rem;"><strong>Content:</strong></div>'
            f'<div style="margin-top: 0.5rem; padding-left: 0.5rem; line-height: 1.6;">{bullet_html}</div>'
            f"</div>"
            f'<div style="'
            f"position: absolute; "
            f"top: 0; "
            f"left: 0; "
            f"width: 4px; "
            f"height: 100%; "
            f"background: linear-gradient(135deg, #E67E22 0%, #A855F7 100%); "
            f"border-radius: 0 0 0 16px;"
            f'"></div>'
            f"</div>"
        )
    return "\n".join(formatted)


def print_search_results(results):
    for result in results:
        print(f"Found in: {result['path']}")
        print(result["chunk"])
        print("-" * 40)


def main():
    """Main Streamlit application"""

    # Page configuration
    st.set_page_config(
        page_title="AI File Search",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Enhanced Modern CSS with Orange Theme and Compact Design
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### SETTINGS Performance Dashboard")

        # Theme section
        st.markdown("#### APPEARANCE Appearance")
        st.markdown(
            "<div class='glass-card'>"
            "<small>HINT: Use the ⋮ menu → Settings to toggle dark/light mode</small></div>",
            unsafe_allow_html=True,
        )

        # Performance metrics section
        st.markdown("#### STATS System Status")

        # Initialize session state for performance tracking
        if "performance_history" not in st.session_state:
            st.session_state.performance_history = {
                "query_times": [],
                "answer_lengths": [],
                "citation_counts": [],
            }

        # Display current performance metrics
        if st.session_state.performance_history["query_times"]:
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_time = sum(
                        st.session_state.performance_history["query_times"]
                    ) / len(st.session_state.performance_history["query_times"])
                    st.metric(
                        "SPEED Response Time",
                        f"{avg_time:.1f}s",
                        delta=f"{avg_time - 2.0:.1f}s" if avg_time > 2.0 else None,
                    )

                with col2:
                    avg_length = sum(
                        st.session_state.performance_history["answer_lengths"]
                    ) / len(st.session_state.performance_history["answer_lengths"])
                    st.metric(
                        "LENGTH Answer Length",
                        f"{avg_length:.0f} chars",
                        delta=f"{avg_length - 200:.0f}" if avg_length > 200 else None,
                    )

                with col3:
                    avg_citations = sum(
                        st.session_state.performance_history["citation_counts"]
                    ) / len(st.session_state.performance_history["citation_counts"])
                    st.metric(
                        "SOURCES Citations Found",
                        f"{avg_citations:.1f}",
                        delta=f"{avg_citations - 3:.1f}" if avg_citations > 3 else None,
                    )

            # Performance chart
            if len(st.session_state.performance_history["query_times"]) > 1:
                with st.container():
                    st.metric(
                        "AVERAGE Average Time",
                        f"{sum(st.session_state.performance_history['query_times'][-5:]) / min(5, len(st.session_state.performance_history['query_times'])):.1f}s",
                        delta=None,
                    )

        else:
            st.markdown(
                "<div class='glass-card'>"
                "<p><strong>READY: Ready to answer your questions!</strong></p>"
                "</div>",
                unsafe_allow_html=True,
            )

        # Model info section
        st.markdown("#### MODEL AI Model")
        st.markdown(
            "<div class='glass-card'>"
            "<p><strong>Phi-3 Mini 4K</strong><br>"
            "Local inference, no cloud dependencies</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Knowledge base info
        st.markdown("#### KNOWLEDGE Knowledge Base")
        index_path = Path("index.faiss")
        if index_path.exists():
            st.success("Knowledge base loaded and ready")
        else:
            st.warning("Knowledge base not found. Run indexing first.")

        # Recent queries section
        st.markdown("#### QUERIES Recent Queries")
        if "recent_queries" not in st.session_state:
            st.session_state.recent_queries = []

        if st.session_state.recent_queries:
            for i, query in enumerate(st.session_state.recent_queries[-3:]):
                st.markdown(
                    f"<div class='glass-card'><small>{i+1}. {query[:50]}...</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='glass-card'><small>No recent queries</small></div>",
                unsafe_allow_html=True,
            )

    # Main content area
    st.markdown('<h1 class="main-header">AI File Search</h1>', unsafe_allow_html=True)

    # Welcome section
    welcome_text = load_welcome_text()

    # About section (compact expandable)
    with st.expander("INFO About this system", expanded=False):
        st.markdown(welcome_text)

    # Main query interface
    st.markdown("### Ask Your Question")

    # Create two columns for the input and button
    col1, col2 = st.columns([4, 1])

    with col1:
        # User input with enhanced placeholder
        question = st.text_input(
            "Question",  # Add a proper label
            placeholder="What would you like to know about your documents?",
            label_visibility="collapsed",
            key="main_question_input",
            on_change=None,  # This will allow Enter key to work
        )

    with col2:
        # Submit button
        ask_button = st.button(
            "Ask AI Assistant",
            key="ask_button",
            type="primary",
            use_container_width=True,
        )

    # Handle form submission with enhanced UX
    submitted_question = None
    if ask_button and question.strip():
        submitted_question = question.strip()
    elif ask_button and not question.strip():
        st.error("Please enter a question to get started!")

    # Process question if submitted
    if submitted_question:
        # Add to recent queries
        if submitted_question not in st.session_state.recent_queries:
            st.session_state.recent_queries.append(submitted_question)
            if len(st.session_state.recent_queries) > 10:
                st.session_state.recent_queries.pop(0)

        # Progress indication with animated steps
        progress_container = st.container()
        with progress_container:
            st.info(f"**Processing your question:** '{submitted_question}'")

            # Step-by-step progress indication
            progress_placeholder = st.empty()

            # Step 1: AI thinking
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #E67E22;">AI: AI is thinking...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 2: Document search
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #E67E22;">Searching documents...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 3: Analyzing passages
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #E67E22;">Analyzing passages...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 4: Generating response
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #A855F7;">Generating response...</h4>',
                    unsafe_allow_html=True,
                )

        # Process the question
        start_time = time.time()
        with st.spinner(f"Generating answer for: '{submitted_question[:50]}...'"):
            try:
                # Get answer and citations
                answer, citations = answer_question(submitted_question)

                # Calculate metrics
                query_time = time.time() - start_time
                answer_length = len(answer) if answer else 0
                citation_count = len(citations) if citations else 0

                # Store performance metrics
                st.session_state.performance_history["query_times"].append(query_time)
                st.session_state.performance_history["answer_lengths"].append(
                    answer_length
                )
                st.session_state.performance_history["citation_counts"].append(
                    citation_count
                )

                # Keep only last 20 entries
                for key in st.session_state.performance_history:
                    if len(st.session_state.performance_history[key]) > 20:
                        st.session_state.performance_history[key] = (
                            st.session_state.performance_history[key][-20:]
                        )

                # Clear progress and show success
                progress_placeholder.empty()
                with progress_container:
                    st.markdown(
                        '<h4 style="margin: 0; color: #22c55e;">SUCCESS: Response generated successfully!</h4>',
                        unsafe_allow_html=True,
                    )

                # Display results
                if answer and answer.strip():
                    # Success metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Query Time", f"{query_time:.1f}s")
                    with col2:
                        st.metric("Answer Length", f"{answer_length} chars")
                    with col3:
                        st.metric("Sources Found", citation_count)

                    # Success message
                    st.success(
                        f"SUCCESS: **Answer generated successfully!** ({query_time:.1f}s with {len(citations)} sources)"
                    )

                    # Display the answer
                    st.markdown("## AI: AI Answer")

                    # Display the answer with its own unique styling class
                    st.markdown(
                        f'<div class="ai-answer-card" style="'
                        f"background: linear-gradient(135deg, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.3) 100%); "
                        f"backdrop-filter: blur(20px); "
                        f"color: #ffffff; "
                        f"padding: 2rem; "
                        f"border-radius: 16px; "
                        f"margin: 1.5rem 0; "
                        f"border: 1px solid rgba(255, 255, 255, 0.15); "
                        f"box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); "
                        f"position: relative; "
                        f"overflow: hidden;"
                        f'">'
                        f'<div style="'
                        f"color: #ffffff; "
                        f"font-size: 16px; "
                        f"line-height: 1.8; "
                        f"white-space: pre-wrap; "
                        f"font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; "
                        f"font-weight: 400;"
                        f'">'
                        f'<div style="color: #A855F7; font-weight: 600; font-size: 18px; margin-bottom: 1rem;">AI RESPONSE</div>'
                        f'<div style="margin-top: 0.5rem; line-height: 1.8; font-size: 16px;">{answer}</div>'
                        f"</div>"
                        f'<div style="'
                        f"position: absolute; "
                        f"top: 0; "
                        f"left: 0; "
                        f"width: 4px; "
                        f"height: 100%; "
                        f"background: linear-gradient(135deg, #A855F7 0%, #E67E22 100%); "
                        f"border-radius: 0 0 0 16px;"
                        f'"></div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    # Display citations if available - moved right after answer
                    if citations and len(citations) > 0:
                        st.markdown("## SOURCES: Sources & Citations")
                        citation_html = format_citations(citations)
                        st.markdown(citation_html, unsafe_allow_html=True)
                    else:
                        st.warning("No specific citations found for this query.")

                    # Create two columns for performance metrics
                    col1, col2 = st.columns([2, 1])

                    with col2:
                        # Performance metrics section
                        st.markdown("### METRICS: Performance Metrics")

                        # Response time
                        st.markdown(
                            f'<div class="metric-card">'
                            f'<h4 style="margin: 0; color: #E67E22; font-weight: 600; font-size: 16px;">SPEED: Response Time</h4>'
                            f'<p style="margin: 0.5rem 0; color: #ffffff; font-size: 24px; font-weight: 700;">{query_time:.1f}s</p>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        # Answer length
                        st.markdown(
                            f'<div class="metric-card">'
                            f'<h4 style="margin: 0; color: #A855F7; font-weight: 600; font-size: 16px;">LENGTH: Answer Length</h4>'
                            f'<p style="margin: 0.5rem 0; color: #ffffff; font-size: 24px; font-weight: 700;">{answer_length} chars</p>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        # Sources count
                        st.markdown(
                            f'<div class="metric-card">'
                            f'<h4 style="margin: 0; color: #E67E22; font-weight: 600; font-size: 16px;">SOURCES: Sources</h4>'
                            f'<p style="margin: 0.5rem 0; color: #ffffff; font-size: 24px; font-weight: 700;">{citation_count}</p>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    # Performance feedback
                    if query_time < 2.0:
                        st.success(
                            f"EXCELLENT: Excellent performance! ({query_time:.1f}s)"
                        )
                    elif query_time < 5.0:
                        st.info(f"GOOD: Good performance ({query_time:.1f}s)")
                    else:
                        st.warning(
                            f"SLOW: Response took {query_time:.1f}s - consider optimizing"
                        )

                else:
                    st.error(
                        "No answer generated. Please try rephrasing your question."
                    )

            except Exception as e:
                progress_placeholder.empty()
                st.error(f"ERROR: **Error generating answer:** {str(e)}")

                # Troubleshooting tips
                st.markdown(
                    '<h4 style="margin: 0; color: #f56565;">TROUBLESHOOT: Troubleshooting Tips:</h4>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    """
                    - Make sure the FAISS index exists (run `python bench_embedding.py`)
                    - Check that the Phi-3 model is downloaded in `ai_models/`
                    - Try rephrasing your question
                    - Ensure your documents are in the `extracts/` folder
                    """
                )

    # Handle empty question submission
    elif ask_button:
        st.warning("WARNING: Please enter a question first!")

    # Footer
    st.markdown(
        "<div style='text-align: center; margin-top: 3rem; padding: 2rem; color: #888;'>"
        "<span>AI: Powered by <strong>Phi-3</strong></span>"
        " | "
        "<span>KNOWLEDGE: Local Knowledge Base</span>"
        " | "
        "<span>SPEED: No Cloud Dependencies</span>"
        "<br><br>"
        "Built with love using Streamlit & Modern AI"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
