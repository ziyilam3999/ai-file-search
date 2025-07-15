"""🤖 llm.py
Purpose : Phi-3 Local LLM integration for answer generation
Inputs  : question + context chunks
Outputs : AI-generated answer with citations
Uses    : llama-cpp-python, Phi-3-mini-4k-instruct-q4.gguf
"""

import os
from pathlib import Path
from typing import Optional

from loguru import logger


class Phi3LLM:
    """Phi-3 Local LLM for answer generation."""

    def __init__(self, model_path: Optional[str] = None, verbose: bool = False):
        """
        Initialize Phi-3 model.

        Args:
            model_path: Path to the Phi-3 GGUF model file
            verbose: Enable verbose llama.cpp logging
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python not found. Install with: pip install llama-cpp-python"
            )

        if model_path is None:
            # Default path to Phi-3 model
            model_path = str(
                Path(__file__).parent.parent
                / "ai_models"
                / "Phi-3-mini-4k-instruct-q4.gguf"
            )

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Phi-3 model not found: {self.model_path}")

        logger.info(f"🤖 Loading Phi-3 model: {self.model_path.name}")

        # Initialize llama.cpp model without ChatML format
        self.llm = Llama(
            model_path=str(self.model_path),
            n_ctx=1536,  # Further reduced from 2048 for speed
            n_threads=8,  # Increased from 6 (if you have 8+ cores)
            n_batch=256,  # Reduced from 512 for faster processing
            verbose=verbose,
            # No chat_format - use raw completion
        )

        logger.success("✅ Phi-3 model loaded successfully")

    def generate_answer(
        self,
        prompt: str,
        max_tokens: int = 150,  # FINAL PUSH: Reduced from 200 for target speed
        temperature: float = 0.35,  # FINAL PUSH: Increased from 0.3 for faster generation
        stop_sequences: Optional[list] = None,
    ) -> str:
        """
        Generate an answer using Phi-3.

        Args:
            prompt: The formatted prompt with question and context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.35 for maximum performance)
            stop_sequences: Sequences that should stop generation

        Returns:
            Generated answer text
        """
        if stop_sequences is None:
            stop_sequences = ["\n\nQuestion:", "\n\nContext:", "Question:", "Context:"]

        logger.info(
            f"🤖 Generating answer (max_tokens={max_tokens}, temp={temperature})"
        )

        try:
            # Use direct completion instead of chat completion for RAG prompts
            response = self.llm.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,  # Use parameter
                temperature=temperature,  # Use parameter
                stop=["Question:", "Context:", "\n\n\n", "References:"],
                stream=False,
            )

            answer = response["choices"][0]["text"].strip()

            logger.success(f"✅ Generated {len(answer)} character answer")
            return answer

        except Exception as e:
            logger.error(f"❌ Phi-3 generation failed: {e}")
            raise

    def generate_streaming_answer(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.35,  # Updated defaults
    ):
        """
        Generate an answer with streaming output (for future CLI enhancement).

        Args:
            prompt: The formatted prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Token strings as they are generated
        """
        logger.info("🤖 Starting streaming generation...")

        try:
            # Use create_completion with stream=True instead of chat_completion
            stream = self.llm.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                stop=[
                    "Question:",
                    "Context:",
                    "\n\n\n",
                    "References:",
                ],  # Updated stop sequences
            )

            for chunk in stream:
                if chunk["choices"][0].get("text"):
                    yield chunk["choices"][0]["text"]

        except Exception as e:
            logger.error(f"❌ Streaming generation failed: {e}")
            raise

    def is_available(self) -> bool:
        """Check if the model is properly loaded and available."""
        return hasattr(self, "llm") and self.llm is not None


# Global instance for reuse (avoid reloading the model)
_phi3_instance: Optional[Phi3LLM] = None


def get_phi3_llm(model_path: Optional[str] = None, verbose: bool = False) -> Phi3LLM:
    """
    Get or create a Phi-3 LLM instance (singleton pattern).

    Args:
        model_path: Path to model file (only used on first call)
        verbose: Enable verbose logging (only used on first call)

    Returns:
        Phi3LLM instance
    """
    global _phi3_instance

    if _phi3_instance is None:
        _phi3_instance = Phi3LLM(model_path, verbose)

    return _phi3_instance
