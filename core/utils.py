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
    Also handles confluence:// URLs by opening in browser.
    """
    import webbrowser

    try:
        # Handle Confluence URLs
        if file_path.startswith("confluence://"):
            from core.confluence import get_confluence_url_for_path

            confluence_url = get_confluence_url_for_path(file_path)
            if confluence_url:
                webbrowser.open(confluence_url)
                logger.info(f"Opened Confluence page in browser: {confluence_url}")
            else:
                logger.error(f"Could not resolve Confluence URL for: {file_path}")
            return

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


def format_citations(
    citations: List[Dict[str, Any]] | None, as_html: bool = True
) -> str:
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

    # Assign deterministic fallback IDs when missing.
    # Some tests provide citations without an "id" field.
    normalized: List[Dict[str, Any]] = []
    next_id = 1
    for cite in citations:
        if "id" not in cite:
            normalized.append({**cite, "id": next_id})
            next_id += 1
        else:
            normalized.append(cite)

    # Group citations by file path
    grouped_citations: Dict[str, List[Dict[str, Any]]] = {}
    for cite in normalized:
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

        # Collect all content chunks (as bullet items when appropriate)
        all_items: List[str] = []

        for cite in cites:
            content = cite.get("chunk", "")

            # Clean up content artifacts (e.g., excessive asterisks or dashes)
            # Remove lines that are mostly separator characters
            lines = content.split("\n")
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty lines or lines that are mostly non-alphanumeric (separators)
                if not line:
                    continue
                if len(line) > 3 and len(re.findall(r"[\w\s]", line)) < len(line) * 0.5:
                    continue
                cleaned_lines.append(line)

            if not cleaned_lines:
                continue

            paragraph = " ".join(cleaned_lines)
            paragraph = re.sub(r"\s+", " ", paragraph).strip()
            if not paragraph:
                continue

            # Bullet rendering rules expected by tests:
            # - sentence splitting: "A. B. C." -> bullets
            # - dash splitting: "A - B - C" -> bullets
            bullet_items: List[str] = []
            if " - " in paragraph and paragraph.count(" - ") >= 1:
                bullet_items = [p.strip() for p in paragraph.split(" - ") if p.strip()]
            else:
                parts = [
                    p.strip()
                    for p in re.split(r"(?<=[.!?])\s+", paragraph)
                    if p.strip()
                ]
                if len(parts) >= 2:
                    bullet_items = parts

            if bullet_items:
                for item in bullet_items:
                    all_items.append(f"• {item}")
            else:
                # Truncate if too long (max 300 chars for preview)
                if len(paragraph) > 300:
                    paragraph = paragraph[:300] + "..."
                all_items.append(paragraph)

        # Remove duplicate items (if chunks overlap)
        unique_items: List[str] = []
        seen_items: set[str] = set()
        for item in all_items:
            if item not in seen_items:
                unique_items.append(item)
                seen_items.add(item)

        if as_html:
            # Convert to HTML with collapsible details
            paragraphs_html = "".join(
                [
                    f'<p style="margin: 8px 0; line-height: 1.6;">{html.escape(item)}</p>'
                    for item in unique_items
                ]
            )

            # Escape normalized file path for HTML attributes
            # Tests expect backslashes to be converted to forward slashes.
            safe_file_path = html.escape(file_display)
            safe_filename = html.escape(filename)

            formatted_output.append(
                f"""
                <div style="margin-bottom: 12px; padding: 10px; background-color: #2a2a2a; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <div style="display: flex; justify-content: space-between; align-items: center;" title="{safe_file_path}">
                        <div style="font-weight: 600; color: #4CAF50; font-size: 0.9em;">
                            [{id_str}] {safe_filename}
                        </div>
                        <button class="open-file-btn" data-file-path="{safe_file_path}" style="background-color: #4CAF50; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.8em;">
                            📂 Open
                        </button>
                    </div>
                    <details style="margin-top: 8px;">
                        <summary style="cursor: pointer; color: #aaa; font-size: 0.85em;">Show context</summary>
                        <div style="color: #e0e0e0; font-size: 0.9em; margin-top: 8px; padding-left: 8px; border-left: 2px solid #444;">
                            {paragraphs_html}
                        </div>
                    </details>
                </div>
                """
            )
        else:
            # Plain text formatting
            paragraphs_text = "\n".join([f"  {item}" for item in unique_items])
            formatted_output.append(
                f"SOURCE {id_str}: {file_display}\n{paragraphs_text}\n"
            )

    return "".join(formatted_output) if as_html else "\n".join(formatted_output)
