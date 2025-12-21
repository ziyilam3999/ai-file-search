# Refactoring

Technical debt and cleanup tasks.

## Active Technical Debt

| ID | Description | Priority | Effort | Status |
|----|-------------|----------|--------|--------|
| TD-001 | EmbeddingAdapter uses mock instead of real incremental updates | Medium | High | Not Started |
| TD-002 | PRD_v0.4.docx should be converted to Markdown | Low | Low | Not Started |
| TD-003 | milestones.yml could be merged into progress.md | Low | Low | Completed |

## Completed Refactoring

| ID | Description | Completed |
|----|-------------|-----------|
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

*Last Updated: 2025-12-21*
