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
from ui.components import (
    format_citations,
    format_citations_streaming,
    load_welcome_text,
    render_interactive_citations,
)
from ui.styles import ANIMATION_STYLES, MAIN_STYLES


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
    st.markdown(MAIN_STYLES, unsafe_allow_html=True)
    st.markdown(ANIMATION_STYLES, unsafe_allow_html=True)

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
                    '<h4 style="margin: 0; color: #E67E22;">🤔 AI is thinking...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 2: Document search
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #E67E22;">🔍 Searching documents...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 3: Analyzing passages
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #E67E22;">📖 Analyzing passages...</h4>',
                    unsafe_allow_html=True,
                )
            time.sleep(0.5)

            # Step 4: Starting AI response
            with progress_placeholder.container():
                st.markdown(
                    '<h4 style="margin: 0; color: #A855F7;">🤖 AI is responding...</h4>',
                    unsafe_allow_html=True,
                )

        # Initialize streaming containers
        start_time = time.time()

        # Create containers for streaming content
        answer_container = st.container()
        citations_container = st.container()

        # Create placeholders for dynamic content
        with answer_container:
            st.markdown("## 🤖 AI Response")
            answer_placeholder = st.empty()

        with citations_container:
            citations_placeholder = st.empty()

        try:
            # Get streaming answer and citations
            answer_generator, citations = answer_question(
                submitted_question, streaming=True
            )

            # Initialize streaming variables
            streamed_answer = ""
            citation_numbers_found = set()

            # Clear progress and start streaming
            progress_placeholder.empty()

            # Stream the answer
            for token in answer_generator:
                streamed_answer += token

                # Find citation numbers in the current text

                current_citations = set(re.findall(r"\[(\d+)\]", streamed_answer))
                new_citations = current_citations - citation_numbers_found
                citation_numbers_found = current_citations

                # Update the answer display with streaming effect
                with answer_placeholder.container():
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
                        f'<div style="color: #A855F7; font-weight: 600; font-size: 18px; margin-bottom: 1rem;">🤖 AI RESPONSE</div>'
                        f'<div style="margin-top: 0.5rem; line-height: 1.8; font-size: 16px;">{streamed_answer}<span style="animation: blink 1s infinite;">|</span></div>'
                        f"</div>"
                        f'<div style="'
                        f"position: absolute; "
                        f"top: 0; "
                        f"left: 0; "
                        f"width: 4px; "
                        f"height: 100%; "
                        f"background: linear-gradient(180deg, #A855F7 0%, #E67E22 100%);"
                        f'"></div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Update citations as they're referenced
                if citations and citation_numbers_found:
                    formatted_citations = format_citations_streaming(
                        citations, citation_numbers_found, new_citations
                    )
                    with citations_placeholder.container():
                        st.markdown("## 📚 Sources")
                        st.markdown(formatted_citations, unsafe_allow_html=True)

                # Small delay for smooth streaming effect
                time.sleep(0.03)

            # Remove blinking cursor and finalize
            final_answer = streamed_answer
            with answer_placeholder.container():
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
                    f'<div style="color: #A855F7; font-weight: 600; font-size: 18px; margin-bottom: 1rem;">🤖 AI RESPONSE</div>'
                    f'<div style="margin-top: 0.5rem; line-height: 1.8; font-size: 16px;">{final_answer}</div>'
                    f"</div>"
                    f'<div style="'
                    f"position: absolute; "
                    f"top: 0; "
                    f"left: 0; "
                    f"width: 4px; "
                    f"height: 100%; "
                    f"background: linear-gradient(180deg, #A855F7 0%, #E67E22 100%);"
                    f'"></div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # SWITCH TO INTERACTIVE MODE
            citations_placeholder.empty()
            with citations_container:
                render_interactive_citations(citations)

            # Calculate final metrics
            query_time = time.time() - start_time
            answer_length = len(final_answer) if final_answer else 0
            citation_count = len(citations) if citations else 0

            # Store performance metrics
            st.session_state.performance_history["query_times"].append(query_time)
            st.session_state.performance_history["answer_lengths"].append(answer_length)
            st.session_state.performance_history["citation_counts"].append(
                citation_count
            )

            # Keep only last 20 entries
            for key in st.session_state.performance_history:
                if len(st.session_state.performance_history[key]) > 20:
                    st.session_state.performance_history[key] = (
                        st.session_state.performance_history[key][-20:]
                    )

            # Show final success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏱️ Response Time", f"{query_time:.1f}s")
            with col2:
                st.metric("📝 Answer Length", f"{answer_length} chars")
            with col3:
                st.metric("📚 Sources Found", citation_count)

            # Final success message
            st.success(
                f"✅ **Streaming response completed!** ({query_time:.1f}s with {len(citations)} sources)"
            )

        except Exception as e:
            logger.error(f"ERROR: Streaming failed: {e}")

            # Fallback to non-streaming
            progress_placeholder.empty()
            with progress_container:
                st.warning("Streaming failed, falling back to standard response...")

            # Use existing non-streaming approach
            with st.spinner(f"Generating answer for: '{submitted_question[:50]}...'"):
                try:
                    answer, citations = answer_question(
                        submitted_question, streaming=False
                    )

                    if answer and answer.strip():
                        # Show non-streaming result
                        st.markdown("## 🤖 AI Answer")
                        st.markdown(
                            f'<div class="ai-answer-card" style="'
                            f"background: linear-gradient(135deg, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.3) 100%); "
                            f"backdrop-filter: blur(20px); "
                            f"color: #ffffff; "
                            f"padding: 2rem; "
                            f"border-radius: 16px; "
                            f"margin: 1.5rem 0; "
                            f"border: 1px solid rgba(255, 255, 255, 0.15); "
                            f"box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);"
                            f'">'
                            f'<div style="color: #A855F7; font-weight: 600; font-size: 18px; margin-bottom: 1rem;">🤖 AI RESPONSE</div>'
                            f'<div style="margin-top: 0.5rem; line-height: 1.8; font-size: 16px;">{answer}</div>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        # Show citations
                        if citations:
                            render_interactive_citations(citations)

                        st.success("✅ Response generated successfully (fallback mode)")
                    else:
                        st.error("❌ Unable to generate response. Please try again.")

                except Exception as fallback_error:
                    logger.error(f"ERROR: Fallback also failed: {fallback_error}")
                    st.error(
                        "❌ Unable to generate response. Please check your configuration and try again."
                    )


if __name__ == "__main__":
    main()
