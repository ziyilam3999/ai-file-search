"""Configuration settings for AI File Search
Single source of truth for all LLM and performance settings
"""

# ============================================================================
# PATH CONSTANTS - Single source of truth for file paths
# ============================================================================
INDEX_PATH = "index.faiss"
DATABASE_PATH = "meta.sqlite"
DOCUMENTS_DIR = "ai_search_docs"  # Deprecated as single source, used as default
EXTRACTS_DIR = "extracts"  # Deprecated
LOGS_DIR = "logs"
BACKUPS_DIR = "backups"
AI_MODELS_DIR = "ai_models"
DEFAULT_MODEL_NAME = "Phi-3-mini-4k-instruct-q4.gguf"
CONFIG_PATH = "prompts/watcher_config.yaml"


def load_watch_paths() -> list[str]:
    """Load watch paths from configuration file."""
    from pathlib import Path

    import yaml

    try:
        if Path(CONFIG_PATH).exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("watch_paths", [DOCUMENTS_DIR])
    except Exception as e:
        print(f"Error loading config: {e}")

    return [DOCUMENTS_DIR]


# LLM Generation Settings - OPTIMIZED FOR SPEED (105s → ~70-80s target)
LLM_CONFIG = {
    "max_tokens": 30,  # Reduced for faster responses (30 words)
    "temperature": 0.1,  # Keep deterministic
    "n_ctx": 2048,  # Context window (must fit prompt + retrieved chunks + output)
    "n_threads": 8,  # CPU threads for inference
    "n_batch": 384,  # Larger batch for higher throughput (watch RAM)
}

# Performance Presets for easy speed vs quality tuning
SPEED_PRESETS = {
    "ultra_fast": {"max_tokens": 50, "temperature": 0.0},  # ~35-40 words, deterministic
    "fast": {
        "max_tokens": 150,
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


# Embedding & Chunking Settings - SINGLE SOURCE OF TRUTH
EMBEDDING_CONFIG = {
    "chunk_size": 400,  # Words per chunk
    "chunk_overlap": 25,  # Overlapping words between chunks
    "words_per_page": 300,  # Estimated words per page for citation calculation
}


def calculate_document_page(doc_chunk_id: int) -> int:
    """
    Calculate estimated page number based on document content analysis.

    This estimates total pages from document chunks and words, calibrated to
    produce realistic page counts for typical books.

    Args:
        doc_chunk_id: The chunk position within the document (1-based)

    Returns:
        Estimated page number within the document
    """
    import sqlite3

    # Get document info for this chunk
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Find which document this chunk belongs to and get total chunks
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM meta
        WHERE file = (SELECT file FROM meta WHERE doc_chunk_id = ? LIMIT 1)
    """,
        (doc_chunk_id,),
    )

    result = cursor.fetchone()
    conn.close()

    if not result or not result[0]:
        return 1

    total_chunks = result[0]

    # Get chunking parameters from config
    chunk_size = EMBEDDING_CONFIG["chunk_size"]
    chunk_overlap = EMBEDDING_CONFIG["chunk_overlap"]

    # Calculate effective words per chunk (excluding overlap)
    effective_words_per_chunk = chunk_size - chunk_overlap

    # Estimate total words in the document
    estimated_total_words = total_chunks * effective_words_per_chunk

    # Use calibrated words-per-page ratio for realistic page estimates
    # Calibrated based on Peter Pan (115 pages, 135 chunks) = ~440 words/page
    words_per_page = 440
    estimated_total_pages = max(10, estimated_total_words / words_per_page)

    # Calculate proportional position within the estimated page range
    position_percent = doc_chunk_id / total_chunks
    estimated_page = max(1, int(position_percent * estimated_total_pages))

    return estimated_page
