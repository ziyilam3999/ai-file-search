# AI Agent Quick Reference - File Placement Rules

## 🎯 DECISION TREE (Copy-Paste for AI Agents)
NEW FILE: filename.py/md/toml ├── Is it README.md? │ └── YES → README.md (root) ✅ ├── Is it other documentation? (.md) │ └── YES → docs/filename.md ✅ ├── Is it configuration? (.toml, .yaml, .json config) │ └── YES → config/filename.toml ✅ ├── Does filename start with "test_"? │ └── YES → tests/filename.py ✅ ├── Is it a debug/bench/analyze/tool script? │ └── YES → tools/filename.py ✅
├── Is it core system functionality? (ask, embedding, extract) │ └── YES → core/filename.py ✅ ├── Is it user interface related? │ └── YES → ui/filename.py ✅ ├── Is it a background service/daemon? │ └── YES → daemon/filename.py ✅ ├── Is it a user command? (setup_, switch_, cli_) │ └── YES → filename.py (root) ✅ └── DEFAULT → tools/filename.py ✅

## 🧹 **CLEAN ROOT STRATEGY**

### ✅ **ROOT = ESSENTIAL ONLY** (Max ~15 files)
- **User Commands**: cli.py, setup_*.py, switch_*.py
- **Main Documentation**: README.md ONLY
- **Critical Data**: index.faiss, meta.sqlite
- **Project Config**: pyproject.toml, poetry.toml

### 📁 **ORGANIZED FOLDERS**
- **docs/** = All documentation (except README.md)
- **config/** = All configuration files  
- **tests/** = All test files
- **tools/** = All development utilities

## 📋 COMMON EXAMPLES

### ✅ CORRECT Placements:
- `README.md` (root) - Main project doc
- `cli.py` (root) - User command
- `docs/PROJECT_STRUCTURE.md` - Documentation  
- `docs/API_SPECIFICATION.md` - Documentation
- `config/project_structure.toml` - Configuration
- `tests/test_new_feature.py` - Test file
- `tools/debug_performance.py` - Development tool
- `core/new_module.py` - Core functionality

### ❌ INCORRECT Placements:
- `PROJECT_STRUCTURE.md` (root) → Use `docs/PROJECT_STRUCTURE.md`
- `project_structure.toml` (root) → Use `config/project_structure.toml`
- `API_GUIDE.md` (root) → Use `docs/API_GUIDE.md`
- `tests/unit/test_feature.py` → Use `tests/test_feature.py`
- `tools/scripts/debug.py` → Use `tools/debug.py`
- `src/anything.py` → Use appropriate folder
- `test_feature.py` (root) → Use `tests/test_feature.py`

## 🚫 NEVER CREATE THESE FOLDERS:
- `tests/unit/`
- `tests/integration/` 
- `tools/scripts/`
- `src/`
- `data/`

## 🚫 NEVER PUT IN ROOT:
- `PROJECT_STRUCTURE.md` → `docs/`
- `AI_AGENT_RULES.md` → `docs/`
- `BUILD_LOG.md` → `docs/`
- `USER_GUIDE.md` → `docs/`
- `project_structure.toml` → `config/`
- `settings.yaml` → `config/`

## 🔒 NEVER MOVE THESE FILES:
- `README.md` (main project doc)
- `index.faiss` (search index)
- `meta.sqlite` (database)
- `cli.py` (main user command)
- `smart_watcher.py` (essential user command)
- `pyproject.toml` (Python project config)

## 🎯 PATH TEMPLATES FOR AI AGENTS:

### New Documentation File:
```markdown
# Location: docs/<PURPOSE>.md
# AI File Search - <Document Title>

Content goes here...

## References
- Main documentation: [README.md](../README.md)
- Project structure: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
```

### New Configuration File:
```toml
# Location: config/<purpose>.toml
# Configuration for <purpose>

[section]
key = "value"
```

### New Test File:
```markdown
# Location: tests/test_<feature>.py
#!/usr/bin/env python3
"""Test suite for <feature>"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ... test code
```

### New Tool File:
```markdown
# Location: tools/<purpose>.py
#!/usr/bin/env python3
"""<Tool description>

Usage:
    python tools/<tool_name>.py [args]
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ... tool code
🤖 VALIDATION COMMANDS:
```
# Check project structure
python tools/validate_structure.py --scan

# Get guidance
python tools/validate_structure.py --guidance

# Suggest location for new file
python tools/validate_structure.py --suggest-location "your_file.py"

# Check if file is correctly placed
python tools/validate_structure.py --check-file "path/to/file.py"
📖 DOCUMENTATION REFERENCES:
Complete Guide: docs/PROJECT_STRUCTURE.md
Configuration: config/project_structure.toml
Main Project: README.md
🎯 QUICK CHECKLIST:
Before creating any file, ask:

✅ Is this documentation? → docs
✅ Is this configuration? → config
✅ Is this a test? → tests
✅ Is this a tool/utility? → tools
✅ Is this a user command? → Root (if essential)
✅ Does this belong in root? → Probably NO!
REMEMBER: Keep root clean and organized! 🧹✨