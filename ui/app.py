"""🎨 ui/app.py
Purpose: Streamlit UI for AI File Search with ask & cite functionality
Features: Question input, AI answers, citations, performance stats, modern design
Usage: streamlit run ui/app.py
"""

# Import our core functionality
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
        return "# 🔍 AI File Search\nWelcome to your local AI-powered document search!"


def format_citations(citations):
    """Format citations for display with enhanced orange-purple glass morphism"""
    if not citations:
        return "No citations available."

    formatted = []
    for i, cite in enumerate(citations):
        formatted.append(
            f'<div class="citation-card" style="background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); color: #ffffff; padding: 1.5rem; border-radius: 20px; margin: 1rem 0; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); min-height: 80px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">'
            f'<h4 style="margin: 0; color: #ffffff; font-weight: 600;">📄 Source {i+1}</h4>'
            f'<span style="background: rgba(230, 126, 34, 0.3); color: #ffffff; padding: 6px 12px; border-radius: 16px; font-size: 12px; font-weight: 500;">Relevance: {cite.get("score", 0):.3f}</span>'
            f"</div>"
            f'<p style="margin: 0.8rem 0; color: #e0e0e0; font-weight: 500; font-size: 16px;">{cite["file"]}, page {cite["page"]}</p>'
            f'<div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 12px; margin-top: 1rem;">'
            f'<code style="color: #ffffff; font-size: 14px; line-height: 1.6; font-family: \'Inter\', monospace;">{cite["chunk"]}</code>'
            f"</div>"
            f"</div>"
        )
    return "\n\n".join(formatted)


def print_search_results(results):
    for result in results:
        print(f"Found in: {result['path']}")
        print(result["chunk"])
        print("-" * 40)


