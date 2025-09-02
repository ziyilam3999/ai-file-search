# AI File Search System

Zero-configuration smart document search system with automatic discovery and real-time indexing.

## Quick Start

1. **Complete Setup**: `python complete_setup.py`
2. **Start Watcher**: `python smart_watcher.py start`
3. **Launch UI**: `python -m streamlit run ui/app.py`

## Key Features

- **Zero Configuration**: Auto-discovers document categories
- **Smart Watcher**: Real-time file monitoring and indexing
- **Cross-Platform**: Emoji-free codebase for reliable operation
- **Comprehensive Testing**: 100% test coverage validation
- **Modern UI**: Streamlit-based search interface

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

- Python 3.8+
- 4GB+ RAM (for embedding processing)
- 2GB+ storage (for models and indexes)

## Installation & Setup

### Option 1: Complete Zero-Config Setup (Recommended)
```bash
python complete_setup.py
```
Option 2: Manual Setup
# Install dependencies
pip install -r requirements.txt

# Download AI model
python tools/download_model.py

# Setup auto-discovery
python setup_auto_discovery.py

# Start smart watcher
python smart_watcher.py start
Usage
Basic Search
# Command line search
python cli.py "your search query"

# Web interface
python -m streamlit run ui/app.py
Document Management
# See available categories
python switch_documents.py discover

# Switch to specific category
python switch_documents.py research_papers

# Enable all categories
python switch_documents.py all

🧪 Testing & Validation
Comprehensive Test Suite
# Quick smoke testing (5 tests, ~3 minutes)
python tests/test_quick.py

# Full regression testing (6 categories, ~7 minutes)
python tests/test_regression.py --verbose

# Performance benchmarking
python tests/test_regression.py --performance-only

🎉 ALL TESTS PASSED! (6/6) ⏱️ Total execution time: 411.8 seconds 📊 Citation accuracy: 6/6 queries with authentic citations 🔍 Relevance filtering: 11/11 queries correctly classified

Development Tools
# Validate project structure
python tools/validate_structure.py --scan

# Debug database
python tools/debug_db.py

# Monitor performance
python tools/live_monitor.py
Contributing
Read PROJECT_STRUCTURE.md for file organization
Follow CODE_STYLE_GUIDELINES.md for development
Use AI_AGENT_RULES.md for AI-assisted development
Validate structure: python [validate_structure.py](http://_vscodecontentref_/29) --guidance

These are all the files that need updates. Each file now:

1. **Enforces clean root directory** - only essential files in root
2. **Uses proper organized paths** - docs/, config/, tests/, tools/
3. **Provides clear guidance** for AI agents
4. **Maintains consistency** across all documentation
5. **Includes validation tools** to enforce the structure

The structure now clearly separates:
- **Root**: Essential user commands + main README + critical data
- **docs/**: All documentation 
- **config/**: All configuration files
- **tests/**: All test files
- **tools/**: All development utilities

This creates a much cleaner and more professional project structure! 🎉