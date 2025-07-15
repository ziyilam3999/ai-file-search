"""⚙️  ask.py
Purpose : Given a user question, find best answer chunk(s) and cite source files.
Inputs  : user query (str)
Outputs : answer (str), citations (list)
Uses    : prompts/retrieval_prompt.md, all-MiniLM-L6-v2 embeddings, Phi-3 LLM
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from .embedding import Embedder
from .llm import get_phi3_llm


def answer_question(
    query: str, top_k: int = 1  # FINAL PUSH: Reduced from 2 to 1 for speed
) -> Tuple[str, List[Dict[str, Any]]]:
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

    # 4. Build the full prompt for Phi-3
    full_prompt = prompt_template.format(question=query, context=context_text)
    logger.debug("📝 Prompt length: %d characters", len(full_prompt))

    # 5. Generate answer using Phi-3
    try:
        answer = _generate_answer_with_phi3(full_prompt, citations)
        logger.success(f"✅ Generated answer ({len(answer)} chars)")
        return answer, citations

    except Exception as e:
        logger.error(f"❌ Phi-3 generation failed: {e}")
        logger.info("🔄 Falling back to context-based answer")
        fallback_answer = _generate_fallback_answer(query, results, citations)
        return fallback_answer, citations


def _generate_answer_with_phi3(prompt: str, citations: List[Dict]) -> str:
    """
    Generate an answer using Phi-3 LLM with proper citations.

    Args:
        prompt: The formatted prompt with question and context
        citations: List of citation dictionaries for reference

    Returns:
        AI-generated answer with citations
    """
    try:
        # Get Phi-3 instance
        llm = get_phi3_llm()

        # Generate answer using Phi-3
        raw_answer = llm.generate_answer(
            prompt=prompt,
            max_tokens=150,  # FINAL PUSH: Reduced from 200 for target speed
            temperature=0.35,  # FINAL PUSH: Increased from 0.3 for faster generation
            stop_sequences=["<|im_end|>", "\n\nQuestion:", "\n\nContext:"],
        )

        # Clean up the answer and ensure citations are properly formatted
        answer = raw_answer.strip()

        # Add citations section if not already present
        if "Citations:" not in answer and citations:
            citations_text = "\n\nCitations:"
            for citation in citations:
                citations_text += "\n[{}] {}, page {}".format(
                    citation["id"], citation["file"], citation["page"]
                )
            answer += citations_text

        return answer

    except Exception as e:
        logger.error(f"❌ Phi-3 generation error: {e}")
        # Fall back to context-based answer if Phi-3 fails
        return _generate_context_based_answer(citations)


def _generate_context_based_answer(citations: List[Dict]) -> str:
    """
    Generate a simple answer based on context when Phi-3 is unavailable.
    """
    if not citations:
        return "I couldn't find relevant information to answer your question."

    # Use the best chunk as the basis for the answer
    best_citation = citations[0]
    answer = f"Based on the available information: " f"{best_citation['chunk'][:300]}"

    if len(best_citation["chunk"]) > 300:
        answer += "..."

    # Add citation reference
    answer += f" [1]"

    # Add citations section
    citations_text = "\n\nCitations:"
    for citation in citations:
        citations_text += (
            f"\n[{citation['id']}] {citation['file']}, page {citation['page']}"
        )

    answer += citations_text
    answer += "\n\n(Note: Generated using context extraction - Phi-3 unavailable)"

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