def main():
    """Main Streamlit application"""

    # Page configuration
    st.set_page_config(
        page_title="🔍 AI File Search",
        page_icon="🔍",
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

    /* Consistent metric cards with darker glass */
    .metric-card {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        text-align: center;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Sidebar with professional orange gradient */
    .css-1d391kg {
        background: linear-gradient(180deg, #E67E22 0%, #A855F7 100%);
    }

    /* Header styling with professional orange gradient */
    .main-header {
        background: linear-gradient(135deg, #E67E22 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3.5rem;
    }

    /* Answer section with consistent darker glass styling */
    .answer-container {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        line-height: 1.7;
        font-size: 16px;
        color: #ffffff;
    }

    /* Enhanced sidebar cards with darker glass */
    .sidebar-card {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Success/info messages with professional orange theme */
    .stSuccess {
        background-color: rgba(230, 126, 34, 0.1) !important;
        border: 1px solid rgba(230, 126, 34, 0.3) !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stInfo {
        background-color: rgba(168, 85, 247, 0.1) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stWarning {
        background-color: rgba(245, 101, 101, 0.1) !important;
        border: 1px solid rgba(245, 101, 101, 0.3) !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Enhanced footer with darker glass effect */
    .footer-text {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        text-align: center;
        color: #6b7280;
        font-family: 'Inter', sans-serif;
        margin-top: 3rem;
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Spinner with professional orange theme */
    .stSpinner > div {
        border-top-color: #E67E22 !important;
    }

    /* Enhanced expander styling with darker glass */
    .streamlit-expanderHeader {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        border-radius: 16px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    /* Section spacing improvements */
    .section-spacing {
        margin: 2rem 0;
    }

    /* Streamlit metrics override for consistency with darker glass */
    [data-testid="metric-container"] {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin: 0.5rem 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "performance_stats" not in st.session_state:
        st.session_state.performance_stats = []

    # Enhanced sidebar with compact layout
    with st.sidebar:
        st.markdown("### ⚙️ Performance Dashboard")

        # Theme toggle with enhanced styling
        st.markdown("#### 🎨 Appearance")
        st.markdown(
            '<div class="sidebar-card">'
            "<small>💡 Use the ⋮ menu → Settings to toggle dark/light mode</small></div>",
            unsafe_allow_html=True,
        )

        # Performance metrics with compact spacing
        st.markdown("#### 📊 System Status")

        # Show recent performance if available
        if st.session_state.performance_stats:
            recent_stats = st.session_state.performance_stats[-1]

            # Create compact metric cards
            st.markdown('<div style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "⚡ Response Time",
                    f"{recent_stats['time']:.1f}s",
                    delta=None,
                    help="Time for the most recent query",
                )
            with col2:
                st.metric(
                    "📝 Answer Length",
                    f"{recent_stats['chars']}",
                    delta=None,
                    help="Characters in the last answer",
                )

            st.metric(
                "📚 Citations Found",
                f"{recent_stats['citations']}",
                delta=None,
                help="Number of source citations",
            )

            # Average performance with compact styling
            if len(st.session_state.performance_stats) > 1:
                avg_time = sum(
                    s["time"] for s in st.session_state.performance_stats
                ) / len(st.session_state.performance_stats)
                st.metric(
                    "📈 Average Time",
                    f"{avg_time:.1f}s",
                    delta=f"{recent_stats['time'] - avg_time:+.1f}s",
                    help="Average response time across all queries",
                )
        else:
            st.markdown(
                '<div class="sidebar-card" style="text-align: center;">'
                "<p><strong>🎯 Ready to answer your questions!</strong></p>"
                "<small>No queries yet - ask your first question to see performance metrics</small></div>",
                unsafe_allow_html=True,
            )

        # Compact system info cards
        st.markdown('<div style="margin: 2rem 0;"></div>', unsafe_allow_html=True)

        st.markdown("#### 🤖 AI Model")
        st.markdown(
            '<div class="sidebar-card">'
            "<strong>Phi-3-mini-4k-instruct</strong><br>"
            "<small>Local inference (CPU optimized)</small></div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### 📚 Knowledge Base")
        st.markdown(
            '<div class="sidebar-card">'
            "<strong>Dynamic Document Collection</strong><br>"
            "<small>Based on your uploaded documents</small></div>",
            unsafe_allow_html=True,
        )

        # Compact query history
        st.markdown("#### 📝 Recent Queries")
        if st.session_state.query_history:
            for i, query in enumerate(reversed(st.session_state.query_history[-3:])):
                st.markdown(
                    f'<div class="sidebar-card" style="margin: 0.8rem 0; padding: 0.8rem; font-size: 12px;">'
                    f'<strong>{i+1}.</strong> {query[:35]}{"..." if len(query) > 35 else ""}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="sidebar-card" style="text-align: center;">'
                "<small>No queries yet - ask your first question!</small></div>",
                unsafe_allow_html=True,
            )

    # Enhanced header with better spacing
    st.markdown(
        '<h1 class="main-header">🔍 AI File Search</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align: center; color: #6b7280; font-size: 20px; margin-bottom: 3rem; line-height: 1.6;">Your intelligent document companion powered by local AI</p>',
        unsafe_allow_html=True,
    )

    # Enhanced welcome section with glass morphism
    welcome_text = load_welcome_text()
    with st.expander("ℹ️ About this system", expanded=False):
        st.markdown(
            f'<div class="glass-card">{welcome_text}</div>',
            unsafe_allow_html=True,
        )

    # Enhanced query input section with better spacing
    st.markdown('<div class="section-spacing"></div>', unsafe_allow_html=True)
    st.markdown("### ❓ Ask Your Question")
    st.markdown(
        '<p style="color: #6b7280; margin-bottom: 1.5rem; font-size: 18px; line-height: 1.6;">Enter your question below and get AI-powered answers with source citations</p>',
        unsafe_allow_html=True,
    )

    # Enhanced question input with better UX flow
    question = st.text_input(
        "Enter your question:",
        help="Ask any question about the documents in your collection (Press Enter to submit)",
        key="question_input",
        label_visibility="collapsed",
    )

    # Ask button positioned below input for better UX flow
    ask_button = st.button(
        "🔍 Ask AI Assistant",
        type="primary",
        use_container_width=True,
        help="Submit your question to get an AI-powered answer",
    )

    # Check if Enter was pressed (question changed) or button clicked
    question_submitted = False
    submitted_question = None

    # Check if question was submitted via Enter key
    if question and question.strip():
        # Check if this is a new question (Enter was pressed)
        if "last_question" not in st.session_state:
            st.session_state.last_question = ""

        if question != st.session_state.last_question and question.strip():
            question_submitted = True
            submitted_question = question
            st.session_state.last_question = question

    # Or if Ask button was clicked
    elif ask_button and question.strip():
        question_submitted = True
        submitted_question = question
        st.session_state.last_question = question

    # Process query when submitted
    if question_submitted and submitted_question:
        # Add question to history
        st.session_state.query_history.append(submitted_question)

        # Enhanced notification system with replacing status updates
        st.markdown('<div class="section-spacing"></div>', unsafe_allow_html=True)

        # Create containers that will be replaced with each update
        main_status_container = st.empty()
        progress_container = st.empty()

        # Show immediate feedback
        with main_status_container:
            st.info(f"🚀 **Processing your question:** '{submitted_question}'")

        # Show detailed status updates that replace previous ones
        with progress_container:
            st.markdown(
                '<div style="background: rgba(230, 126, 34, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(230, 126, 34, 0.3); text-align: center;">'
                '<h4 style="margin: 0; color: #E67E22;">🤖 AI is thinking...</h4>'
                '<p style="margin: 0.5rem 0; color: #6b7280;">Please wait while we search through your documents and generate an intelligent response.</p>'
                "</div>",
                unsafe_allow_html=True,
            )

        # Progress tracking with replaceable updates
        time.sleep(0.3)
        with progress_container:
            st.markdown(
                '<div style="background: rgba(230, 126, 34, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(230, 126, 34, 0.3); text-align: center;">'
                '<h4 style="margin: 0; color: #E67E22;">🔍 Searching documents...</h4>'
                '<p style="margin: 0.5rem 0; color: #6b7280;">Analyzing document collection for relevant passages.</p>'
                "</div>",
                unsafe_allow_html=True,
            )

        time.sleep(0.3)
        with progress_container:
            st.markdown(
                '<div style="background: rgba(230, 126, 34, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(230, 126, 34, 0.3); text-align: center;">'
                '<h4 style="margin: 0; color: #E67E22;">📄 Analyzing passages...</h4>'
                '<p style="margin: 0.5rem 0; color: #6b7280;">Extracting relevant information from source documents.</p>'
                "</div>",
                unsafe_allow_html=True,
            )

        time.sleep(0.3)
        with progress_container:
            st.markdown(
                '<div style="background: rgba(168, 85, 247, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(168, 85, 247, 0.3); text-align: center;">'
                '<h4 style="margin: 0; color: #A855F7;">🧠 Generating response...</h4>'
                '<p style="margin: 0.5rem 0; color: #6b7280;">AI model is formulating your answer.</p>'
                "</div>",
                unsafe_allow_html=True,
            )

        # Show final processing status with spinner
        with st.spinner(f"🤖 Finalizing answer for: '{submitted_question[:50]}...'"):
            start_time = time.time()

            # Final status update
            with progress_container:
                st.markdown(
                    '<div style="background: rgba(168, 85, 247, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(168, 85, 247, 0.3); text-align: center;">'
                    '<h4 style="margin: 0; color: #A855F7;">✨ Almost ready...</h4>'
                    '<p style="margin: 0.5rem 0; color: #6b7280;">Finalizing your intelligent response.</p>'
                    "</div>",
                    unsafe_allow_html=True,
                )

            try:
                # Call our core AI function
                answer, citations = answer_question(submitted_question)

                end_time = time.time()
                query_time = end_time - start_time

                # Show success status
                with progress_container:
                    st.markdown(
                        '<div style="background: rgba(34, 197, 94, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(34, 197, 94, 0.3); text-align: center;">'
                        '<h4 style="margin: 0; color: #22c55e;">✅ Response generated successfully!</h4>'
                        f'<p style="margin: 0.5rem 0; color: #6b7280;">Completed in {query_time:.1f}s with {len(citations)} sources found.</p>'
                        "</div>",
                        unsafe_allow_html=True,
                    )
                time.sleep(1)

                # Clear all status containers
                main_status_container.empty()
                progress_container.empty()

                # Store performance stats
                stats = {
                    "time": query_time,
                    "chars": len(answer),
                    "citations": len(citations),
                    "question": submitted_question,
                }
                st.session_state.performance_stats.append(stats)

                # Enhanced results display with consistent spacing
                st.markdown(
                    '<div class="section-spacing"></div>', unsafe_allow_html=True
                )

                # Show success notification
                st.success(
                    f"🎉 **Answer generated successfully!** ({query_time:.1f}s with {len(citations)} sources)"
                )

                st.markdown("## 🤖 AI Answer")

                # Enhanced answer content with better typography
                st.markdown(
                    '<div style="margin: 2rem 0;"></div>', unsafe_allow_html=True
                )
                st.markdown("### 💬 Answer:")
                st.markdown(
                    f'<div class="answer-container" style="color: #ffffff; background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); border-radius: 20px; padding: 2rem; margin: 1.5rem 0; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); line-height: 1.7; font-size: 16px;">{answer}</div>',
                    unsafe_allow_html=True,
                )

                # Enhanced citations section
                if citations:
                    st.markdown(
                        '<div style="margin: 2rem 0;"></div>', unsafe_allow_html=True
                    )
                    st.markdown("## 📚 Sources & Citations")

                    with st.expander(
                        f"📖 View {len(citations)} source(s)", expanded=True
                    ):
                        formatted_citations = format_citations(citations)
                        st.markdown(formatted_citations, unsafe_allow_html=True)

                # Enhanced performance cards with consistent sizing (moved to end)
                st.markdown(
                    '<div style="margin: 2rem 0;"></div>', unsafe_allow_html=True
                )
                st.markdown("### 📊 Performance Metrics")
                perf_col1, perf_col2, perf_col3 = st.columns(3)
                with perf_col1:
                    st.markdown(
                        f'<div style="background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); text-align: center; min-height: 80px; display: flex; flex-direction: column; justify-content: center;">'
                        f'<h4 style="margin: 0; color: #E67E22; font-weight: 600; font-size: 16px;">⚡ Response Time</h4>'
                        f'<h2 style="margin: 10px 0; color: #ffffff; font-weight: 700; font-size: 32px;">{query_time:.1f}s</h2>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with perf_col2:
                    st.markdown(
                        f'<div style="background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); text-align: center; min-height: 80px; display: flex; flex-direction: column; justify-content: center;">'
                        f'<h4 style="margin: 0; color: #A855F7; font-weight: 600; font-size: 16px;">📝 Answer Length</h4>'
                        f'<h2 style="margin: 10px 0; color: #ffffff; font-weight: 700; font-size: 32px;">{len(answer)}</h2>'
                        f'<small style="color: #cccccc;">chars</small>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with perf_col3:
                    st.markdown(
                        f'<div style="background: rgba(0, 0, 0, 0.4); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); text-align: center; min-height: 80px; display: flex; flex-direction: column; justify-content: center;">'
                        f'<h4 style="margin: 0; color: #E67E22; font-weight: 600; font-size: 16px;">📚 Sources</h4>'
                        f'<h2 style="margin: 10px 0; color: #ffffff; font-weight: 700; font-size: 32px;">{len(citations)}</h2>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Performance feedback
                if query_time < 30:
                    st.success(f"⚡ Excellent performance! ({query_time:.1f}s)")
                elif query_time < 60:
                    st.info(f"✅ Good performance ({query_time:.1f}s)")
                else:
                    st.warning(f"⏰ Slower than expected ({query_time:.1f}s)")

            except Exception as e:
                # Clear status containers
                main_status_container.empty()
                progress_container.empty()

                # Show error notification with details
                st.error(f"❌ **Error generating answer:** {str(e)}")
                st.markdown(
                    '<div style="background: rgba(245, 101, 101, 0.1); backdrop-filter: blur(15px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; border: 1px solid rgba(245, 101, 101, 0.3);">'
                    '<h4 style="margin: 0; color: #f56565;">🔧 Troubleshooting Tips:</h4>'
                    '<ul style="margin: 0.5rem 0; color: #6b7280;">'
                    "<li>Try rephrasing your question</li>"
                    "<li>Make sure your question is related to the document collection</li>"
                    "<li>Check that the AI model is properly loaded</li>"
                    "</ul>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                logger.error(f"UI error: {e}")

    elif (ask_button or question_submitted) and not (
        submitted_question and submitted_question.strip()
    ):
        st.warning("⚠️ Please enter a question first!")

    # Enhanced footer with glass effect
    st.markdown(
        '<div class="footer-text">'
        '<div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap;">'
        "<span>🔍 <strong>AI File Search</strong></span>"
        "<span>|</span>"
        "<span>🤖 Powered by <strong>Phi-3</strong></span>"
        "<span>|</span>"
        "<span>📚 Local Knowledge Base</span>"
        "<span>|</span>"
        "<span>⚡ No Cloud Dependencies</span>"
        "</div>"
        '<div style="margin-top: 12px; font-size: 12px; opacity: 0.7;">'
        "Built with ❤️ using Streamlit & Modern AI"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
