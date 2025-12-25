"""Compatibility UI helpers.

The current UI is Flask/HTML based. Some tests still expect the older Streamlit
helper module `ui.components`.

This module provides a minimal, test-focused implementation that:
- loads the welcome text
- formats citations (static + streaming)
- renders interactive citation cards via Streamlit APIs (mocked in tests)

It is intentionally lightweight and does not affect the Flask UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from core.utils import open_local_file


def load_welcome_text() -> str:
    """Load UI welcome markdown text."""
    candidates = [
        Path("prompts/ui_welcome.md"),
        Path(__file__).parent.parent / "prompts" / "ui_welcome.md",
    ]
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            continue
    return "# Welcome"


def format_citations(citations: List[Dict[str, Any]]) -> str:
    """Format citations in a simple, readable text block."""
    if not citations:
        return ""

    parts: List[str] = []
    for c in citations:
        cid = c.get("id", "?")
        file = c.get("file", "")
        page = c.get("page", "?")
        chunk = c.get("chunk", "")
        score = c.get("score")
        header = f"SOURCE {cid}: {file} (page {page})"
        if score is not None:
            try:
                header += f" (score: {float(score):.3f})"
            except Exception:
                pass
        parts.append(header)
        if chunk:
            parts.append(str(chunk))
        parts.append("")

    return "\n".join(parts).strip()


def format_citations_streaming(
    citations: List[Dict[str, Any]], found_ids: Set[int], new_ids: Set[int]
) -> str:
    """Format citations as HTML for streaming UI.

    Tests expect new citations to include `animation: pulse` styling.
    """
    if not citations:
        return ""

    cards: List[str] = []
    for c in citations:
        cid = int(c.get("id", 0) or 0)
        if cid not in found_ids:
            continue

        file = c.get("file", "")
        page = c.get("page", "?")
        chunk = c.get("chunk", "")

        style = ""
        if cid in new_ids:
            style = "animation: pulse 1s ease-in-out 2;"

        cards.append(
            (
                f"<div class='citation-card' style='{style}'>"
                f"<div><strong>{file}</strong> (page {page})</div>"
                f"<div>{chunk}</div>"
                f"</div>"
            )
        )

    return "\n".join(cards)


def render_interactive_citations(citations: List[Dict[str, Any]]) -> None:
    """Render citations using Streamlit primitives.

    Streamlit is mocked in the unit tests.
    """
    import streamlit as st  # type: ignore

    if not citations:
        st.markdown("No citations")
        return

    st.markdown("### Citations")

    for c in citations:
        file = c.get("file", "")
        page = c.get("page", "?")
        chunk = c.get("chunk", "")

        st.markdown(f"**{file}** (page {page})")
        st.markdown(chunk)

        cols = st.columns([5, 1])
        with cols[1]:
            if st.button("Open"):
                open_local_file(str(file))
