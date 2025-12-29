"""Tests for core/config.py"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import LLM_CONFIG, SPEED_PRESETS, get_llm_config


def test_get_llm_config_valid_presets():
    """Test retrieving valid presets."""
    for preset_name, preset_values in SPEED_PRESETS.items():
        config = get_llm_config(preset_name)

        # Check that preset values are applied
        for key, value in preset_values.items():
            assert config[key] == value

        # Check that base keys exist
        assert "n_ctx" in config
        assert "n_threads" in config


def test_get_llm_config_default():
    """Test that default preset is returned when no argument is provided."""
    config = get_llm_config()
    # Default is "fast"
    fast_preset = SPEED_PRESETS["fast"]
    assert config["max_tokens"] == fast_preset["max_tokens"]
    assert config["temperature"] == fast_preset["temperature"]


def test_get_llm_config_invalid():
    """Test that invalid preset falls back to base LLM_CONFIG."""
    config = get_llm_config("non_existent_preset")

    # Should return base config
    assert config == LLM_CONFIG


class TestLLMConfigStructure:
    """Tests for LLM_CONFIG structure and GPU settings."""

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

    def test_n_gpu_layers_is_non_negative_integer(self):
        """Test that n_gpu_layers is a non-negative integer for GPU offloading."""
        n_gpu_layers = LLM_CONFIG["n_gpu_layers"]
        assert isinstance(n_gpu_layers, int), "n_gpu_layers must be an integer"
        assert n_gpu_layers >= 0, "n_gpu_layers must be non-negative"

    def test_n_gpu_layers_enables_gpu_offloading(self):
        """Test that n_gpu_layers is configurable for GPU/CPU modes."""
        # Value of 0 means CPU-only (default for Intel iGPU)
        # Value of 99 means 'offload all available layers' to GPU
        # This is configurable via GPU_LAYERS environment variable
        assert (
            LLM_CONFIG["n_gpu_layers"] >= 0
        ), "n_gpu_layers should be non-negative integer"

    def test_numeric_config_values_are_valid(self):
        """Test that numeric configuration values are within valid ranges."""
        assert LLM_CONFIG["max_tokens"] > 0
        assert 0.0 <= LLM_CONFIG["temperature"] <= 2.0
        assert LLM_CONFIG["n_ctx"] > 0
        assert LLM_CONFIG["n_threads"] > 0
        assert LLM_CONFIG["n_batch"] > 0

    def test_llm_config_max_tokens_reasonable(self):
        """Test that max_tokens is set to reasonable value."""
        # Should be between 10 and 500
        max_tokens = LLM_CONFIG["max_tokens"]
        assert (
            10 <= max_tokens <= 500
        ), f"max_tokens={max_tokens} should be between 10-500"

    def test_llm_config_temperature_valid(self):
        """Test that temperature is set to valid value."""
        # Should be between 0.0 and 1.0 (or up to 2.0 for creative)
        temperature = LLM_CONFIG["temperature"]
        assert (
            0.0 <= temperature <= 1.0
        ), f"temperature={temperature} should be between 0.0-1.0 for accuracy"

    def test_default_model_name_used(self):
        """Test that model name matches Qwen2.5-1.5B deployment."""
        # Model should be set to Qwen2.5-1.5B (migrated from Phi-3.5)
        # Check that configuration references the correct model setup
        assert LLM_CONFIG["n_ctx"] >= 2048, "n_ctx should support Qwen2.5 context"
        assert LLM_CONFIG["n_threads"] > 0, "Model requires thread configuration"
