# Refactoring

Technical debt and cleanup tasks.

## Active Technical Debt

| ID | Description | Priority | Effort | Status |
|----|-------------|----------|--------|--------|
| TD-017 | Code Duplication: SQLite/FAISS/Model loading scattered across modules | Critical | High | Completed |
| TD-018 | Architectural Violations: Empty src/ folder, misplaced root scripts | High | Low | Completed |
| TD-019 | Code Complexity: daemon/watch.py is 1157 lines (God file) | Medium | High | Completed |
| TD-020 | Inconsistent Path Constants: Tools hardcode paths instead of using config | Medium | Medium | Completed |
| TD-021 | Model Caching Inconsistency: Multiple SentenceTransformer instances | Medium | Medium | Completed |
| TD-022 | Type Annotation Gaps in daemon/watch.py | Low | Low | Not Started |
| TD-001 | EmbeddingAdapter uses mock instead of real incremental updates | Medium | High | Not Started |
| TD-002 | PRD_v0.4.docx should be converted to Markdown | Low | Low | Not Started |

## Completed Refactoring

| ID | Description | Completed |
|----|-------------|-----------|
| TD-017 | Database Management: Create DatabaseManager class to centralize SQLite operations | 2025-12-23 |
| TD-019 | Code Complexity: Split daemon/watch.py (1159→696 lines) into focused modules | 2025-12-23 |
| TD-021 | Model Caching: Consolidate SentenceTransformer loading via Embedder singleton | 2025-12-23 |
| TD-020 | Path Constants: Replace 25+ hardcoded paths with DATABASE_PATH/INDEX_PATH | 2025-12-23 |
| TD-018 | Architectural Violations: Delete empty src/ folder, move debug/test scripts to tools/ | 2025-12-23 |
| TD-016 | Refactor core/utils.py to decouple HTML generation from citation formatting | 2025-12-22 |
| TD-015 | Refactor ui/app.py into modular components (styles, components) | 2025-12-22 |
| TD-014 | Extract monitoring logic to core/monitoring.py and clean up JS | 2025-12-21 |
| TD-013 | Refactor daemon module for better configuration usage and code cleanup | 2025-12-21 |
| TD-012 | Centralize AI model paths in config.py and clean up extract.py | 2025-12-21 |
| TD-011 | Update .gitignore to match copilot-instructions.md standards | 2025-12-21 |
| TD-003 | Migrate milestones.yml to progress.md | 2025-12-21 |
| TD-004 | Centralize LLM configuration in config.py | 2025-08-03 |
| TD-005 | Standardize folder naming (sample_docs → ai_search_docs) | 2025-09-08 |
| TD-006 | Fix all mypy type annotations | 2025-08-03 |
| TD-007 | Remove duplicate backup logic in watch.py | 2025-09-06 |
| TD-008 | Remove emoji characters from quick_test.py | 2025-12-21 |
| TD-009 | Centralize path constants (INDEX_PATH, DATABASE_PATH) in config.py | 2025-12-21 |
| TD-010 | Refactor embedding.py to use config.py path constants | 2025-12-21 |

### TD-001: Real Incremental Index Updates

**Current State:**
- `EmbeddingAdapter` in `daemon/watch.py` uses mock incremental updates
- Full index rebuild required for actual changes

**Target State:**
- Implement `add_single_document()`, `update_single_document()`, `remove_single_document()` in Embedder
- Real-time index updates (<1 second per file)

**Effort:** High (estimated 1-2 days)

### TD-002: Convert PRD to Markdown

**Current State:**
- Product requirements in `PRD_v0.4.docx` (Word format)
- Not version-control friendly

**Target State:**
- Convert to `requirements.md` with structured tables
- Reference original Word file for historical purposes

**Effort:** Low (estimated 1 hour)

---

## Refactoring Plan (2025-12-23 Review)

### TD-017: Code Duplication Issues (Critical) - ✅ COMPLETED

**Previous State:**
- SQLite connections scattered across 3 core modules with duplicate connection code
- Each module opened/closed connections independently
- No consistent error handling or transaction management

