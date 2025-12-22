# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- **Interactive Citations:** Added "Open" button to citations in Streamlit UI to open source files in default system viewer.
- **Scenario E (Test Coverage Audit):** Added new scenario to `.github/copilot-instructions.md` for comprehensive test audits.
- **Standalone Desktop App:** New `run_app.py` launcher that wraps the UI in a native window using `pywebview`.
- **Unified Startup:** Launcher automatically starts the file watcher daemon if not running.
- **Streaming Support:** Added Server-Sent Events (SSE) to Flask backend for real-time answer generation.
- **System Status:** Added `/api/status` endpoint and UI status bar to monitor watcher health and file counts.
- **Shared Utilities:** Created `core/utils.py` for shared citation formatting logic.
- Documentation structure migration to standard format
- `docs/guides/` subfolder for user-facing documentation
- Path constants `INDEX_PATH`, `DATABASE_PATH`, `DOCUMENTS_DIR`, `EXTRACTS_DIR`, `LOGS_DIR`, `BACKUPS_DIR` in `core/config.py`
- Standardized `.gitignore` patterns for OS, IDE, and Python environment files

### Changed
- **Refactoring:** Split `ui/app.py` into `ui/styles.py` and `ui/components.py` for better maintainability.
- **Refactoring:** Moved `open_local_file` utility to `core/utils.py` for shared usage.
- **Testing:** Added `tests/test_ui_components.py` and updated `tests/test_core_utils.py` to cover new functionality.
- **Scenario C Enhancement:** Updated refactoring scenario to explicitly require adding unit tests for refactored functions.
- **Refactoring:** Cleaned up test suite by removing experimental `tests/test_simple_rag.py`.
- **Testing:** Added new unit tests `tests/test_core_utils.py` and `tests/test_core_config.py` to improve coverage.
- **Refactoring:** Extracted system monitoring logic from `tools/live_monitor.py` to `core/monitoring.py`.
- **Refactoring:** Updated `ui/flask_app.py` and `tools/live_monitor.py` to use the new `core/monitoring` module.
- **Refactoring:** Cleaned up `ui/static/js/new_search.js` by extracting stream reading logic into `readStreamResponse` method.
- Updated `.github/copilot-instructions.md` with stricter documentation-driven development protocols
- Moved user guides to `docs/guides/` directory
- Refactored `core/embedding.py` to use centralized path constants from `config.py`
- Refactored `core/llm.py` to use centralized `AI_MODELS_DIR` and `DEFAULT_MODEL_NAME` from `config.py`
- Cleaned up `core/extract.py` docstrings and removed TODOs
- Refactored `daemon/watch.py` to use centralized path constants (`DOCUMENTS_DIR`, `EXTRACTS_DIR`, `LOGS_DIR`)
- Improved configuration loading in `daemon/watch.py` to correctly merge defaults with YAML config
- Updated `tests/test_watch.py` to align with new configuration logic
- Refactored `core/config.py` to use `DATABASE_PATH` constant in `calculate_document_page()`

### Fixed
- **Performance:** Implemented in-memory caching for FAISS index and metadata to fix query latency regression (3.3s -> <200ms).
- **Integration Tests:** Fixed `test_search_finds_files_in_subfolders` by correctly patching paths and handling DB connections.
- **Stability:** Fixed `daemon/watch.py` to correctly save index to disk and invalidate cache on updates.
- **Robustness:** Added error handling for corrupted/missing `meta.sqlite` in `core/embedding.py`.
- Replaced emoji characters in `quick_test.py` with text-based indicators per `standards.md`

### Fixed
- Code style: Removed emoji violations for cross-platform compatibility

---

## [0.5.0] - 2025-09-08

### Added
- Real-time token streaming with visual feedback
- Blinking cursor animation during generation
- Dynamic citation highlighting with pulse animations
- Document-relative page calculations
- Glass morphism UI design

### Changed
- Database schema migrated to 4-column format with `doc_chunk_id`
- Page calculation algorithm using proportional positioning
- Calibrated words-per-page ratio for realistic page counts

### Fixed
- Peter Pan correctly shows pages 1-115 instead of impossible numbers
- Citation accuracy improved to 100%

---

## [0.4.2] - 2025-09-08

### Changed
- Token optimization: 100→150 tokens to prevent answer truncation
- Query time: ~46s (balanced speed vs completeness)

### Fixed
- Mid-sentence answer cutoffs eliminated

---

## [0.4.1] - 2025-09-08

### Changed
- Folder naming standardized: `sample_docs` → `ai_search_docs`
- Updated 23+ files, 200+ references across entire codebase

### Fixed
- Index rebuilt with proper citation mapping (7,670 chunks)
- Unicode filename matching with NFKC normalization

---

## [0.4.0] - 2025-09-06

### Added
- Intelligent original file mapping system (`_map_to_original_file()`)
- Priority-based file type detection (PDF→DOCX→TXT→MD)
- File existence validation before indexing

### Fixed
- Critical citation reference problem (extracts/ → ai_search_docs/)
- Index quality: 100% valid file references (was 92.7%)

---

## [0.3.2] - 2025-09-01

### Added
- Comprehensive regression test suite (6 test categories)
- Relevance threshold filtering (1.2 cosine distance)
- Automated test result logging (test_results_*.json)

### Fixed
- Citation hallucination issue (fake Investopedia references)
- FAISS/database synchronization

---

## [0.3.1] - 2025-08-10

### Added
- Performance configuration presets (ultra_fast, fast, balanced, quality)
- Minimal citation mode for UI speed
- Subdirectory support with recursive globbing

### Changed
- Centralized LLM configuration in `core/config.py`
- Token reduction: 225→100→150 tokens
- Temperature optimization: 0.35→0.1

### Fixed
- All mypy type annotation errors
- Pre-commit hook compatibility

---

## [0.3.0] - 2025-08-03

### Added
- APScheduler for nightly reindexing (2:00 AM)
- Pattern-based file filtering
- Comprehensive watcher configuration system

### Changed
- File watcher uses watchdog library
- Thread-safe event queue with deduplication
- Debounced batch processing (5-second default)

---

## [0.2.1] - 2025-07-15

### Added
- Streamlit web UI on localhost:8501
- Question input with AI-powered answer generation
- Citation display with file references
- Performance metrics sidebar
- Session state management

### Fixed
- Embedding format mismatch (4-tuple format)
- UI/core integration issues

---

## [0.2.0] - 2025-07-15

### Added
- Phi-3-mini-4k-instruct-q4.gguf integration
- Real AI-generated answers with citations
- Singleton pattern for model reuse
- Raw completion mode for RAG

### Fixed
- Garbled output via ChatML removal
- Prompt optimization (24 lines → 7 lines)

---

## [0.1.1] - 2025-07-14

### Added
- FAISS semantic search with all-MiniLM-L6-v2
- SQLite metadata storage
- Batch encoding (512 chunks/batch)

### Performance
- Build time: 40.34s (target: <60s)
- Query time: 17.4ms (target: <200ms)
- 3,037 chunks indexed

---

## [0.1.0] - 2024-12-XX

### Added
- Initial project setup with Poetry
- PDF extraction using pdfminer.six
- DOCX extraction using python-docx
- TXT/MD file processing
- Pre-commit hooks (black, isort, flake8, mypy)
- Loguru logging integration

---

*Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)*
