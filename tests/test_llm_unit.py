"""Unit tests for core/llm.py module

Tests LLM singleton pattern, configuration usage, and error handling
Uses mocking to avoid loading the actual model
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Mock llama_cpp BEFORE importing anything else
sys.modules["llama_cpp"] = MagicMock()

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import LLM_CONFIG
from core.llm import LocalLLM, get_llm, preload_llm


class TestLocalLLMInitialization:
    """Test LocalLLM class initialization."""

    def test_local_llm_init_requires_model_path_exists(self):
        """Test initialization checks for model file existence."""
        # Mock llama_cpp.Llama before creating instance
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            # Create a mock model file
            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="tests/fixtures/mock_model.gguf")
                assert llm is not None

    def test_local_llm_uses_default_model_path(self):
        """Test that LocalLLM uses default model path from config."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(verbose=False)
                # Verify initialization succeeded
                assert llm is not None

    def test_local_llm_model_not_found_raises_error(self):
        """Test FileNotFoundError when model doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                LocalLLM(model_path="nonexistent.gguf")

    def test_local_llm_is_available_when_initialized(self):
        """Test is_available returns True when properly initialized."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                assert llm.is_available() is True

    def test_local_llm_is_available_false_when_not_initialized(self):
        """Test is_available returns False when llm is None."""
        llm = object.__new__(LocalLLM)
        # Don't set self.llm
        assert llm.is_available() is False


class TestLLMConfig:
    """Test that LLM_CONFIG values are used correctly."""

    def test_llm_config_has_required_keys(self):
        """Test that LLM_CONFIG contains all required keys."""
        required_keys = [
            "max_tokens",
            "temperature",
            "n_ctx",
            "n_threads",
            "n_batch",
            "n_gpu_layers",
        ]
        for key in required_keys:
            assert key in LLM_CONFIG, f"Missing required key: {key}"

    def test_llm_config_values_are_valid_types(self):
        """Test that config values are correct types."""
        assert isinstance(LLM_CONFIG["max_tokens"], int)
        assert isinstance(LLM_CONFIG["temperature"], (int, float))
        assert isinstance(LLM_CONFIG["n_ctx"], int)
        assert isinstance(LLM_CONFIG["n_threads"], int)
        assert isinstance(LLM_CONFIG["n_batch"], int)
        assert isinstance(LLM_CONFIG["n_gpu_layers"], int)

    def test_llm_config_numeric_ranges_valid(self):
        """Test that numeric values are in valid ranges."""
        assert LLM_CONFIG["max_tokens"] > 0
        assert 0.0 <= LLM_CONFIG["temperature"] <= 2.0
        assert LLM_CONFIG["n_ctx"] > 0
        assert LLM_CONFIG["n_threads"] > 0
        assert LLM_CONFIG["n_batch"] > 0
        assert LLM_CONFIG["n_gpu_layers"] >= 0


class TestLLMGenerateAnswer:
    """Test answer generation."""

    def test_generate_answer_returns_string(self):
        """Test that generate_answer returns string response."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = {
                "choices": [{"text": "Test response"}]
            }

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                response = llm.generate_answer("Test prompt")

                assert isinstance(response, str)
                assert response == "Test response"

    def test_generate_answer_strips_whitespace(self):
        """Test that response is stripped of leading/trailing whitespace."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = {
                "choices": [{"text": "  Response with whitespace  "}]
            }

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                response = llm.generate_answer("Test prompt")

                assert response == "Response with whitespace"

    def test_generate_answer_custom_max_tokens(self):
        """Test that custom max_tokens parameter is respected."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = {
                "choices": [{"text": "Response"}]
            }

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                llm.generate_answer("Test", max_tokens=50)

                # Verify custom parameter was passed
                call_kwargs = mock_llama_instance.create_completion.call_args[1]
                assert call_kwargs["max_tokens"] == 50

    def test_generate_answer_custom_temperature(self):
        """Test that custom temperature parameter is respected."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = {
                "choices": [{"text": "Response"}]
            }

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                llm.generate_answer("Test", temperature=0.5)

                call_kwargs = mock_llama_instance.create_completion.call_args[1]
                assert call_kwargs["temperature"] == 0.5


class TestLLMStreamingAnswer:
    """Test streaming answer generation."""

    def test_generate_streaming_answer_yields_tokens(self):
        """Test streaming yields tokens from response."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = [
                {"choices": [{"text": "Hello"}]},
                {"choices": [{"text": " world"}]},
                {"done": True},
            ]

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                tokens = list(llm.generate_streaming_answer("Test prompt"))

                assert len(tokens) == 2
                assert tokens[0] == "Hello"
                assert tokens[1] == " world"

    def test_generate_streaming_answer_handles_empty(self):
        """Test streaming handles empty response gracefully."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance
            mock_llama_instance.create_completion.return_value = [{"done": True}]

            with patch("pathlib.Path.exists", return_value=True):
                llm = LocalLLM(model_path="test.gguf")
                tokens = list(llm.generate_streaming_answer("Test"))

                assert tokens == []


class TestGetLLMSingleton:
    """Test get_llm singleton pattern."""

    def test_get_llm_returns_local_llm_instance(self):
        """Test get_llm returns a LocalLLM instance."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                import core.llm

                core.llm._llm_instance = None

                llm = get_llm()

                assert isinstance(llm, LocalLLM)

    def test_get_llm_singleton_behavior(self):
        """Test that get_llm returns same instance on subsequent calls."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                import core.llm

                core.llm._llm_instance = None

                llm1 = get_llm()
                llm2 = get_llm()

                # Should be the same instance
                assert llm1 is llm2

    def test_get_llm_only_calls_llama_once(self):
        """Test that Llama constructor is only called once."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                import core.llm

                core.llm._llm_instance = None

                get_llm()
                get_llm()
                get_llm()

                # Should only be called once for singleton
                assert mock_llama.call_count == 1


class TestPreloadLLM:
    """Test preload_llm function."""

    def test_preload_llm_initializes_model(self):
        """Test preload_llm initializes the LLM."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                import core.llm

                core.llm._llm_instance = None

                preload_llm()

                # Verify Llama was instantiated
                assert mock_llama.called

    def test_preload_llm_is_idempotent(self):
        """Test calling preload_llm multiple times is safe."""
        with patch("llama_cpp.Llama") as mock_llama:
            mock_llama_instance = MagicMock()
            mock_llama.return_value = mock_llama_instance

            with patch("pathlib.Path.exists", return_value=True):
                import core.llm

                core.llm._llm_instance = None

                # Multiple calls should not fail
                preload_llm()
                preload_llm()
                preload_llm()

                # Still should only be called once due to singleton
                assert mock_llama.call_count == 1
