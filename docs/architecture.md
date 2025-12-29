# Architecture

High-level design and technology stack decisions for the AI File Search system.

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | Python | 3.12+ | Core development |
| **Package Manager** | Poetry | 2.0+ | Dependency management |
| **Embedding Model** | all-MiniLM-L6-v2 | - | Sentence embeddings (384-dim) |
| **Vector Store** | FAISS | 1.11+ | Semantic search index |
| **LLM** | Qwen2.5-1.5B-Instruct | Q4_K_M quantized (1.1GB) | Local AI answer generation |
| **LLM Binding** | llama-cpp-python | 0.3.12+ | LLM inference (GPU optional) |
| **UI Framework** | Streamlit | 1.35+ | Web interface |
| **File Watcher** | watchdog | 6.0+ | Real-time file monitoring |
| **Scheduler** | APScheduler | 3.11+ | Nightly reindexing |
| **Logging** | Loguru | 0.7+ | Structured logging |

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   CLI        │  │  Streamlit   │  │  File Watcher Daemon │   │
│  │  (cli.py)    │  │  (ui/app.py) │  │  (smart_watcher.py)  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   ask.py     │  │ embedding.py │  │     extract.py       │   │
│  │  (Q&A)       │  │  (Search)    │  │  (Doc Processing)    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                     │                │
│         ▼                 ▼                     ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   llm.py     │  │  config.py   │  │     daemon/watch.py  │   │
│  │  (AI Model)  │  │  (Settings)  │  │  (File Monitoring)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ index.faiss  │  │ meta.sqlite  │  │   ai_search_docs/    │   │
│  │ (Vectors)    │  │ (Metadata)   │  │   (User Documents)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Watched Paths (User Files)
        │
        ▼ [daemon/watch.py + embedding.py]
   Memory (Text Extraction)
        │
        ▼ [embedding.py]
   index.faiss + meta.sqlite (Searchable Index)
        │
        ▼ [ask.py + llm.py]
   AI-Generated Answers with Citations
        │
        ▼ [Citations point back to]
   Original Files
```

## Directory Structure

```
ai-file-search/
├── README.md                    # Project entry point
├── cli.py                       # Command-line interface
├── smart_watcher.py             # Watcher control script
├── complete_setup.py            # Full system setup
├── pyproject.toml               # Python project config
│
├── core/                        # Core functionality
│   ├── ask.py                   # Question answering
│   ├── config.py                # Configuration management
│   ├── embedding.py             # Search and indexing
│   ├── extract.py               # Document processing
│   ├── index_manager.py         # Index lifecycle management
│   ├── path_utils.py            # Path validation and stats
│   └── llm.py                   # AI model interface
│
├── daemon/                      # Background services
│   └── watch.py                 # File watching daemon
│
├── ui/                          # User interfaces
│   ├── flask_app.py             # Flask web app
│   └── templates/               # HTML templates
│
├── docs/                        # Documentation
│   ├── guides/                  # User-facing guides
│   └── [project management]     # Dev documentation
│
├── tests/                       # Test suite
├── tools/                       # Development utilities
├── config/                      # Configuration files
├── prompts/                     # AI prompt templates
├── ai_search_docs/              # User documents
├── extracts/                    # Extracted text content
└── logs/                        # System logs
```

## Key Design Decisions

### 1. Local-First AI
- All processing happens locally (no cloud dependencies)
- Privacy-preserving: documents never leave the machine
- Phi-3-mini chosen for balance of quality and CPU inference speed

### 2. Two-Stage Retrieval
- **Stage 1**: FAISS semantic search finds relevant chunks
- **Stage 2**: LLM generates answer from retrieved context
- Relevance threshold (1.2) filters irrelevant queries

### 3. Citation Mapping
- Extracted text stored separately from originals
- Citations always point to user-accessible original files
- Priority mapping: PDF → DOCX → TXT → MD

### 4. Performance Optimization
- Batch processing for embeddings (512 chunks/batch)
- Singleton pattern for LLM model loading
- Speed presets: ultra_fast, fast, balanced, quality

## Configuration

See `core/config.py` for centralized configuration:

```python
LLM_CONFIG = {
    "max_tokens": 150,      # Answer length
    "temperature": 0.1,     # Determinism
    "n_ctx": 1536,          # Context window
    "n_threads": 8,         # CPU threads
}

SPEED_PRESETS = {
    "ultra_fast": {"max_tokens": 50, "temperature": 0.0},
    "fast": {"max_tokens": 150, "temperature": 0.1},
    "balanced": {"max_tokens": 200, "temperature": 0.3},
    "quality": {"max_tokens": 400, "temperature": 0.5},
}
```

## Performance Targets

| Metric | Target | Achieved |
|--------|--------|----------|
| Index Build | < 60s | 40.34s |
| Query Response | < 200ms | 17.4ms |
| Answer Generation | < 60s | ~63s (improved from 126s) |
| Chunks Processed | - | 7,670 |

### LLM Performance Optimizations (December 2025)

**Achieved 42% improvement** (126s → 63s first token time) through:

1. **Context Chunk Reduction** (5→3 chunks)
   - Reduced prompt processing load significantly
   - No quality degradation observed
   - Changed in `ui/flask_app.py` top_k parameter

2. **GPU Testing** (Intel Iris Xe iGPU)
   - CPU and GPU perform identically (~105-110s)
   - Root cause: UMA architecture (shared memory), 2GB reserved < 2.39GB model
   - Production uses CPU-only (GPU_LAYERS=0) for consistency

3. **Diagnostic Logging** (`core/ask.py`)
   - Added timing breakdown: LLM GET + first token + generation
   - Identified bottleneck: prompt processing (105s of 109s)
   - Singleton pattern confirmed working (0.00s-0.02s lookup)

4. **Benchmark Tool** (`tools/benchmark_models.py`)
   - Ollama-based multi-model comparison
   - Tests Phi-3.5, Qwen2.5 (1.5b/0.5b), Gemma2 (2b)
   - Enables speed/quality trade-off analysis

**Architecture Decision:** Keep llama-cpp-python for production stability, use Ollama for experimentation.
