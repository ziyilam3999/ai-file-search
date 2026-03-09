# AI File Search — Application Overview

AI File Search is a local-first, AI-powered semantic document search system. It lets users ask natural-language questions about their documents and receive concise, cited answers — all running offline with local AI models.

## Key Features

- **Semantic search** — find documents by meaning, not just keywords
- **AI-generated answers** — concise responses with numbered citations back to source files
- **Real-time file watching** — new/modified documents are automatically indexed in the background
- **Multiple interfaces** — desktop app (Flask + PyWebView), CLI, and REST API
- **Offline operation** — all AI inference runs locally; no cloud API keys required
- **Confluence integration** — optionally sync and search Confluence wiki pages
- **Speed presets** — tune the quality/speed tradeoff (ultra_fast, fast, balanced, quality)
- **Supported formats** — PDF, DOCX, TXT, and Markdown

## Architecture

```
 ┌─────────────────────┐
 │   User Documents     │  PDF, DOCX, TXT, MD files
 │   ai_search_docs/    │  (or custom watch paths)
 └────────┬────────────┘
          │  watchdog (real-time)
          ▼
 ┌─────────────────────┐
 │   daemon/watch.py    │  Detects file create/modify/delete events
 │   File Watcher       │  Debounces duplicates, queues changes
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │   core/extract.py    │  Extracts plain text from each file format
 │   Text Extraction    │  (pdfminer, python-docx, direct read)
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │  daemon/             │  Splits text into 400-word chunks (25-word overlap)
 │  embedding_adapter   │  Embeds chunks with sentence-transformers
 │                      │  Stores vectors in FAISS, metadata in SQLite
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │  index.faiss         │  FAISS vector index (384-dim, L2 distance)
 │  meta.sqlite         │  SQLite metadata (file, chunk text, page, URL)
 └────────┬────────────┘
          │
          │  User asks a question
          ▼
 ┌─────────────────────┐
 │  core/embedding.py   │  Embeds the query, searches FAISS for top-k chunks
 │  Vector Search       │  Returns ranked chunks with relevance scores
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │  core/ask.py         │  Assembles retrieved chunks into a prompt
 │  RAG Pipeline        │  Sends prompt + context to local LLM
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │  core/llm.py         │  Qwen2.5-1.5B (GGUF, via llama-cpp-python)
 │  Local LLM           │  Generates concise answer with citations
 └────────┬────────────┘
          │
          ▼
 ┌─────────────────────┐
 │  Answer + Citations  │  Displayed in desktop UI, CLI, or API response
 └─────────────────────┘
```

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Embedding model | sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Vector index | FAISS (IndexFlatL2 with IndexIDMap) |
| Metadata store | SQLite |
| Local LLM | Qwen2.5-1.5B-Instruct (Q4_K_M GGUF) via `llama-cpp-python` |
| Web framework | Flask |
| Desktop wrapper | PyWebView |
| File monitoring | watchdog |
| Task scheduling | APScheduler |
| PDF extraction | pdfminer.six |
| DOCX extraction | python-docx |
| Confluence API | atlassian-python-api |
| Dependency management | Poetry |
| Testing | pytest |

## Core Modules

### `core/embedding.py` — Vector Search

Manages the FAISS index and sentence-transformer model. Key responsibilities:

- Loads and caches the `all-MiniLM-L6-v2` model (384-dimensional embeddings)
- Splits document text into chunks (400 words, 25-word overlap)
- Embeds chunks and adds them to a FAISS `IndexIDMap` (supports incremental add/remove)
- Queries the index for top-k most similar chunks given a question embedding
- Returns results as `(chunk_text, file_path, chunk_id, doc_chunk_id, score)` tuples

### `core/llm.py` — Local LLM

Wraps `llama-cpp-python` for local inference with the Qwen2.5-1.5B model:

- Singleton pattern — model loaded once and reused across requests
- Warm-start priming on initialization to eliminate first-call latency
- Supports both streaming (token-by-token) and non-streaming generation
- Default config: 100 max tokens, temperature 0.1, 2048 context window, 8 CPU threads
- GPU offloading available via `GPU_LAYERS` environment variable

### `core/ask.py` — RAG Pipeline

