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

from .config import AI_MODELS_DIR, DEFAULT_MODEL_NAME, LLM_CONFIG


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
                Path(__file__).parent.parent / AI_MODELS_DIR / DEFAULT_MODEL_NAME
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

        # Warm-start: run a tiny completion to prime the model/cache
        self._warm_start()

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
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Generate an answer with streaming output for real-time UI updates.

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

        logger.info(
            f"STREAMING: Starting generation (max_tokens={actual_max_tokens}, temp={actual_temperature})"
        )

        try:
            # Use create_completion with stream=True
            stream = self.llm.create_completion(
                prompt=prompt,
                max_tokens=actual_max_tokens,
                temperature=actual_temperature,
                stream=True,
                stop=["Question:", "Context:", "\n\n\n", "References:"],
            )

            token_count = 0
            for chunk in stream:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    token = chunk["choices"][0].get("text", "")
                    if token:
                        token_count += 1
                        yield token

            logger.success(f"STREAMING: Completed {token_count} tokens")

        except Exception as e:
            logger.error(f"ERROR: Streaming generation failed: {e}")
            # Fallback: yield an error message
            yield f"Error generating response: {str(e)}"

    def _warm_start(self) -> None:
        """Run a tiny completion to prime the model so first user query is faster."""
        try:
            self.llm.create_completion(
                prompt="Warm start",
                max_tokens=1,
                temperature=0.0,
                stream=False,
                stop=["Warm"],
            )
            logger.info("WARM START: Primed model with a 1-token run")
        except Exception as e:
            logger.warning(f"WARM START: skipped due to error: {e}")

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
        logger.info("SINGLETON: Creating NEW Phi-3 instance (first time)")
        _phi3_instance = Phi3LLM(model_path, verbose)
    else:
        logger.info("SINGLETON: Reusing EXISTING Phi-3 instance (model already loaded)")

    return _phi3_instance
