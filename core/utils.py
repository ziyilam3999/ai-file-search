import html
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger


def open_local_file(file_path: str) -> None:
    """
    Open a file in the system's default viewer.
    Cross-platform support for Windows, macOS, and Linux.
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            logger.error(f"File not found: {path}")
            return

        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(("open", str(path)))
        else:  # Linux
            subprocess.call(("xdg-open", str(path)))
    except Exception as e:
        logger.error(f"Failed to open file: {e}")


def format_citations(citations: List[Dict[str, Any]], as_html: bool = True) -> str:
    """
    Format citations for display with clean, professional formatting.
    Shared between Streamlit and Flask UIs.

    Args:
        citations: List of citation dictionaries
        as_html: If True, returns HTML with 'Open' buttons. If False, returns plain text.
    """
    if not citations:
        return "No citations available."

    formatted_output = []

    for i, cite in enumerate(citations):
        # Clean up the file path for better display
        file_path = cite.get("file", "Unknown File")
        file_display = file_path.replace("\\", "/")

        # Get content
        content = cite.get("chunk", "")

        # Enhanced content splitting to preserve ALL content
        bullet_points = []

        if ". " in content and len(content.split(". ")) > 2:
            # Split by sentences
            sentences = re.split(r"(?<=\.)\s+", content)
            parts = [s.strip() for s in sentences if s.strip()]

            for part in parts:
                part = part.strip()
                if (
                    part
                    and not part.endswith(".")
                    and not part.endswith("!")
                    and not part.endswith("?")
                ):
                    part += "."
                if part:
                    bullet_points.append(f"• {part}")

        elif " - " in content and len(content.split(" - ")) > 2:
            # Split by dashes
            parts = [s.strip() for s in content.split(" - ") if s.strip()]
            for part in parts:
                part = part.strip()
                if (
                    part
                    and not part.endswith(".")
                    and not part.endswith("!")
                    and not part.endswith("?")
                ):
                    if len(part) > 20:
                        part += "."
                if part:
                    bullet_points.append(f"• {part}")

        elif "\n" in content:
            # Split by line breaks
            parts = [s.strip() for s in content.split("\n") if s.strip()]
            bullet_points = [f"• {part}" for part in parts]

        else:
            # Fallback: Split into logical chunks
            words = content.split()
            chunk_size = 20

            for j in range(0, len(words), chunk_size):
                chunk = " ".join(words[j : j + chunk_size])
                if chunk.strip():
                    bullet_points.append(f"• {chunk}")

        # If no bullet points created, use the full content
        if not bullet_points:
            bullet_points = [f"• {content}"]

        if as_html:
            # Convert to HTML
            bullets_html = "".join(
                [f'<div style="margin-bottom: 4px;">{bp}</div>' for bp in bullet_points]
            )

            # Escape file path for HTML attribute
            safe_file_path = html.escape(file_path)

            formatted_output.append(
                f"""
                <div style="margin-bottom: 16px; padding: 12px; background-color: #2a2a2a; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #4CAF50; font-size: 0.9em;">
                            SOURCE {i+1}: {file_display}
                        </div>
                        <button class="open-file-btn" data-file-path="{safe_file_path}" style="background-color: #4CAF50; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8em;">
                            📂 Open
                        </button>
                    </div>
                    <div style="color: #e0e0e0; font-size: 0.95em; line-height: 1.5;">
                        {bullets_html}
                    </div>
                </div>
                """
            )
        else:
            # Plain text formatting
            bullets_text = "\n".join([f"  {bp}" for bp in bullet_points])
            formatted_output.append(f"SOURCE {i+1}: {file_display}\n{bullets_text}\n")

    return "".join(formatted_output) if as_html else "\n".join(formatted_output)
