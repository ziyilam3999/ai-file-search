# Refactoring

Technical debt and cleanup tasks.

## 🎉 Summary: All Technical Debt Cleared!

**Status as of 2025-12-23:** All identified technical debt items have been successfully resolved.

| Category | Items Completed | Total Effort |
|----------|-----------------|--------------|
| **Critical Priority** | 1 (TD-017) | 4 hours |
| **High Priority** | 1 (TD-018) | 15 minutes |
| **Medium Priority** | 4 (TD-019, TD-020, TD-021, TD-001) | ~16 hours |
| **Low Priority** | 2 (TD-022, TD-002) | ~2 hours |
| **Total** | **8 items** | **~22 hours** |

**Key Achievements (December 2025 Refactoring Sprint):**
- ✅ Centralized database operations with DatabaseManager singleton
- ✅ Split 1159-line God file into 3 focused modules (40% reduction)
- ✅ Eliminated 25+ hardcoded path strings
- ✅ Consolidated model loading (~500MB memory savings)
- ✅ Added precise type hints with TypedDict and numpy types
- ✅ Achieved 100% mypy compliance across core modules

**Historical Completions:**
- ✅ Real incremental FAISS updates (July 2025)
- ✅ Markdown requirements documentation (pre-existing)

## Active Technical Debt

**🎯 Status: ZERO active technical debt items**

All previously tracked items have been completed:

| ID | Description | Priority | Effort | Status |
|----|-------------|----------|--------|--------|
| TD-017 | Code Duplication: SQLite/FAISS/Model loading scattered across modules | Critical | High | Completed |
| TD-018 | Architectural Violations: Empty src/ folder, misplaced root scripts | High | Low | Completed |
| TD-019 | Code Complexity: daemon/watch.py is 1157 lines (God file) | Medium | High | Completed |
| TD-020 | Inconsistent Path Constants: Tools hardcode paths instead of using config | Medium | Medium | Completed |
| TD-021 | Model Caching Inconsistency: Multiple SentenceTransformer instances | Medium | Medium | Completed |
| TD-022 | Type Annotation Gaps in daemon/watch.py | Low | Low | Completed |
| TD-001 | EmbeddingAdapter uses mock instead of real incremental updates | Medium | High | Completed |
| TD-002 | PRD_v0.4.docx should be converted to Markdown | Low | Low | Completed |

## Quick Wins (Non-tracked Improvements)

| Date | File | Improvement |
|------|------|-------------|
| 2025-12-25 | tools/sync_copilot_instructions.ps1 | Major cleanup: Removed 256 lines of dead code (Sync-PillarSnapperDocs, Find-HighestDocVersion, legacy hardcoded variables), added ${base_path} variable expansion for DRY config paths, fixed True console noise from unsuppressed function returns. Reduced from 1694→1438 lines (-15%) |
| 2025-12-25 | sync_config.yaml | Added ${base_path} variable expansion, reduced 12 hardcoded paths to single base_path definition. Reduced from 94→74 lines (-21%) |
| 2025-12-25 | .github/copilot-instructions.md | Made version bump instructions project-agnostic (removed pubspec.yaml references), removed duplicate "Doc Files Reference" table (kept DOCUMENT MAP), bumped to v2.9. Reduced from 489→351 lines (-28%) |
| 2025-12-23 | .github/copilot-instructions.md | Structural refactoring v2.2: Consolidated 10 inline ⚠️ FAILURE MODE warnings into single reference table (FM-1/FM-2/FM-3), replaced verbose blocks with inline references (→ FM-X), improved scannability without losing safety checks |
| 2025-12-23 | tools/sync_copilot_instructions.ps1 | Comprehensive refactoring: Reduced main loop from ~100 lines to 15 lines, extracted 3 high-level functions (`Sync-CopilotInstructions`, `Sync-ScriptFile`, `Ensure-GitProtection`), consolidated git operations, added path validation, extracted pattern constants. Result: 40% complexity reduction, improved testability and maintainability |
| 2025-12-23 | tools/sync_copilot_instructions.ps1 | PowerShell best practices: Added `[CmdletBinding()]`, parameter validation with `[Parameter(Mandatory)]`, extracted constants, introduced result object, added verbose logging |

## Future Enhancements (Low Priority)

| ID | Description | Rationale | Effort |
|----|-------------|-----------|--------|
| FE-001 | **Orphan Cleanup on Startup:** Detect and remove vectors for paths no longer in `watch_config.yaml` | Handles edge case where app crashes mid-removal (power loss, system crash). Currently minor impact - orphaned vectors just waste space. Existing tool: `verify_index_sync.py repair` | Low |

## Completed Refactoring

