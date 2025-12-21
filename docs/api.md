# API Reference

Technical API documentation for core system components.

## Embedder API

### Class: `core.embedding.Embedder`

The main class for semantic search and document indexing.

### Critical: Query Return Format

**REQUIREMENT**: The `Embedder.query()` method MUST return a 4-tuple format.

```python
def query(self, query: str, k: int = 5) -> List[Tuple[str, str, int, float]]:
    """
    Search for relevant document chunks.
    
    Args:
        query: Natural language search query
        k: Number of results to return (default: 5)
    
    Returns:
        List of tuples: (chunk_text, file_path, chunk_id, score)
    """
```

#### Return Format Details

| Position | Element | Type | Description |
|----------|---------|------|-------------|
| 0 | chunk_text | str | The actual text content of the chunk |
| 1 | file_path | str | Relative path to the source file |
| 2 | chunk_id | int | Unique identifier for the chunk |
| 3 | score | float | FAISS distance/similarity score |

#### Example Return Value

```python
[
    ("Modern Web Application Architecture 1. Frontend...", "ai_search_docs/technical_docs/web_architecture.txt", 3, 1.968598),
    ("Database design patterns include...", "ai_search_docs/technical_docs/database_guide.txt", 15, 2.123456),
    ("API versioning strategies...", "ai_search_docs/software_dev/api_design.txt", 7, 2.456789)
]
```

### Method: `build_index()`

```python
def build_index(self) -> None:
    """
    Build FAISS index from all documents in extracts/ directory.
    
    - Processes all .txt files in extracts/
    - Generates sentence embeddings using all-MiniLM-L6-v2
    - Creates FAISS IndexFlatL2 with 384 dimensions
    - Stores metadata in SQLite database
    - Maps citations to original files in ai_search_docs/
    """
```

### Method: `_map_to_original_file()`

```python
def _map_to_original_file(self, extracts_rel_path: str) -> Optional[str]:
    """
    Map extracted file path back to original file in ai_search_docs/.
    
    Args:
        extracts_rel_path: Relative path from extracts/ directory
    
    Returns:
        Path to original file in ai_search_docs/, or None if not found
    
    Priority order: PDF → DOCX → TXT → MD
    """
```

## LLM API

### Class: `core.llm.LLMClient`

Interface for the Phi-3 language model.

```python
def generate_answer(self, prompt: str) -> str:
    """
    Generate answer using optimized configuration.
    
    Args:
        prompt: The prompt to send to the LLM
    
    Returns:
        Generated text response
    
    Uses configuration from core.config.LLM_CONFIG
    """
```

### Streaming Support

```python
def generate_streaming_answer(self, prompt: str) -> Iterator[str]:
    """
    Generate answer with real-time token streaming.
    
    Yields:
        Individual tokens as they are generated
    """
```

## Configuration API

### Module: `core.config`

Centralized configuration management.

```python
# Default configuration
LLM_CONFIG = {
    "max_tokens": 150,
    "temperature": 0.1,
    "n_ctx": 1536,
    "n_threads": 8,
    "n_batch": 256,
}

# Speed presets
SPEED_PRESETS = {
    "ultra_fast": {"max_tokens": 50, "temperature": 0.0},
    "fast": {"max_tokens": 150, "temperature": 0.1},
    "balanced": {"max_tokens": 200, "temperature": 0.3},
    "quality": {"max_tokens": 400, "temperature": 0.5},
}
```

### Functions

```python
def set_speed_preset(preset_name: str) -> None:
    """Apply speed preset to LLM_CONFIG."""

def show_current_config() -> None:
    """Display current settings and available presets."""

def print_performance_estimate() -> None:
    """Show estimated response times for current config."""
```

## Ask API

### Module: `core.ask`

Question answering with context retrieval.

```python
def answer(question: str, streaming: bool = False) -> str:
    """
    Answer a question using retrieved context.
    
    Args:
        question: Natural language question
        streaming: Enable real-time token streaming
    
    Returns:
        AI-generated answer with citations
    
    Applies relevance threshold (1.2) to filter irrelevant queries.
    """
```

## Extraction API

### Module: `core.extract`

Document text extraction.

```python
def extract_text(file_path: str) -> str:
    """
    Extract text from PDF, DOCX, TXT, or MD file.
    
    Args:
        file_path: Path to the document file
    
    Returns:
        Extracted text content
    
    Raises:
        ValueError: If file type is not supported
    """
```

## System Dependencies

Components that depend on these APIs:

- `ui/app.py`: Streamlit web interface
- `daemon/watch.py`: File watcher (EmbeddingAdapter)
- `cli.py`: Command-line interface
- `tests/`: Test suite validation

---

*Last Updated: 2025-12-21*