**Actions Taken:**
1. ✅ Created `core/database.py` with `DatabaseManager` class (247 lines)
   - Context manager pattern for safe connection handling
   - Singleton pattern via `get_db_manager()` function
   - 15+ helper methods: `execute_query()`, `fetch_all()`, `fetch_one()`, `ensure_table_exists()`, etc.
2. ✅ Refactored `core/config.py` - replaced direct sqlite3 connection
3. ✅ Refactored `core/embedding.py` - removed 3 sqlite3.connect() calls
4. ✅ Refactored `daemon/embedding_adapter.py` - removed 4 sqlite3.connect() calls
5. ✅ Removed unused sqlite3 imports from all refactored modules

**Result:**
- All SQLite operations now centralized through DatabaseManager
- Consistent error handling and transaction management
- Reduced code duplication (DRY principle)
- Easier to maintain and test database operations

**Effort:** 4 hours

---

### TD-018: Architectural Violations (High)

**Current State:**
- Empty `src/search/` folder exists (violates standards.md "Never Create These Folders")
- `debug_retrieval.py` in root (should be in tools/)
- `quick_test.py` in root (should be in tools/)

**Target State:**
- Delete `src/` folder entirely
- Move `debug_retrieval.py` → `tools/debug_retrieval.py`
- Move `quick_test.py` → `tools/quick_test.py`

**Effort:** Low (estimated 15 minutes)

**Steps:**
1. [x] Delete `src/` folder (empty)
2. [x] Move `debug_retrieval.py` to `tools/`
3. [x] Move `quick_test.py` to `tools/`
4. [x] Update any imports/references if needed

**Result:** Completed 2025-12-23. Root directory cleaned, standards.md compliance achieved.

---

### TD-019: Code Complexity in daemon/watch.py (Medium)

**Current State:**
- `daemon/watch.py` is 1157 lines - a "God file"
- Contains 4 major classes: `EmbeddingAdapter`, `FileChangeQueue`, `FileChangeHandler`, `FileWatcher`
- Difficult to test, maintain, and understand

**Target State:**
Split into focused modules:
```
daemon/
├── __init__.py           # Public exports
├── watcher.py            # FileWatcher (orchestration) ~300 lines
├── embedding_adapter.py  # EmbeddingAdapter ~200 lines
├── file_queue.py         # FileChangeQueue + FileChangeHandler ~150 lines
├── config_loader.py      # Configuration loading logic ~100 lines
└── scheduler.py          # APScheduler integration ~100 lines
```

**Effort:** High (estimated 4-6 hours)

**Steps:**
1. [x] Create `daemon/embedding_adapter.py` - extract EmbeddingAdapter class
2. [x] Create `daemon/file_queue.py` - extract FileChangeQueue + FileChangeHandler
3. [x] Refactor `daemon/watch.py` to import from new modules
4. [x] Update `daemon/__init__.py` with public exports
5. [x] Run all tests to verify no regressions
6. [ ] Update imports in `smart_watcher.py`, `run_watcher.py` (if needed)

**Result:** Completed 2025-12-23. daemon/watch.py reduced from 1159 to 696 lines (40% reduction).

**New Structure:**
- `daemon/watch.py` - 696 lines (FileWatcher orchestration)
- `daemon/embedding_adapter.py` - 358 lines (EmbeddingAdapter)
- `daemon/file_queue.py` - 136 lines (FileChangeQueue + Handler)
- `daemon/__init__.py` - Updated with public exports

---

### TD-020: Inconsistent Path Constants Usage (Medium)

**Current State:**
- Tools hardcode `"meta.sqlite"` and `"index.faiss"` instead of using config constants
- Inconsistent with `core/` modules which use `DATABASE_PATH` and `INDEX_PATH`

**Affected Files:**
- `tools/monitor_file_processing.py` - uses "index.faiss"
- `tests/test_regression.py` - uses "index.faiss"
- All files listed in TD-017 for "meta.sqlite"