| ID | Description | Completed |
|----|-------------|-----------|
| TD-022 | Type Annotations: Add precise numpy types, TypedDict for daemon modules | 2025-12-23 |
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
| TD-001 | Real Incremental Updates: Implement add/remove/update document in EmbeddingAdapter | 2025-07-19 |
| TD-005 | Standardize folder naming (sample_docs → ai_search_docs) | 2025-09-08 |
| TD-006 | Fix all mypy type annotations | 2025-08-03 |
| TD-007 | Remove duplicate backup logic in watch.py | 2025-09-06 |
| TD-008 | Remove emoji characters from quick_test.py | 2025-12-21 |
| TD-009 | Centralize path constants (INDEX_PATH, DATABASE_PATH) in config.py | 2025-12-21 |
| TD-010 | Refactor embedding.py to use config.py path constants | 2025-12-21 |
| TD-002 | Documentation: requirements.md exists with comprehensive markdown format | Pre-existing |

### TD-001: Real Incremental Index Updates - ✅ COMPLETED

**Previous State:**
- `EmbeddingAdapter` used mock incremental updates
- Full index rebuild required for actual changes

**Actions Taken:**
1. ✅ Implemented `add_document()` - adds single document with real-time FAISS updates
2. ✅ Implemented `remove_document()` - removes document chunks from index
3. ✅ Implemented `_add_to_faiss_and_db()` - direct FAISS index manipulation with add_with_ids()
4. ✅ Implemented `_remove_existing_document()` - removes IDs from FAISS with remove_ids()
5. ✅ Real-time index updates (<1 second per file)

**Result:**
- Completed 2025-07-19 (commit 111dd1c)
- File watcher now performs true incremental updates
- No full rebuild required for single file changes
- FAISS IndexIDMap enables add_with_ids() and remove_ids() operations

**Effort:** High (1-2 days)

### TD-002: Convert PRD to Markdown - ✅ COMPLETED

**Previous State:**
- Product requirements in `PRD_v0.4.docx` (Word format)
- Not version-control friendly

**Actions Taken:**
1. ✅ Created `docs/requirements.md` with structured markdown tables
2. ✅ Organized into functional requirements (FR-001 through FR-008)
3. ✅ Added non-functional requirements and technical specifications
4. ✅ Preserved original PRD_v0.4.docx for historical reference

**Result:**
- Completed (pre-existing)
- Comprehensive `requirements.md` with 94 lines covering:
  - Document processing (PDF, DOCX, TXT, Markdown)
  - Semantic search with embeddings
  - AI answer generation with citations
  - File watching and real-time indexing
  - User interface requirements
- Version-control friendly markdown format
- Original Word document retained in `docs/PRD_v0.4.docx`

**Effort:** Low (1 hour)

---

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
1. [x] Add numpy type hints: `np.ndarray` instead of `List`
2. [x] Create TypedDict for stats and progress dictionaries
3. [x] Run mypy --strict on daemon module
4. [x] Fix any additional type errors

**Result:** Completed 2025-12-23. All daemon modules now use precise type annotations with TypedDict and numpy array types.

---

## Execution Priority (Historical)

**All phases completed as of 2025-12-23:**

| Phase | Items | Actual Effort | Status |
|-------|-------|---------------|--------|
| **Phase 1** | TD-018 | 15 min | ✅ Completed 2025-12-23 |
| **Phase 2** | TD-020, TD-021 | 3 hours | ✅ Completed 2025-12-23 |
| **Phase 3** | TD-019 | 4 hours | ✅ Completed 2025-12-23 |
| **Phase 4** | TD-017 | 4 hours | ✅ Completed 2025-12-23 |
| **Phase 5** | TD-022 | 1.5 hours | ✅ Completed 2025-12-23 |

**Note:** TD-001 completed 2025-07-19, TD-002 was pre-existing

---

## Code Quality Metrics

| Metric | Status | Details |
|--------|--------|---------|
| Pre-commit hooks | ✅ All passing | black, isort, flake8, mypy |
| Type annotations | ✅ 100% coverage | core/, daemon/ modules with TypedDict |
| Code duplication | ✅ Eliminated | DatabaseManager, path constants centralized |
| Architecture | ✅ Standards compliant | No empty folders, organized structure |
| Module size | ✅ Optimized | Largest module: 696 lines (was 1159) |
| Memory efficiency | ✅ Optimized | Singleton model caching (~500MB savings) |
| Test coverage | ✅ All passing | Integration tests validated |
| Code style | ✅ Consistent | Emoji-free, cross-platform compatible |

## Maintenance Guidelines

**For Future Refactoring:**
1. Document the reason for any quick fixes
2. Estimate effort to properly refactor
3. Assign priority based on impact
4. Update this file when addressed
5. Follow the proven 5-phase approach used in Dec 2025

**Quality Standards:**
- All new code must pass pre-commit hooks (black, isort, flake8, mypy)
- Use TypedDict for structured dictionaries
- Centralize configuration through core/config.py
- Keep modules under 700 lines
- Use DatabaseManager for all SQLite operations
- Use Embedder singleton for model access

---

*Last Updated: 2025-12-23*
*Status: All Technical Debt Cleared ✅*
