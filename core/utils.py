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
    Groups citations by file to avoid duplicates.

    Args:
        citations: List of citation dictionaries
        as_html: If True, returns HTML with 'Open' buttons. If False, returns plain text.
    """
    if not citations:
        return "No citations available."

    # Group citations by file path
    grouped_citations: Dict[str, List[Dict[str, Any]]] = {}
    for cite in citations:
        file_path = cite.get("file", "Unknown File")
        if file_path not in grouped_citations:
            grouped_citations[file_path] = []
        grouped_citations[file_path].append(cite)

    formatted_output = []

    for file_path, cites in grouped_citations.items():
        # Get all IDs for this file
        ids = sorted([c["id"] for c in cites])
        id_str = ", ".join(map(str, ids))

        # Clean up the file path for better display
        filename = os.path.basename(file_path)
        file_display = file_path.replace("\\", "/")

        # Collect all content chunks
        all_bullet_points = []

        for cite in cites:
            content = cite.get("chunk", "")

            # Clean up content artifacts (e.g., excessive asterisks or dashes)
            # Remove lines that are mostly separator characters
            lines = content.split("\n")
            cleaned_lines = []
            for line in lines:
                # Skip lines that are mostly non-alphanumeric (separators)
                if (
                    len(line.strip()) > 3
                    and len(re.findall(r"[\w\s]", line)) < len(line) * 0.5
                ):
                    continue
                cleaned_lines.append(line)
            content = "\n".join(cleaned_lines)

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

            all_bullet_points.extend(bullet_points)

        # Remove duplicate bullet points (if chunks overlap)
        unique_bullets = []
        seen_bullets = set()
        for bp in all_bullet_points:
            if bp not in seen_bullets:
                unique_bullets.append(bp)
                seen_bullets.add(bp)

        if as_html:
            # Convert to HTML
            bullets_html = "".join(
                [
                    f'<div style="margin-bottom: 4px;">{bp}</div>'
                    for bp in unique_bullets
                ]
            )

            # Escape file path for HTML attribute
            safe_file_path = html.escape(file_path)
            safe_filename = html.escape(filename)

            formatted_output.append(
                f"""
                <div style="margin-bottom: 16px; padding: 12px; background-color: #2a2a2a; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;" title="{safe_file_path}">
                        <div style="font-weight: 600; color: #4CAF50; font-size: 0.9em;">
                            SOURCE {id_str}: {safe_filename}
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
            bullets_text = "\n".join([f"  {bp}" for bp in unique_bullets])
            formatted_output.append(
                f"SOURCE {id_str}: {file_display}\n{bullets_text}\n"
            )

    return "".join(formatted_output) if as_html else "\n".join(formatted_output)
