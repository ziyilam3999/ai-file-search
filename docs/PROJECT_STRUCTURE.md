# AI File Search - Project Structure Guide

## 📁 **File Organization Rules**

This document defines the standard file organization for AI agents and developers working on this project.

### 🎯 **Core Principles**
- **Clean Root Directory** - Only essential user commands and README
- **Single-Layer Organization** - Maximum 2 levels (folder/file.py)
- **Clear Purpose** - Each folder has obvious contents
- **Consistent Patterns** - Similar files go in the same place

---

## 📂 **Directory Structure**

📁 ai-file-search/ # Project root ├── 🎯 ESSENTIAL USER COMMANDS (Root) # ONLY files users run directly │ ├── README.md # Main project documentation │ ├── cli.py # Main search interface │ ├── smart_watcher.py # Watcher control │ ├── run_watcher.py # Simple watcher │ ├── complete_setup.py # Full system setup │ ├── setup_auto_discovery.py # Auto-discovery setup │ └── switch_documents.py # Category management │ ├── 💾 CORE DATA FILES (Root Level) # System-critical files │ ├── index.faiss # Search index (DO NOT MOVE) │ ├── meta.sqlite # Metadata database (DO NOT MOVE) │ ├── pyproject.toml # Python project config │ └── poetry.toml # Poetry configuration │ ├── 📂 core/ # Core functionality modules │ ├── init.py │ ├── ask.py # Question answering │ ├── config.py # Configuration management │ ├── embedding.py # Search and indexing │ ├── extract.py # Document processing │ └── llm.py # AI model interface │ ├── 📂 daemon/ # Background services │ ├── init.py │ └── watch.py # File watching daemon │ ├── 📂 ui/ # User interface components │ ├── init.py │ ├── app.py # Streamlit web app │ └── dashboard.py # Dashboard components │ ├── 📂 tests/ # 🆕 ALL TESTING FILES (SINGLE LAYER) │ ├── test_ask.py # Unit tests for core.ask │ ├── test_embedding.py # Unit tests for core.embedding │ ├── test_extract.py # Unit tests for core.extract │ ├── test_complete_system.py # Integration tests │ ├── test_regression.py # Regression test suite │ ├── test_quick.py # Quick smoke tests │ ├── test_config.yaml # Test configuration │ └── fixtures/ # Test data only │ ├── 📂 tools/ # 🆕 DEVELOPMENT UTILITIES (SINGLE LAYER) │ ├── debug_db.py # Database debugging │ ├── download_model.py # AI model downloader │ ├── extract_missing_files.py # File extraction utility │ ├── check_emoji_free.py # Code validation │ ├── bench_phi3_performance.py # Performance benchmarking │ ├── validate_structure.py # Project structure validator │ └── live_monitor.py # System monitoring │ ├── 📂 docs/ # 🆕 ALL DOCUMENTATION (ORGANIZED) │ ├── README.md # Documentation index │ ├── PROJECT_STRUCTURE.md # This file │ ├── AI_AGENT_RULES.md # Quick reference for AI agents │ ├── COMPLETE_USER_GUIDE.md # Complete user documentation │ ├── AUTO_DISCOVERY_GUIDE.md # Auto-discovery setup guide │ ├── QUICK_START.md # Quick start guide │ ├── CODE_STYLE_GUIDELINES.md # Development guidelines │ ├── BUILD_LOG.md # Build and development log │ └── EMBEDDER_API_SPECIFICATION.md # API documentation │ ├── 📂 config/ # 🆕 ALL CONFIGURATION FILES │ ├── project_structure.toml # AI agent configuration │ └── project_structure.toml # Template configurations │ ├── 📂 sample_docs/ # User document categories ├── 📂 extracts/ # Processed document extracts ├── 📂 prompts/ # AI prompts and templates ├── 📂 logs/ # System logs ├── 📂 ai_models/ # AI model files └── 📂 test_regression_results/ # Test output files

---

## 🤖 **AI Agent Guidelines**

### ✅ **When Creating New Files:**

#### **Tests** → Always use `tests/filename.py`
```python
# ✅ CORRECT
tests/test_new_feature.py
tests/test_performance.py
tests/test_integration_xyz.py

# ❌ INCORRECT
tests/unit/test_new_feature.py
tests/integration/test_performance.py
test_new_feature.py  # (in root)
```

