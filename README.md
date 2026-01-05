# AI File Search System

Zero-configuration smart document search system with automatic discovery and real-time indexing.

## Quick Start

1. **Complete Setup**: `python complete_setup.py`
2. **Start Watcher**: `python smart_watcher.py start`
3. **Launch App**: `python run_app.py`
4. **Search Documents**: `python cli.py "your search query"`

## Key Features

- **Zero Configuration**: Auto-discovers document categories
- **Smart Watcher**: Real-time file monitoring and indexing
- **Citation References**: Citations point to user-accessible files in `ai_search_docs/`
- **Multi-Format Support**: PDF, DOCX, TXT, and Markdown files
- **Modern UI**: Native desktop app with AI-powered answers
- **Background Processing**: File watcher runs as background service

## Project Structure

- 📋 **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Complete file organization guide
- 🤖 **[docs/AI_AGENT_RULES.md](docs/AI_AGENT_RULES.md)** - Quick reference for AI agents
- 🔧 **[config/project_structure.toml](config/project_structure.toml)** - Machine-readable configuration
- ✅ **Validator**: `python tools/validate_structure.py --guidance`

## Documentation

### User Guides
- 📖 **[docs/COMPLETE_USER_GUIDE.md](docs/COMPLETE_USER_GUIDE.md)** - Complete setup and usage
- 🚀 **[docs/QUICK_START.md](docs/QUICK_START.md)** - Quick start guide
- 🔍 **[docs/AUTO_DISCOVERY_GUIDE.md](docs/AUTO_DISCOVERY_GUIDE.md)** - Auto-discovery setup

### Development
- 🏗️ **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Project organization
- 🎨 **[docs/CODE_STYLE_GUIDELINES.md](docs/CODE_STYLE_GUIDELINES.md)** - Development guidelines
- 📝 **[docs/BUILD_LOG.md](docs/BUILD_LOG.md)** - Development history
- 🔌 **[docs/EMBEDDER_API_SPECIFICATION.md](docs/EMBEDDER_API_SPECIFICATION.md)** - API documentation

## System Requirements

- Python 3.12+
- 4GB+ RAM (for embedding processing)
- 2GB+ storage (for models and indexes)

## Installation & Setup

### Poetry Installation (Recommended)
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run complete setup
python complete_setup.py
```
Manual Installation
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies from pyproject.toml
pip install -e .

# Run complete setup
python complete_setup.py

Usage
File Watcher Control
python smart_watcher.py start      # Start background file monitoring
python smart_watcher.py stop       # Stop file monitoring
python smart_watcher.py status     # Check watcher status
python smart_watcher.py restart    # Restart watcher

Document Search
# Command line search
python cli.py "machine learning algorithms"

# Interactive desktop app
python run_app.py

Document Management
# Auto-discover new categories
python switch_documents.py discover

# View category status
python switch_documents.py status

# Enable specific category
python switch_documents.py enable research_papers

Index Management
# Rebuild search index
python -c "from core.embedding import Embedder; Embedder().build_index()"

# Quick system test
python tests/test_quick.py

Document Organization
The system automatically organizes documents in this structure:
ai_search_docs/               # Your documents (user-maintainable)
├── business_rules/
├── meeting_notes/
├── research_papers/
├── technical_docs/
└── user_manuals/

extracts/                  # Processed text (auto-generated)
├── business_rules/
└── ...

index.faiss               # Search index
meta.sqlite              # Document metadata

Testing & Validation
Quick Testing
# Comprehensive smoke test (5 tests, ~3 minutes)
python tests/test_quick.py

# Test specific components
python tests/test_embedding.py
python tests/test_extract.py
python tests/test_ask.py

Performance Testing
# Full regression testing
python tests/test_regression.py --verbose

# Performance benchmarking
python tests/bench_llm_performance.py

# Monitor live performance
python tools/live_monitor.py

Development Tools
# Validate project structure
python tools/validate_structure.py --scan

# Debug database contents
python tools/debug_db.py

# Check embedding format compliance
python tools/validate_embedder_format.py

# Monitor file processing
python tools/monitor_file_processing.py

Architecture
Core Processing: core - Embedding, extraction, and LLM modules
File Watching: watch.py - Real-time file monitoring
User Interface: ui - Streamlit-based web interface
CLI Interface: cli.py - Command-line search tool
Configuration: prompts - System prompts and configuration
Citation System
The system maintains a clean citation architecture:

User Documents: Store files in ai_search_docs/category/
Processing: System extracts text to extracts/category/
Search: Index built from extracted content
Citations: Results reference original files in ai_search_docs
This ensures users can always access and modify their original documents.

AI Model
Embedding Model: all-MiniLM-L6-v2 (384-dimensional vectors)
Language Model: Qwen2.5-1.5B-Instruct (2K context, Q4_K_M quantized)
Search Engine: FAISS with L2 distance indexing
Database: SQLite for metadata storage
Contributing
Read PROJECT_STRUCTURE.md for file organization
Follow CODE_STYLE_GUIDELINES.md for development
Use AI_AGENT_RULES.md for AI-assisted development
Validate structure: python [validate_structure.py](http://_vscodecontentref_/12) --guidance
Run tests: python tests/test_quick.py before committing