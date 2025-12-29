"""CORE: ask.py
Purpose : Given a user question, find best answer chunk(s) and cite source files.
Inputs  : user query (str)
Outputs : answer (str), citations (list)
Uses    : prompts/retrieval_prompt.md, all-MiniLM-L6-v2 embeddings, Local LLM (Qwen2.5-1.5B)
"""

import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple, Union

from loguru import logger

from .config import EXTRACTS_DIR, LLM_CONFIG, calculate_document_page
from .embedding import Embedder
from .llm import get_llm

_INDEX_BOOTSTRAPPED = False
_PROMPT_TEMPLATE = None


def _get_prompt_template() -> str:
    """Load and cache the prompt template from disk.

    Returns:
        Cached prompt template string
    """
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        prompt_path = Path(__file__).parent.parent / "prompts" / "retrieval_prompt.md"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                _PROMPT_TEMPLATE = f.read()
            logger.debug("CACHE: Loaded and cached prompt template")
        except FileNotFoundError:
            # Fallback template if file doesn't exist
            _PROMPT_TEMPLATE = """
Context: {context}

Question: {question}

Please provide a comprehensive answer based on the context above. Include specific details and cite your sources using [1], [2], etc.

Answer:"""
            logger.warning("CACHE: Using fallback prompt template (file not found)")
    return _PROMPT_TEMPLATE


def answer_question(
    query: str, top_k: int = 3, streaming: bool = False
) -> Union[
    Tuple[str, List[Dict[str, Any]]], Tuple[Iterator[str], List[Dict[str, Any]]]
]:
    """
    Answer a question using RAG with numbered citations and page numbers.

    Args:
        query: User's question
        top_k: Number of top chunks to retrieve for context (default: 5)
        streaming: If True, return generator for streaming; if False, return complete answer

    Returns:
        If streaming=False: Tuple of (answer_text, citations)
        If streaming=True: Tuple of (generator, citations)
        where citations is [{"id": int, "file": str, "page": int, "chunk": str}]
    """
    logger.info(f"THINKING: Answering question: '{query}' (streaming={streaming})")

    # 1. Embed the question and find top chunks
    retrieval_start = time.time()
    embedder = Embedder()
    results = embedder.query(query, k=top_k)
    retrieval_time = time.time() - retrieval_start
    logger.info(f"⏱️ RETRIEVAL TIME: {retrieval_time:.2f}s")

    # If the index/DB isn't ready yet (common in fresh test/dev environments),
    # bootstrap once from extracts and retry.
    global _INDEX_BOOTSTRAPPED
    if (not results) and (not _INDEX_BOOTSTRAPPED):
        try:
            index_exists = Path(embedder.index_path).exists()
            db_exists = Path(embedder.db_path).exists()

            needs_bootstrap = (not index_exists) or (not db_exists)

            # If files exist, also ensure they contain usable data.
            if not needs_bootstrap:
                try:
                    # If the FAISS index is empty (ntotal==0), retrieval will always fail.
                    index_obj = embedder._get_index()
                    if index_obj is None or getattr(index_obj, "ntotal", 0) == 0:
                        needs_bootstrap = True

                    # If metadata is empty or clearly out of sync with the index, rebuild.
                    from core.database import DatabaseManager

                    meta_count = DatabaseManager(embedder.db_path).get_record_count()
                    if meta_count == 0:
                        needs_bootstrap = True
                    elif (
                        index_obj is not None
                        and getattr(index_obj, "ntotal", 0) != meta_count
                    ):
                        needs_bootstrap = True
                except Exception:
                    needs_bootstrap = True

            if needs_bootstrap and Path(EXTRACTS_DIR).exists():
                logger.warning(
                    "Index/metadata missing or empty; bootstrapping index from extracts..."
                )
                embedder.build_index(watch_paths=EXTRACTS_DIR)
                _INDEX_BOOTSTRAPPED = True

                retrieval_start = time.time()
                results = embedder.query(query, k=top_k)
                retrieval_time = time.time() - retrieval_start
                logger.info(
                    f"⏱️ RETRIEVAL TIME (after bootstrap): {retrieval_time:.2f}s"
                )
        except Exception as e:
            logger.warning(f"Index bootstrap failed: {e}")

    if not results:
        empty_answer = (
            "I couldn't find any relevant information to answer your question."
        )
        if streaming:
            return (iter([empty_answer]), [])
        return (empty_answer, [])

    logger.info(f"FOUND: {len(results)} relevant chunks")

    # 2. Check relevance threshold - if all results have poor scores, return no answer
    RELEVANCE_THRESHOLD = 1.2  # Cosine distance threshold (lower = more similar)
    relevant_results = []
    for result in results:
        chunk_text, file_path, chunk_id, doc_chunk_id, score = result
        if chunk_text and file_path and score < RELEVANCE_THRESHOLD:
            relevant_results.append(result)

    if not relevant_results:
        no_relevant_answer = "I couldn't find relevant information in the provided documents to answer this question."
        if streaming:
            return (iter([no_relevant_answer]), [])
        return (no_relevant_answer, [])

    # Use only relevant results for further processing
    results = relevant_results
    logger.info(f"RELEVANT: {len(results)} chunks passed relevance threshold")

    # 3. Get cached prompt template
    prompt_template = _get_prompt_template()

    # 4. Build citations first (needed for both streaming and non-streaming)
    citations = []
    context_parts = []
    for i, result in enumerate(results):
        chunk_text, file_path, chunk_id, doc_chunk_id, score = result
        if chunk_text and file_path:
            # Calculate actual page within document
            estimated_page = calculate_document_page(doc_chunk_id)
            citations.append(
                {
                    "id": i + 1,
                    "file": file_path,
                    "page": estimated_page,  # Real document page estimate
                    "chunk": (
                        chunk_text[:300] + "..."
                        if len(chunk_text) > 300
                        else chunk_text
                    ),
                    "score": float(score),
                }
            )
            context_parts.append(f"[{i + 1}] {chunk_text}")

    # 5. Create the full prompt
    context = "\n\n".join(context_parts)
    full_prompt = prompt_template.format(context=context, question=query)

    # 6. Generate answer with streaming or non-streaming
    try:
        generation_start = time.time()
        if streaming:
            # Return streaming generator; log timing inside generator
            answer_generator = _generate_streaming_answer_with_llm(
                full_prompt, citations, generation_start, retrieval_time
            )
            return answer_generator, citations
        else:
            # Return complete answer (existing behavior)
            answer = _generate_answer_with_llm(full_prompt, citations)
            generation_time = time.time() - generation_start
            logger.info(f"⏱️ GENERATION TIME: {generation_time:.2f}s")
            logger.info(f"⏱️ TOTAL TIME: {retrieval_time + generation_time:.2f}s")
            return answer, citations
    except Exception as e:
        logger.error(f"ERROR: Answer generation failed: {e}")
        fallback_answer = _generate_fallback_answer(query, results, citations)
        if streaming:
            return (iter([fallback_answer]), citations)
        return fallback_answer, citations


