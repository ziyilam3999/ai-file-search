"""
UI Components: ui/components.py
Purpose: Reusable UI components and rendering logic for the Streamlit application.
"""

import re
from pathlib import Path

import streamlit as st

from core.utils import open_local_file


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


def format_citations_streaming(citations, found_numbers, new_numbers):
    """Format citations for streaming display with highlighting for new citations."""
    if not citations:
        return "No citations available."

    formatted = []
    formatted.append(
        '<div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">'
    )

    for citation in citations:
        citation_id = citation["id"]

        # Show ALL citations, not just referenced ones (for debugging)
        if True:  # Changed from: if citation_id in found_numbers:
            # This citation has been referenced
            is_new = citation_id in new_numbers
            highlight_style = (
                "background: rgba(168, 85, 247, 0.2); animation: pulse 2s;"
                if is_new
                else ""
            )

            file_display = citation["file"].replace("\\", "/")
            content = citation["chunk"]

            formatted.append(
                f"""
            <div style="margin: 1rem 0; padding: 1rem; border-left: 3px solid #A855F7; {highlight_style}">
                <div style="font-weight: 600; color: #A855F7; margin-bottom: 0.5rem;">
                    📄 [{citation_id}] {file_display}, page {citation["page"]} {"🆕" if is_new else ""}
                </div>
                <div style="color: #E5E7EB; font-size: 14px; line-height: 1.6;">
                    {content[:200]}...
                </div>
            </div>
            """
            )

    formatted.append("</div>")
    return "".join(formatted)


def render_interactive_citations(citations):
    """Render citations as interactive widgets with 'Open File' buttons."""
    if not citations:
        st.info("No citations available.")
        return

    st.markdown("## 📚 Sources")

    for i, cite in enumerate(citations):
        # Clean path for display
        file_display = cite["file"].replace("\\", "/")

        # Layout: Text on left (5/6), Button on right (1/6)
        col1, col2 = st.columns([5, 1])

        with col1:
            # Render the content card using the existing CSS class
            st.markdown(
                f"""
                <div class="citation-card" style="margin: 0;">
                    <div style="color: #E67E22; font-weight: 600; font-size: 16px;">SOURCE {cite['id']}</div>
                    <div style="margin: 0.5rem 0;">
                        <strong>File:</strong> <code style="background: rgba(255,255,255,0.1);">{file_display}</code>
                    </div>
                    <div style="font-size: 14px; color: #E5E7EB;">
                        {cite['chunk'][:300]}...
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            # Vertically center the button relative to the card
            st.write("")
            st.write("")
            if st.button("📂 Open", key=f"btn_open_{i}", help=f"Open {file_display}"):
                open_local_file(cite["file"])

        # Add some spacing between rows
        st.write("")