Tools/Scripts → Always use tools/filename.py
```python
# ✅ CORRECT
tools/analyze_performance.py
tools/cleanup_database.py
tools/validate_system.py

# ❌ INCORRECT
tools/scripts/analyze_performance.py
tools/utilities/cleanup_database.py
analyze_performance.py  # (in root)
```
Documentation → Always use docs/filename.md (except README.md)
# ✅ CORRECT
docs/API_SPECIFICATION.md
docs/DEVELOPMENT_GUIDE.md
docs/USER_MANUAL.md

# ❌ INCORRECT
API_SPECIFICATION.md  # (in root)
guides/USER_MANUAL.md

Configuration → Always use config/filename.toml
# ✅ CORRECT
config/project_structure.toml
config/deployment.toml
config/settings.yaml

# ❌ INCORRECT
project_structure.toml  # (in root)
configs/settings.yaml

Core Functionality → Use appropriate module folder
# ✅ CORRECT
core/new_module.py      # Core system functionality
daemon/new_service.py   # Background services
ui/new_component.py     # User interface

# ❌ INCORRECT
new_module.py  # (in root, unless user-facing command)

🚫 DO NOT CREATE:
tests/unit/ subfolders
tests/integration/ subfolders
tools/scripts/ subfolders
src/ folders (reorganization remnant)
data/ folders (reorganization remnant)
Documentation files in root (except README.md)
Configuration files in root (except pyproject.toml, poetry.toml)
📍 Path References in Code:
Always use relative paths from project root:

# ✅ CORRECT
"tests/test_something.py"
"tools/utility_script.py" 
"core/module.py"
"docs/PROJECT_STRUCTURE.md"
"config/project_structure.toml"

# ❌ INCORRECT  
"../tests/test_something.py"
"./tools/utility_script.py"
"PROJECT_STRUCTURE.md"  # (if in docs/)

🎯 File Placement Decision Tree
Is it the main README?
YES → Root level (README.md only)
NO → Continue...
Is it a user-facing command?
YES → Root level (cli.py, setup_*.py, switch_*.py)
NO → Continue...
Is it documentation?
YES → docs/filename.md
NO → Continue...
Is it configuration?
YES → config/filename.toml
NO → Continue...
Is it a test file?
YES → tests/test_*.py
NO → Continue...
Is it a development/maintenance tool?
YES → tools/tool_name.py
NO → Continue...
Is it core system functionality?
YES → core/module.py
NO → Continue...
Is it a background service?
YES → daemon/service.py
NO → Continue...
Is it UI-related?
YES → ui/component.py
NO → Consider if it belongs in this project
🔒 Protected Files (DO NOT MOVE)
These files must stay in root for system compatibility:

README.md - Main project documentation
index.faiss - Search index (20+ files reference this)
meta.sqlite - Database (core system dependency)
cli.py - Main user interface
smart_watcher.py - Primary watcher
complete_setup.py - Setup entry point
switch_documents.py - User management tool
pyproject.toml - Python project configuration
poetry.toml - Poetry configuration
🧹 Clean Root Strategy
What Belongs in Root:
Essential User Commands (7 files max)
Main README.md (project entry point)
Critical Data Files (index.faiss, meta.sqlite)
Project Configuration (pyproject.toml, poetry.toml)
What Moves to Organized Folders:
All Documentation → docs (except README.md)
All Configuration → config (except essential project configs)
All Development Tools → tools
All Tests → tests
Benefits:
✅ Professional Appearance - Clean, focused root directory
✅ Easy Navigation - Users immediately see what they can run
✅ Better Organization - Related files grouped together
✅ Scalable Structure - Easy to maintain as project grows
📋 AI Agent Checklist
Before creating any new file, ask:

✅ Purpose: What does this file do?
✅ Audience: Who will use it? (Users, developers, system)
✅ Category: Test, tool, core, UI, docs, config, or user command?
✅ Location: Which folder based on the decision tree?
✅ Naming: Does the filename clearly indicate its purpose?
✅ Root Impact: Will this clutter the root directory?
Example Decision Process:
New File: "performance_benchmark.py"
1. Purpose: Measures system performance 
2. Audience: Developers/maintainers
3. Category: Development tool
4. Location: tools/
5. Final: tools/performance_benchmark.py ✅
6. Root Impact: No - keeps root clean ✅

🚀 Migration Status
✅ Completed: Single-layer structure implemented
✅ Completed: Clean root directory strategy
✅ Tests: Organized in flat tests/ folder
✅ Tools: Organized in flat tools/ folder
✅ Documentation: Organized in docs/ folder
✅ Configuration: Organized in config/ folder
🗑️ Cleanup: Remove reorganization remnants (src/, data/, nested folders)
Last Updated: September 2, 2025 Version: 1.1 - Clean root directory implementation