Orchestrates the full retrieval-augmented generation flow:

1. Embeds the user's question
2. Retrieves top-k relevant chunks from FAISS (default k=5, relevance threshold 1.2)
3. Formats chunks as numbered context `[1]`, `[2]`, etc.
4. Sends the prompt (from `prompts/retrieval_prompt.md`) with context to the LLM
5. Returns the answer string and a list of citation objects (file, page, score, preview)
6. Falls back to context-based answers if the LLM is unavailable

### `core/extract.py` — Text Extraction

Converts document files to plain UTF-8 text:

- **PDF**: pdfminer.six
- **DOCX**: python-docx (paragraph extraction)
- **TXT / MD**: direct read with UTF-8, fallback to Latin-1

### `core/database.py` — Metadata Storage

SQLite database (`meta.sqlite`) storing chunk metadata:

- Schema: `id`, `file`, `chunk`, `doc_chunk_id`, `source_url`
- Context-manager based connection pooling
- Methods for file lookup, record counts, and incremental deletion

### `core/config.py` — Configuration

Single source of truth for paths, LLM settings, and performance presets:

- Path constants: `index.faiss`, `meta.sqlite`, `ai_search_docs/`, `extracts/`, `logs/`
- LLM config: max_tokens, temperature, n_ctx, n_threads, n_batch, n_gpu_layers
- Speed presets: `ultra_fast` (50 tokens), `fast` (150), `balanced` (200), `quality` (400)
- Embedding config: chunk_size=400, chunk_overlap=25, words_per_page=300
- Citation display config

### `core/confluence.py` — Confluence Integration

Syncs Confluence Cloud wiki pages into the search index:

- Authenticates via email + API token
- Fetches pages with HTML-to-text conversion (BeautifulSoup)
- Tracks page hierarchy and version for incremental sync
- Stores `source_url` in the database for direct linking back to Confluence

## Daemon Services

### `daemon/watch.py` — File Watcher

Real-time file system monitoring using watchdog:

- Watches configured directories for file create/modify/delete events
- Debounces duplicate events and batches changes
- Processes changes through extraction and incremental indexing
- APScheduler runs nightly full re-indexing
- Configurable include/exclude patterns via `prompts/watcher_config.yaml`

### `daemon/embedding_adapter.py` — Incremental Indexer

Background embedding processor that keeps the FAISS index in sync:

- Adds new documents via `add_documents_batch()` without full rebuilds
- Thread-locked operations for concurrent safety
- Tracks statistics: documents added, removed, failures
- Pre-warms the embedding model on initialization

### `daemon/file_queue.py` — Change Queue

Thread-safe queue for file change events with deduplication.

## User Interfaces

### Desktop App (`run_app.py`)

The primary interface. Startup sequence:

1. Configures logging, loads user config
2. Checks for updates (non-blocking)
3. Ensures the file watcher is running
4. Starts Flask on port 5001 in a background thread
5. Pre-loads AI models (embedding + LLM) in a background thread
6. Opens a native PyWebView window pointing at the Flask server

The web UI features:

- **Chat interface** with conversation history (stored in localStorage)
- **Streaming answers** — tokens render in real time via Server-Sent Events
- **Status bar** — watcher status, document count, indexing progress
- **Activity sidebar** — real-time system events (model loading, indexing, etc.)
- **Settings page** — manage watch paths, trigger reindexing, configure Confluence
- **Setup wizard** — first-run flow for Confluence credentials
- **Dark theme** throughout

### CLI (`cli.py`)

Terminal-based search:

```
python cli.py "Who is Alice?"           # Single question
python cli.py --interactive             # Interactive mode
python cli.py sync-confluence --space KEY  # Sync Confluence
python cli.py confluence-status         # Check connection
```

Options: `--verbose`, `--citations`, `--no-llm`, `--interactive`

### REST API (`ui/flask_app.py`)