**Target State:**
- All files import and use `DATABASE_PATH`, `INDEX_PATH` from `core/config.py`

**Effort:** Medium (estimated 2 hours)

**Steps:**
1. [x] Update each tool file to import from `core.config`
2. [x] Replace hardcoded strings with constants
3. [x] Run tests to verify no regressions
4. [ ] Add pre-commit hook to detect hardcoded path strings (optional)

**Result:** Completed 2025-12-23. All tools now use centralized path constants.

---

### TD-021: Model Caching Inconsistency (Medium)

**Current State:**
- `core/embedding.py` uses `_MODEL_CACHE` global singleton pattern
- `daemon/watch.py` `EmbeddingAdapter._pre_warm_model()` loads its own instance
- `daemon/watch.py` `_generate_embeddings()` loads yet another instance
- Result: Multiple model instances in memory (~500MB each)

**Affected Code:**
- `core/embedding.py:48` - `_MODEL_CACHE = SentenceTransformer(self.model_name)`
- `daemon/watch.py:114` - `model = SentenceTransformer(self.embedder.model_name)`
- `daemon/watch.py:260` - `model = SentenceTransformer(self.embedder.model_name)`

**Target State:**
- Single shared model instance via `Embedder._get_model()`
- `EmbeddingAdapter` calls `self.embedder._get_model()` instead of creating new instances

**Effort:** Medium (estimated 1-2 hours)

**Steps:**
1. [x] Make `Embedder._get_model()` a public method or add `get_model()` wrapper
2. [x] Update `EmbeddingAdapter._pre_warm_model()` to use `self.embedder._get_model()`
3. [x] Update `EmbeddingAdapter._generate_embeddings()` to use `self.embedder._get_model()`
4. [x] Remove duplicate `SentenceTransformer` imports in `daemon/watch.py`
5. [ ] Add memory usage test to verify single instance

**Result:** Completed 2025-12-23. Single model instance now shared across all components (~500MB memory savings).

---

### TD-022: Type Annotation Gaps (Low)

**Current State:**
- `daemon/watch.py` has vague type hints like `Optional[List]`
- Some functions lack return type annotations

**Affected Functions:**
- `_generate_embeddings() -> Optional[List]` should be `Optional[np.ndarray]`
- `_add_to_faiss_and_db()` - embeddings parameter is `List` but should be `np.ndarray`
- Various `Dict[str, Any]` could be more specific with TypedDict

**Target State:**
- Precise type annotations throughout `daemon/watch.py`
- mypy strict mode passes

**Effort:** Low (estimated 1 hour)

**Steps:**
1. [ ] Add numpy type hints: `np.ndarray` instead of `List`
2. [ ] Create TypedDict for stats and progress dictionaries
3. [ ] Run mypy --strict on daemon module
4. [ ] Fix any additional type errors

---

## Execution Priority

| Phase | Items | Total Effort | Description |
|-------|-------|--------------|-------------|
| **Phase 1** | TD-018 | 15 min | Quick wins: Delete empty folder, move misplaced files |
| **Phase 2** | TD-020, TD-021 | 3-4 hours | Path constants + model caching fixes |
| **Phase 3** | TD-019 | 4-6 hours | Split daemon/watch.py into modules |
| **Phase 4** | TD-017 | 4-6 hours | Create DatabaseManager, consolidate code |
| **Phase 5** | TD-022, TD-001, TD-002 | 2-3 hours | Type annotations + existing debt |

**Recommended Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

---

## Code Quality Metrics

| Metric | Status |
|--------|--------|
| Pre-commit hooks | All passing (black, isort, flake8, mypy) |
| Type annotations | 100% coverage in core modules |
| Test coverage | All tests passing |
| Code style | Emoji-free (cross-platform compatibility) |

## Refactoring Guidelines

When adding technical debt:
1. Document the reason for the quick fix
2. Estimate effort to properly refactor
3. Assign priority based on impact
4. Update this file when addressed

---

*Last Updated: 2025-12-23*
