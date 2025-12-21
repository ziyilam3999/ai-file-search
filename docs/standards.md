# Standards

File organization rules, coding conventions, and style guidelines for this project.

---

## 1. File Placement Rules

### Decision Tree for New Files

```
NEW FILE: filename.py/md/toml
├── Is it README.md?
│   └── YES → README.md (root)
├── Is it other documentation? (.md)
│   └── YES → docs/filename.md
├── Is it configuration? (.toml, .yaml, .json config)
│   └── YES → config/filename.toml
├── Does filename start with "test_"?
│   └── YES → tests/filename.py
├── Is it a debug/bench/analyze/tool script?
│   └── YES → tools/filename.py
├── Is it core system functionality?
│   └── YES → core/filename.py
├── Is it user interface related?
│   └── YES → ui/filename.py
├── Is it a background service/daemon?
│   └── YES → daemon/filename.py
├── Is it a user command? (setup_, switch_, cli_)
│   └── YES → filename.py (root)
└── DEFAULT → tools/filename.py
```

### Clean Root Strategy

**ROOT = ESSENTIAL ONLY** (Max ~15 files)
- **User Commands**: cli.py, setup_*.py, switch_*.py
- **Main Documentation**: README.md ONLY
- **Critical Data**: index.faiss, meta.sqlite
- **Project Config**: pyproject.toml, poetry.toml

### Organized Folders

| Folder | Contents |
|--------|----------|
| `docs/` | All documentation (except README.md) |
| `config/` | All configuration files |
| `tests/` | All test files |
| `tools/` | All development utilities |
| `core/` | Core system modules |
| `ui/` | User interface components |
| `daemon/` | Background services |

### Correct Placements

| File | Location | Reason |
|------|----------|--------|
| `README.md` | root | Main project documentation |
| `cli.py` | root | User command |
| `PROJECT_STRUCTURE.md` | `docs/` | Documentation |
| `API_SPECIFICATION.md` | `docs/` | Documentation |
| `project_config.toml` | `config/` | Configuration |
| `test_new_feature.py` | `tests/` | Test file |
| `debug_performance.py` | `tools/` | Development tool |
| `new_module.py` | `core/` | Core functionality |

### Incorrect Placements

| Wrong | Correct |
|-------|---------|
| `PROJECT_STRUCTURE.md` (root) | `docs/PROJECT_STRUCTURE.md` |
| `project_structure.toml` (root) | `config/project_structure.toml` |
| `tests/unit/test_feature.py` | `tests/test_feature.py` |
| `tools/scripts/debug.py` | `tools/debug.py` |
| `src/anything.py` | Use appropriate folder |
| `test_feature.py` (root) | `tests/test_feature.py` |

### Never Create These Folders

- `tests/unit/`
- `tests/integration/`
- `tools/scripts/`
- `src/`
- `data/`

### Never Move These Files

- `README.md` (main project doc)
- `index.faiss` (search index)
- `meta.sqlite` (database)
- `cli.py` (main user command)
- `pyproject.toml` (Python project config)

---

## 2. Coding Conventions

### Emoji-Free Code Requirement

**CRITICAL**: This codebase MUST remain emoji-free for cross-platform compatibility.

#### Rationale

1. **Cross-Platform Compatibility**: Emoji characters cause encoding issues in subprocess calls across Windows/Mac/Linux
2. **Professional Standards**: Text-based indicators are more professional and accessible
3. **Subprocess Reliability**: Prevents Unicode encoding errors in terminal operations
4. **AI Agent Compatibility**: Ensures consistent behavior across different AI development environments

#### Prohibited Characters

**NEVER USE** emoji characters in any code files:
- No Unicode emoticons (happy face, rocket, checkmark, X, etc.)
- No symbol pictographs (wrench, folder, computer, etc.)
- No status indicators using emoji

#### Required Text Replacements

| Instead of Emoji | Use Text |
|------------------|----------|
| checkmark | `SUCCESS:` or `COMPLETED:` |
| X mark | `ERROR:` or `FAILED:` |
| rocket | `STARTING:` or `LAUNCHING:` |
| folder | `FOLDER:` or `DIRECTORY:` |
| document | `FILE:` |
| wrench | `CONFIGURING:` or `SETUP:` |
| computer | `SYSTEM:` or `PROCESSING:` |
| target | `TARGET:` or `FOCUS:` |
| memo | `NOTE:` or `INFO:` |
| warning | `WARNING:` |
| magnifying glass | `SEARCHING:` or `ANALYZING:` |

#### Code Examples

**INCORRECT** (with emoji):
```python
print("rocket Starting file watcher...")
logging.info("checkmark Index created successfully")
raise Exception("X mark Failed to load model")
```

**CORRECT** (emoji-free):
```python
print("STARTING: File watcher...")
logging.info("SUCCESS: Index created successfully")
raise Exception("ERROR: Failed to load model")
```

#### File Types Covered

This requirement applies to ALL text files:
- Python files (*.py)
- Markdown files (*.md)
- Configuration files (*.yaml, *.yml, *.json)
- Text files (*.txt)
- Documentation files

---

## 3. Quick Checklist

Before creating any file:

- [ ] Is this documentation? → `docs/`
- [ ] Is this configuration? → `config/`
- [ ] Is this a test? → `tests/`
- [ ] Is this a tool/utility? → `tools/`
- [ ] Is this a user command? → Root (if essential)
- [ ] Does this belong in root? → Probably NO!
- [ ] Are there any emoji characters? → Remove them!

---

*Last Updated: 2025-12-21*