Flask endpoints available at `http://localhost:5001`:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/search/stream` | Streaming search (SSE) |
| POST | `/search` | Non-streaming search |
| GET | `/api/status` | Watcher status, doc/index counts |
| GET | `/api/activity` | Recent system activity events |
| GET | `/api/preload-status` | Model loading progress |
| GET | `/api/version` | Version and update info |
| GET/POST | `/api/settings/watch-paths` | Manage watched directories |
| DELETE | `/api/settings/watch-paths` | Remove a watch path |
| POST | `/api/settings/reindex` | Trigger full reindex |
| POST | `/api/open-file` | Open a local file or Confluence page |
| POST | `/api/browse-folder` | Native folder picker dialog |
| GET/POST | `/api/user-config` | User configuration |
| POST | `/api/user-config/confluence` | Save Confluence credentials |
| GET | `/api/confluence/status` | Confluence connection status |
| GET | `/api/confluence/spaces` | List accessible spaces |
| POST | `/api/confluence/sync` | Start space sync (async) |
| GET | `/api/jobs/<job_id>` | Background job status |
| GET | `/api/jobs` | List all background jobs |

## Entry Points

| Command | Purpose |
|---|---|
| `python run_app.py` | Launch the desktop app |
| `python cli.py "question"` | Search from the terminal |
| `python smart_watcher.py start` | Start the file watcher daemon |
| `python smart_watcher.py stop` | Stop the file watcher daemon |
| `python smart_watcher.py status` | Check watcher status |
| `python complete_setup.py` | One-time setup (downloads models, builds index) |
| `python switch_documents.py discover` | Discover document categories |
| `python setup_auto_discovery.py` | Configure auto-discovery |

## Configuration

### Config Files

| File | Purpose |
|---|---|
| `core/config.py` | Path constants, LLM settings, speed presets |
| `prompts/watcher_config.yaml` | Watch paths and file include/exclude patterns |
| `prompts/retrieval_prompt.md` | RAG system prompt template |
| `config/confluence.yaml` | Confluence config template |
| `.env` / `.env.example` | Confluence API credentials |

### User Config Directory

Platform-specific user settings (credentials, preferences):

- **Windows**: `%APPDATA%/ai-file-search/`
- **macOS**: `~/Library/Application Support/ai-file-search/`
- **Linux**: `~/.config/ai-file-search/`

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `GPU_LAYERS` | Number of LLM layers offloaded to GPU (0=CPU, 99=full GPU) | `0` |
| `CONFLUENCE_URL` | Confluence Cloud instance URL | — |
| `CONFLUENCE_EMAIL` | Confluence account email | — |
| `CONFLUENCE_API_TOKEN` | Confluence API token | — |

## Project Structure

```
ai-file-search/
├── cli.py                  # CLI entry point
├── run_app.py              # Desktop app launcher
├── smart_watcher.py        # Watcher daemon controller
├── run_watcher.py          # Watcher entry point
├── complete_setup.py       # One-time setup script
├── switch_documents.py     # Document category management
├── setup_auto_discovery.py # Auto-discovery setup
├── core/                   # Core library modules
│   ├── ask.py              #   RAG pipeline
│   ├── embedding.py        #   FAISS vector search
│   ├── llm.py              #   Local LLM wrapper
│   ├── extract.py          #   Text extraction
│   ├── database.py         #   SQLite metadata
│   ├── config.py           #   Configuration
│   ├── confluence.py       #   Confluence client
│   ├── index_manager.py    #   Index lifecycle
│   ├── monitoring.py       #   System monitoring
│   ├── user_config.py      #   User settings
│   ├── path_utils.py       #   Path utilities
│   ├── utils.py            #   General utilities
│   └── version.py          #   Version management
├── daemon/                 # Background services
│   ├── watch.py            #   File watcher
│   ├── embedding_adapter.py#   Incremental indexer
│   └── file_queue.py       #   Change event queue
├── ui/                     # Web UI
│   ├── flask_app.py        #   Flask backend + API
│   ├── templates/          #   HTML templates
│   ├── static/             #   CSS + JavaScript
│   ├── app.py              #   Legacy Streamlit app
│   └── components.py       #   Legacy UI components
├── prompts/                # AI prompt templates
├── config/                 # Config templates
├── tests/                  # Test suite (pytest)
├── tools/                  # Dev utilities
├── docs/                   # Documentation
├── ai_search_docs/         # Default document directory
├── ai_models/              # Downloaded AI models
├── pyproject.toml          # Python project config (Poetry)
└── poetry.lock             # Dependency lock file
```
