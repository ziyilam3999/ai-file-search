"""Compatibility Streamlit-style UI entrypoint.

The current UI is Flask/HTML based, but some tests still expect an older
Streamlit module layout providing `ui.app` with `main`, `load_welcome_text`,
and `format_citations`.

This module is intentionally lightweight and does not affect the Flask UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def load_welcome_text() -> str:
    candidates = [
        Path("prompts/ui_welcome.md"),
        Path(__file__).parent.parent / "prompts" / "ui_welcome.md",
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                if text.strip():
                    return text
        except FileNotFoundError:
            continue
    return "# AI File Search"


def format_citations(citations: List[Dict[str, Any]] | None) -> str:
    if not citations:
        return "No citations available."

    parts: List[str] = []
    for cite in citations:
        cid = cite.get("id", "?")
        file = cite.get("file", "")
        page = cite.get("page", "?")
        chunk = cite.get("chunk", "")
        score = cite.get("score")

        header = f"<div><strong>SOURCE {cid}</strong></div>"
        meta = (
            f"<div><strong>File:</strong> {file}</div>"
            f"<div><strong>Page:</strong> {page}</div>"
        )
        if score is not None:
            meta += f"<div><strong>Score:</strong> {score}</div>"

        body = f"<div>{chunk}</div>" if chunk else ""
        parts.append("<div class='citation'>" + header + meta + body + "</div>")

    return "\n".join(parts)


def main() -> None:
    # Placeholder for legacy Streamlit entrypoint.
    return
