"""Configuration settings for AI File Search
Single source of truth for all LLM and performance settings
"""

# LLM Generation Settings - OPTIMIZED FOR SPEED (51.9s → <20s target)
LLM_CONFIG = {
    "max_tokens": 100,  # Tokens for answer generation (optimized for speed)
    "temperature": 0.1,  # Temperature for deterministic responses (optimized for speed)
    "n_ctx": 1536,  # Context window size (reduced for speed)
    "n_threads": 8,  # CPU threads for inference
    "n_batch": 256,  # Batch size for processing (reduced for speed)
}

# Performance Presets for easy speed vs quality tuning
SPEED_PRESETS = {
    "ultra_fast": {"max_tokens": 50, "temperature": 0.0},  # ~35-40 words, deterministic
    "fast": {
        "max_tokens": 100,
        "temperature": 0.1,
    },  # ~75-80 words, mostly deterministic
    "balanced": {
        "max_tokens": 200,
        "temperature": 0.3,
    },  # ~150-160 words, some creativity
    "quality": {"max_tokens": 400, "temperature": 0.5},  # ~300-320 words, more creative
}


def get_llm_config(preset: str = "fast") -> dict:
    """
    Get LLM configuration for a given preset.

    Args:
        preset: One of 'ultra_fast', 'fast', 'balanced', 'quality'

    Returns:
        Dictionary with LLM configuration settings
    """
    if preset in SPEED_PRESETS:
        config = LLM_CONFIG.copy()
        config.update(SPEED_PRESETS[preset])
        return config
    return LLM_CONFIG.copy()


def set_speed_preset(preset: str) -> None:
    """
    Update the global LLM_CONFIG with a speed preset.

    Args:
        preset: One of 'ultra_fast', 'fast', 'balanced', 'quality'

    Example:
        set_speed_preset("ultra_fast")  # For maximum speed
        set_speed_preset("quality")     # For best answers
    """
    global LLM_CONFIG
    if preset in SPEED_PRESETS:
        LLM_CONFIG.update(SPEED_PRESETS[preset])
        print(f"SUCCESS: LLM Config updated to '{preset}' preset:")
        print(f"   max_tokens: {LLM_CONFIG['max_tokens']}")
        print(f"   temperature: {LLM_CONFIG['temperature']}")
    else:
        available = list(SPEED_PRESETS.keys())
        print(f"ERROR: Unknown preset '{preset}'. Available: {available}")


def show_current_config() -> None:
    """Display current LLM configuration and available presets."""
    print("CURRENT LLM Configuration:")
    for key, value in LLM_CONFIG.items():
        print(f"   {key}: {value}")
    print()
    print("AVAILABLE Speed Presets:")
    for preset, settings in SPEED_PRESETS.items():
        tokens = settings["max_tokens"]
        temp = settings["temperature"]
        words = f"~{int(tokens * 0.75)}-{int(tokens * 0.8)} words"
        print(f"   {preset:12} -> {tokens:3} tokens, {temp:3} temp ({words})")
    print()
    print("USAGE: set_speed_preset('ultra_fast') for maximum speed")


def get_performance_estimate(preset: str | None = None) -> dict:
    """
    Get estimated performance metrics for a preset.

    Args:
        preset: Speed preset name, or None for current config

    Returns:
        Dictionary with estimated metrics
    """
    if preset and preset in SPEED_PRESETS:
        config = SPEED_PRESETS[preset]
    else:
        config = LLM_CONFIG

    tokens = config["max_tokens"]
    temp = config["temperature"]

    # Rough estimates based on token count and temperature
    estimated_words = int(tokens * 0.75)
    estimated_chars = int(tokens * 4)

    # Speed estimates (very rough)
    if tokens <= 50:
        speed_category = "Ultra Fast"
        estimated_time = "5-15s"
    elif tokens <= 100:
        speed_category = "Fast"
        estimated_time = "10-25s"
    elif tokens <= 200:
        speed_category = "Balanced"
        estimated_time = "20-40s"
    else:
        speed_category = "Quality"
        estimated_time = "30-60s"

    return {
        "tokens": tokens,
        "temperature": temp,
        "estimated_words": estimated_words,
        "estimated_chars": estimated_chars,
        "speed_category": speed_category,
        "estimated_time": estimated_time,
    }


def print_performance_estimate(preset: str | None = None) -> None:
    """Print performance estimate in a readable format."""
    estimate = get_performance_estimate(preset)
    preset_name = preset or "current"

    print(f"PERFORMANCE ESTIMATE for '{preset_name}' preset:")
    print(f"   Tokens: {estimate['tokens']}")
    print(f"   Temperature: {estimate['temperature']}")
    print(f"   Estimated words: {estimate['estimated_words']}")
    print(f"   Estimated chars: {estimate['estimated_chars']}")
    print(f"   Speed category: {estimate['speed_category']}")
    print(f"   Estimated time: {estimate['estimated_time']}")


# Citation display settings (for UI optimization)
CITATION_CONFIG = {
    "max_citation_length": 150,  # Max characters per citation content
    "max_bullet_points": 1,  # Max bullet points per citation
    "max_words_per_bullet": 15,  # Max words per bullet point
    "show_full_file_path": False,  # Show abbreviated file paths for speed
    "minimal_mode": True,  # Use ultra-fast minimal citations by default
    "skip_content_processing": True,  # Skip content processing for max speed
}


def show_citation_config() -> None:
    """Display current citation configuration."""
    print("CITATION Configuration:")
    for key, value in CITATION_CONFIG.items():
        print(f"   {key}: {value}")


def set_citation_mode(minimal: bool = True) -> None:
    """
    Set citation display mode for speed optimization.

    Args:
        minimal: True for minimal/fast mode, False for detailed mode
    """
    global CITATION_CONFIG
    if minimal:
        CITATION_CONFIG.update(
            {
                "minimal_mode": True,
                "skip_content_processing": True,
                "max_citation_length": 100,
                "max_bullet_points": 1,
            }
        )
        print("SUCCESS: Citation mode set to MINIMAL (fastest)")
    else:
        CITATION_CONFIG.update(
            {
                "minimal_mode": False,
                "skip_content_processing": False,
                "max_citation_length": 300,
                "max_bullet_points": 3,
            }
        )
        print("SUCCESS: Citation mode set to DETAILED (slower)")
