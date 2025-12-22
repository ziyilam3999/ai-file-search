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
