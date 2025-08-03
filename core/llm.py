"""LLM: llm.py
Purpose : Phi-3 Local LLM integration for answer generation
Inputs  : question + context chunks
Outputs : AI-generated answer with citations
Uses    : llama-cpp-python, Phi-3-mini-4k-instruct-q4.gguf
"""

import os
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import LLM_CONFIG


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

        logger.info(f"LOADING: Phi-3 model: {self.model_path.name}")

        # Initialize llama.cpp model using config settings
        self.llm = Llama(
            model_path=str(self.model_path),
            n_ctx=LLM_CONFIG["n_ctx"],  # Use config value
            n_threads=LLM_CONFIG["n_threads"],  # Use config value
            n_batch=LLM_CONFIG["n_batch"],  # Use config value
            verbose=verbose,
            # No chat_format - use raw completion
        )

        logger.success("SUCCESS: Phi-3 model loaded successfully")

    def generate_answer(
        self,
        prompt: str,
        max_tokens: int | None = None,  # None = use config default
        temperature: float | None = None,  # None = use config default
        stop_sequences: Optional[list] = None,
    ) -> str:
        """
        Generate an answer using Phi-3.

        Args:
            prompt: The formatted prompt with question and context
            max_tokens: Maximum tokens to generate (None = use config)
            temperature: Sampling temperature (None = use config)
            stop_sequences: Sequences that should stop generation

        Returns:
            Generated answer text
        """
        # Use config defaults if not specified with explicit type casting
        actual_max_tokens: int = (
            max_tokens if max_tokens is not None else int(LLM_CONFIG["max_tokens"])
        )
        actual_temperature: float = (
            temperature if temperature is not None else float(LLM_CONFIG["temperature"])
        )

        if stop_sequences is None:
            stop_sequences = ["\n\nQuestion:", "\n\nContext:", "Question:", "Context:"]

        logger.info(
            f"GENERATING: answer (max_tokens={actual_max_tokens}, temp={actual_temperature})"
        )

        try:
            # Use direct completion instead of chat completion for RAG prompts
            response = self.llm.create_completion(
                prompt=prompt,
                max_tokens=actual_max_tokens,  # Use parameter
                temperature=actual_temperature,  # Use parameter
                stop=["Question:", "Context:", "\n\n\n", "References:"],
                stream=False,
            )

            answer = response["choices"][0]["text"].strip()

            logger.success(f"SUCCESS: Generated {len(answer)} character answer")
            return answer

        except Exception as e:
            logger.error(f"ERROR: Phi-3 generation failed: {e}")
            raise

    def generate_streaming_answer(
        self,
        prompt: str,
        max_tokens: int | None = None,  # None = use config default
        temperature: float | None = None,  # None = use config default
    ):
        """
        Generate an answer with streaming output (for future CLI enhancement).

        Args:
            prompt: The formatted prompt
            max_tokens: Maximum tokens to generate (None = use config)
            temperature: Sampling temperature (None = use config)

        Yields:
            Token strings as they are generated
        """
        # Use config defaults if not specified with explicit type casting
        actual_max_tokens: int = (
            max_tokens if max_tokens is not None else int(LLM_CONFIG["max_tokens"])
        )
        actual_temperature: float = (
            temperature if temperature is not None else float(LLM_CONFIG["temperature"])
        )

        logger.info("STREAMING: Starting streaming generation...")

        try:
            # Use create_completion with stream=True instead of chat_completion
            stream = self.llm.create_completion(
                prompt=prompt,
                max_tokens=actual_max_tokens,
                temperature=actual_temperature,
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
            logger.error(f"ERROR: Streaming generation failed: {e}")
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
