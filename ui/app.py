"""🎨 ui/app.py
Purpose: Streamlit UI for AI File Search with ask & cite functionality
Features: Question input, AI answers, citations, performance stats, dark/light mode
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
    """Format citations for display in Streamlit"""
    if not citations:
        return "No citations available."

    formatted = []
    for cite in citations:
        formatted.append(
            f"**[{cite['id']}]** {cite['file']}, page {cite['page']}\n"
            f"*Relevance: {cite.get('score', 0):.3f}*\n"
            f"```\n{cite['chunk']}\n```"
        )
    return "\n\n".join(formatted)


def main():
    """Main Streamlit application"""

    # Page configuration
    st.set_page_config(
        page_title="🔍 AI File Search",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for better styling
    st.markdown(
        """
    <style>
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 10px;
    }
    .citation-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
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

    # Sidebar - Performance Stats & Controls
    with st.sidebar:
        st.header("⚙️ Performance Stats")

        # Theme toggle (built-in to Streamlit)
        st.subheader("🎨 Appearance")
        st.info("Use the ⋮ menu → Settings to toggle dark/light mode")

        # Performance metrics
        st.subheader("📊 System Status")

        # Show recent performance if available
        if st.session_state.performance_stats:
            recent_stats = st.session_state.performance_stats[-1]
            st.metric("Last Query Time", f"{recent_stats['time']:.1f}s")
            st.metric("Answer Length", f"{recent_stats['chars']} chars")
            st.metric("Citations", f"{recent_stats['citations']}")

            # Average performance
            if len(st.session_state.performance_stats) > 1:
                avg_time = sum(
                    s["time"] for s in st.session_state.performance_stats
                ) / len(st.session_state.performance_stats)
                st.metric("Average Time", f"{avg_time:.1f}s")
        else:
            st.info("No queries yet")

        # System info
        st.subheader("🤖 AI Model")
        st.text("Phi-3-mini-4k-instruct")
        st.text("Local inference (CPU)")

        st.subheader("📚 Document Count")
        st.text("20+ indexed documents")

        # Query history
        st.subheader("📝 Recent Queries")
        if st.session_state.query_history:
            for i, query in enumerate(reversed(st.session_state.query_history[-5:])):
                st.text(f"{i+1}. {query[:30]}...")
        else:
            st.text("No queries yet")

    # Main content area
    st.title("🔍 AI File Search")

    # Welcome section
    welcome_text = load_welcome_text()
    with st.expander("ℹ️ About this system", expanded=False):
        st.markdown(welcome_text)

    # Query input section
    st.header("❓ Ask a Question")

    # Question input with Enter key support
    col1, col2 = st.columns([4, 1])

    with col1:
        question = st.text_input(
            "Enter your question:",
            placeholder="e.g., Who is Alice? What is Wonderland like?",
            help="Ask any question about the documents in your collection (Press Enter to submit)",
            key="question_input",
        )

    with col2:
        # Add some spacing to align the button with the input field
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        ask_button = st.button("🔍 Ask", type="primary", use_container_width=True)

    # Check if Enter was pressed (question changed) or button clicked
    question_submitted = False

    # Check if question was submitted via Enter key
    if question and question.strip():
        # Check if this is a new question (Enter was pressed)
        if "last_question" not in st.session_state:
            st.session_state.last_question = ""

        if question != st.session_state.last_question and question.strip():
            question_submitted = True
            st.session_state.last_question = question

    # Or if Ask button was clicked
    if ask_button and question.strip():
        question_submitted = True
        st.session_state.last_question = question

    # Process query when submitted
    if question_submitted:
        # Add question to history
        st.session_state.query_history.append(question)

        # Show progress
        with st.spinner(f"🤖 Generating AI answer for: '{question[:50]}...'"):
            start_time = time.time()

            try:
                # Call our core AI function
                answer, citations = answer_question(question)

                end_time = time.time()
                query_time = end_time - start_time

                # Store performance stats
                stats = {
                    "time": query_time,
                    "chars": len(answer),
                    "citations": len(citations),
                    "question": question,
                }
                st.session_state.performance_stats.append(stats)

                # Display results
                st.header("🤖 AI Answer")

                # Performance indicator
                perf_col1, perf_col2, perf_col3 = st.columns(3)
                with perf_col1:
                    st.metric("Response Time", f"{query_time:.1f}s")
                with perf_col2:
                    st.metric("Answer Length", f"{len(answer)} chars")
                with perf_col3:
                    st.metric("Sources Found", len(citations))

                # Answer content
                st.markdown("### Answer:")
                st.markdown(answer)

                # Citations section
                if citations:
                    st.header("📚 Sources & Citations")

                    with st.expander(
                        f"📖 View {len(citations)} source(s)", expanded=True
                    ):
                        formatted_citations = format_citations(citations)
                        st.markdown(formatted_citations)

                # Performance feedback
                if query_time < 30:
                    st.success(f"⚡ Excellent performance! ({query_time:.1f}s)")
                elif query_time < 60:
                    st.info(f"✅ Good performance ({query_time:.1f}s)")
                else:
                    st.warning(f"⏰ Slower than expected ({query_time:.1f}s)")

            except Exception as e:
                st.error(f"❌ Error generating answer: {str(e)}")
                logger.error(f"UI error: {e}")

    elif (ask_button or question_submitted) and not question.strip():
        st.warning("⚠️ Please enter a question first!")

    # Sample questions section
    st.header("💡 Try These Sample Questions")
    sample_questions = [
        "Who is Alice?",
        "What is Wonderland like?",
        "Who is Ebenezer Scrooge?",
        "What happens in the secret garden?",
        "Who is Peter Pan?",
    ]

    cols = st.columns(len(sample_questions))
    for i, sample_q in enumerate(sample_questions):
        with cols[i]:
            if st.button(sample_q, key=f"sample_{i}"):
                # Store the selected question in a temporary session state
                st.session_state.selected_sample_question = sample_q
                st.rerun()

    # Handle sample question selection
    if hasattr(st.session_state, "selected_sample_question"):
        # Use the selected sample question as the current question
        sample_question = st.session_state.selected_sample_question
        # Clear the temporary state
        delattr(st.session_state, "selected_sample_question")

        # Process the sample question immediately
        if sample_question.strip():
            # Add question to history
            st.session_state.query_history.append(sample_question)

            # Show progress
            with st.spinner(
                f"🤖 Generating AI answer for: '{sample_question[:50]}...'"
            ):
                start_time = time.time()

                try:
                    # Call our core AI function
                    answer, citations = answer_question(sample_question)

                    end_time = time.time()
                    query_time = end_time - start_time

                    # Store performance stats
                    stats = {
                        "time": query_time,
                        "chars": len(answer),
                        "citations": len(citations),
                        "question": sample_question,
                    }
                    st.session_state.performance_stats.append(stats)

                    # Display results
                    st.header("🤖 AI Answer")

                    # Performance indicator
                    perf_col1, perf_col2, perf_col3 = st.columns(3)
                    with perf_col1:
                        st.metric("Response Time", f"{query_time:.1f}s")
                    with perf_col2:
                        st.metric("Answer Length", f"{len(answer)} chars")
                    with perf_col3:
                        st.metric("Sources Found", len(citations))

                    # Answer content
                    st.markdown("### Answer:")
                    st.markdown(answer)

                    # Citations section
                    if citations:
                        st.header("📚 Sources & Citations")

                        with st.expander(
                            f"📖 View {len(citations)} source(s)", expanded=True
                        ):
                            formatted_citations = format_citations(citations)
                            st.markdown(formatted_citations)

                    # Performance feedback
                    if query_time < 30:
                        st.success(f"⚡ Excellent performance! ({query_time:.1f}s)")
                    elif query_time < 60:
                        st.info(f"✅ Good performance ({query_time:.1f}s)")
                    else:
                        st.warning(f"⏰ Slower than expected ({query_time:.1f}s)")

                except Exception as e:
                    st.error(f"❌ Error generating answer: {str(e)}")
                    logger.error(f"UI error: {e}")

    # Footer
    st.markdown("---")
    st.markdown(
        "🔍 **AI File Search** | "
        "🤖 Powered by Phi-3 | "
        "📚 Local Knowledge Base | "
        "⚡ No Cloud Dependencies"
    )


if __name__ == "__main__":
    main()
