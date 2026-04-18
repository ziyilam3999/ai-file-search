# AI File Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/ziyilam3999/ai-file-search)](https://github.com/ziyilam3999/ai-file-search/releases)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)

Zero-configuration smart document search system with semantic search and AI-powered Q&A. Drop in your documents, ask questions in natural language, and get answers with citations.

## Features

- **Zero configuration** — Auto-discovers and categorizes documents
- **Semantic search** — Find documents by meaning, not just keywords
- **AI-powered Q&A** — Ask questions and get answers with source citations
- **Real-time indexing** — File watcher monitors for new and updated documents
- **Multi-format support** — PDF, DOCX, TXT, and Markdown

## Tech Stack

- **Python 3.12+** — Core language
- **Sentence Transformers** — all-MiniLM-L6-v2 for semantic embeddings
- **FAISS** — Vector similarity search
- **Qwen2.5-1.5B-Instruct** — Local LLM for Q&A (quantized, runs on CPU)
- **Flask / Streamlit** — Web UI
- **SQLite** — Document metadata storage
- **Watchdog** — Real-time file monitoring

## Quick Start

```bash
# Install dependencies
poetry install

# Run setup (downloads models, initializes indexes)
python complete_setup.py

# Start the file watcher
python smart_watcher.py start

# Search via CLI
python cli.py "your search query"

# Or launch the web UI
python run_app.py
```

## How It Works

```mermaid
graph TB
    D[Documents<br/>PDF · DOCX · TXT · MD] --> A[Auto-Discovery<br/>& Text Extraction]
    A --> E[Embedding<br/>all-MiniLM-L6-v2]
    E --> I[FAISS Index]
    Q[Query] --> S[Semantic Search]
    I --> S
    S --> T[Top Results]
    T --> L[LLM Q&A<br/>Qwen2.5-1.5B, local]
    L --> R[Answer + Citations]
```

1. **Drop documents** into `ai_search_docs/` (auto-organized by category)
2. **File watcher** detects changes and extracts text
3. **Embeddings** are generated and stored in a FAISS index
4. **Search** returns semantically similar documents
5. **Q&A mode** feeds top results to a local LLM for natural language answers with citations

## Usage

### File Watcher

```bash
python smart_watcher.py start      # Start background monitoring
python smart_watcher.py stop       # Stop monitoring
python smart_watcher.py status     # Check watcher status
```

### Document Management

```bash
python switch_documents.py discover   # Auto-discover new categories
python switch_documents.py status     # View category status
python switch_documents.py enable research_papers  # Enable a category
```

## System Requirements

- Python 3.12+
- 4GB+ RAM (for embedding model and LLM inference)
- 2GB+ storage (for models and indexes)

## License

MIT