def _generate_answer_with_llm(prompt: str, citations: List[Dict]) -> str:
    """
    Generate an answer using Phi-3 LLM with config settings.

    Args:
        prompt: The formatted prompt with question and context
        citations: List of citation dictionaries for reference

    Returns:
        AI-generated answer with citations
    """
    try:
        # Get LLM instance
        llm = get_llm()

        # Generate answer using Phi-3 with config settings (single source of truth)
        raw_answer = llm.generate_answer(
            prompt=prompt,
            max_tokens=int(LLM_CONFIG["max_tokens"]),  # Ensure int type
            temperature=float(LLM_CONFIG["temperature"]),  # Ensure float type
            stop_sequences=["<|im_end|>", "\n\nQuestion:", "\n\nContext:"],
        )

        # Clean up the answer
        answer = raw_answer.strip()
        return answer

    except Exception as e:
        logger.error(f"ERROR: Phi-3 generation error: {e}")
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
    answer += "\n\n(Note: Generated using context extraction - Phi-3 unavailable)"

    return answer


def _generate_fallback_answer(query: str, results: List, citations: List[Dict]) -> str:
    """
    Generate a simple fallback answer when main generation fails.
    """
    if not results:
        return "I couldn't find relevant information to answer your question."

    best_chunk, best_file, _, _, best_score = results[0]  # Fixed for 5-tuple

    answer = (
        f"I found relevant information about your question: "
        f"{best_chunk[:300]}... [1]"
    )

    return answer


def _generate_streaming_answer_with_llm(
    prompt: str,
    citations: List[Dict],
    generation_start: float,
    retrieval_time: float,
):
    """
    Generate a streaming answer using Phi-3 LLM with config settings.

    Args:
        prompt: The formatted prompt with question and context
        citations: List of citation dictionaries for reference

    Yields:
        Partial answer strings as they are generated
    """
    try:
        # Get LLM instance with timing diagnostic
        pre_get_llm = time.time()
        llm = get_llm()
        llm_get_time = time.time() - pre_get_llm
        logger.info(f"⏱️ LLM GET: {llm_get_time:.2f}s (singleton lookup)")

        # Generate streaming answer using Phi-3 with timing
        full_answer = ""
        token_count = 0
        first_token_time: float | None = None
        pre_generate = time.time()

        for token in llm.generate_streaming_answer(
            prompt=prompt,
            max_tokens=int(LLM_CONFIG["max_tokens"]),
            temperature=float(LLM_CONFIG["temperature"]),
        ):
            if token:
                token_count += 1
                if first_token_time is None:
                    first_token_time = time.time()
                    time_to_first = first_token_time - generation_start
                    prompt_processing_time = first_token_time - pre_generate
                    logger.info(
                        f"⏱️ FIRST TOKEN: {time_to_first:.2f}s total "
                        f"(LLM get: {llm_get_time:.2f}s, prompt processing: {prompt_processing_time:.2f}s)"
                    )
                full_answer += token
                yield token

        # Log total generation time (streaming) with detailed breakdown
        total_generation_time = time.time() - generation_start
        tokens_per_sec = (
            token_count / total_generation_time if total_generation_time > 0 else 0
        )
        logger.info(
            f"⏱️ GENERATION TIME (stream): {total_generation_time:.2f}s "
            f"(tokens={token_count}, rate={tokens_per_sec:.2f} tok/s)"
        )
        logger.info(
            f"⏱️ TOTAL TIME (stream): {retrieval_time + total_generation_time:.2f}s"
        )

    except Exception as e:
        logger.error(f"ERROR: Phi-3 streaming generation error: {e}")
        # Fall back to context-based answer
        fallback_answer = _generate_context_based_answer(citations)
        for char in fallback_answer:
            yield char
