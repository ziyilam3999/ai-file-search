"""⚙️  ask.py
Purpose : Given a user question, find best answer chunk(s) and cite source files.
Inputs  : user query (str)
Outputs : answer (str), citations (list)
Uses    : prompts/retrieval_prompt.md, all-MiniLM-L6-v2 embeddings
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from .embedding import Embedder


def answer_question(query: str, top_k: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Answer a question using RAG with numbered citations and page numbers.

    Args:
        query: User's question
        top_k: Number of top chunks to retrieve for context

    Returns:
        Tuple of (answer_text, citations)
        where citations is [{"id": int, "file": str, "page": int, "chunk": str}]
    """
    logger.info(f"🤔 Answering question: '{query}'")

    # 1. Embed the question and find top chunks
    embedder = Embedder()
    results = embedder.query(query, k=top_k)

    if not results:
        return (
            "I couldn't find any relevant information to answer your question.",
            [],
        )

    logger.info(f"📚 Found {len(results)} relevant chunks")

    # 2. Load prompt template
    prompt_path = Path(__file__).parent.parent / "prompts" / "retrieval_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        logger.error(f"❌ Prompt template not found: {prompt_path}")
        return "Error: Prompt template not found.", []

    # 3. Format context from chunks with numbered citations
    context_chunks = []
    citations = []

    for i, (chunk_text, file_path, chunk_id, score) in enumerate(results, 1):
        # Estimate page number from chunk_id (assuming ~3 chunks per page)
        estimated_page = max(1, (chunk_id // 3) + 1)

        context_chunks.append(f"[{i}] {chunk_text}")
        citations.append(
            {
                "id": i,
                "file": Path(file_path).name,  # Just filename, not full path
                "page": estimated_page,
                "chunk": (
                    chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
                ),
                "chunk_id": chunk_id,
                "score": score,
            }
        )

    context_text = "\n\n".join(context_chunks)

    # 4. Build the full prompt (for future Phi-3 integration)
    full_prompt = prompt_template.format(question=query, context=context_text)
    # Note: full_prompt will be used when Phi-3 integration is added
    del full_prompt  # Temporarily suppress unused variable warning

    # 5. Generate answer (simulated for now)
    try:
        answer = _generate_answer_with_citations(query, results, citations)
        logger.success(f"✅ Generated answer ({len(answer)} chars)")
        return answer, citations

    except Exception as e:
        logger.error(f"❌ Answer generation failed: {e}")
        fallback_answer = _generate_fallback_answer(query, results, citations)
        return fallback_answer, citations


def _generate_answer_with_citations(
    query: str, results: List, citations: List[Dict]
) -> str:
    """
    Generate an answer with proper numbered citations and page references.
    This is a simulation - replace with actual Phi-3 model integration.
    """
    # Extract key information from the best chunks
    if not results:
        return "I couldn't find relevant information to answer your question."

    # Simple answer generation based on available chunks
    answer_parts = []

    # Always try to provide some answer based on the retrieved chunks
    if len(results) >= 1:
        best_chunk = results[0][0]
        if best_chunk and len(best_chunk.strip()) > 20:
            answer_parts.append(
                f"Based on the available information, " f"{best_chunk[:200]}... [1]"
            )

        if len(results) >= 2:
            second_chunk = results[1][0]
            if second_chunk and len(second_chunk.strip()) > 20:
                answer_parts.append(f"Additionally, {second_chunk[:150]}... [2]")

    # If no good chunks found, provide a generic response
    if not answer_parts:
        answer_parts.append(
            "I found some relevant passages but they may not directly "
            "answer your question. Please check the citations below "
            "for more context."
        )

    # Add citations section
    citations_text = "\n\nCitations:"
    for citation in citations:
        citations_text += (
            f"\n[{citation['id']}] {citation['file']}, " f"page {citation['page']}"
        )

    answer = " ".join(answer_parts) + citations_text

    # Add note about simulation
    answer += (
        "\n\n(Note: This is a simulated response. "
        "Integrate Phi-3 model for actual AI-generated answers.)"
    )

    return answer


def _generate_fallback_answer(query: str, results: List, citations: List[Dict]) -> str:
    """
    Generate a simple fallback answer when main generation fails.
    """
    if not results:
        return "I couldn't find relevant information to answer your question."

    best_chunk, best_file, _, best_score = results[0]
    best_citation = citations[0]

    answer = (
        f"I found relevant information about your question: "
        f"{best_chunk[:300]}... [1]"
    )
    answer += (
        f"\n\nCitations:\n[1] {best_citation['file']}, " f"page {best_citation['page']}"
    )

    return answer


# TODO(copilot): Replace _generate_answer_with_citations() with actual
# Phi-3 model integration
