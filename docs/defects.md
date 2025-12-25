# Defects

Known bugs, issues, and their resolution status.

## Active Defects

| ID | Description | Severity | Status | Reported |
|----|-------------|----------|--------|----------|
| DEF-023 | test_ui_backend.py leaks mocked modules into other tests via sys.modules | High | Open | 2025-12-23 |
| DEF-024 | tests expect ui.components but module is missing | Medium | Open | 2025-12-23 |
| DEF-025 | tests expect daemon.watch.ExtractorAdapter but symbol is missing | Medium | Open | 2025-12-23 |
| DEF-027 | Settings UI: delete/add path buttons give 400 errors on second click | Medium | Fixed | 2025-12-25 |

## Resolved Defects

| ID | Description | Severity | Resolution | Resolved |
|----|-------------|----------|------------|----------|
| DEF-027 | Settings UI: delete/add path buttons give 400 errors on second click | Medium | Fixed UI to accept both "success" and "accepted" status from async operations | 2025-12-25 |
| DEF-026 | Model loading banner overlays and blocks status panel | Medium | Changed position from absolute to relative for natural document flow | 2025-12-25 |
| DEF-022 | test_enhanced_adapter.py never asserts - always returns True | High | Added proper assert statements to validate operations | 2025-12-23 |
| DEF-021 | Numpy array boolean check causes ValueError in add_document() | Critical | Changed `if not embeddings:` to `if embeddings is None:` | 2025-12-23 |
| DEF-020 | Immediate indexing calls non-existent Embedder.add_document() | Critical | Changed to use EmbeddingAdapter.add_document() which has the method | 2025-12-23 |
| DEF-019 | Files not searchable after adding watch path (regression from DEF-018 fix) | High | Root cause was DEF-020, fixed by using correct API | 2025-12-23 || DEF-018 | Index/DB desync when removing watch paths (orphaned FAISS vectors) | Critical | Added FAISS vector removal to remove_watch_path() + verification tool | 2025-12-23 |
| DEF-017 | Model singleton not persisting between requests (~85-90s reload on each query) | High | Confirmed working - singleton reuses model, timing variations due to inference complexity | 2025-12-22 |
| DEF-016 | Watcher crash loop when index files missing | High | Added `_ensure_index_exists` to initialize empty index/DB | 2025-12-22 |
| DEF-015 | App crash due to FAISS/DB desync (Zombie Vectors) | Critical | Upgraded to IndexIDMap and synchronized deletions | 2025-12-22 |
| DEF-012 | Missing index file on fresh run | High | Rebuilt index manually | 2025-12-22 |
| DEF-014 | Poor retrieval recall (top_k=1) | High | Increased top_k to 5 and added metadata reload on cache miss | 2025-12-22 |
| DEF-013 | Stale index cache in app process | High | Implemented mtime check for index/metadata reload | 2025-12-22 |
| DEF-012 | Search failed after adding new watch path (files not indexed) | High | Implemented initial scan in watcher startup | 2025-12-22 |
| DEF-009 | Performance regression (FAISS index reload on every query) | Critical | Implemented in-memory caching for FAISS index | 2025-12-22 |
| DEF-010 | Integration test failure (Temp path handling) | High | Fixed path patching and DB connection handling | 2025-12-22 |
| DEF-011 | Corrupted DB handling in Ask | Medium | Added error handling for missing/corrupted meta table | 2025-12-22 |
| DEF-001 | Citation hallucination (fake Investopedia references) | Critical | Added relevance threshold (1.2), enhanced prompts | 2025-09-01 |
| DEF-002 | Citations point to extracts/ instead of ai_search_docs/ | Critical | Implemented _map_to_original_file() mapping | 2025-09-06 |
| DEF-003 | Garbled LLM output ("distits rock nrock head") | Critical | Removed ChatML format, simplified prompts | 2025-07-15 |
| DEF-004 | Answer truncation mid-sentence | High | Increased max_tokens 100→150 | 2025-09-08 |
| DEF-005 | Embedding format mismatch (expected 4 values, got 2) | High | Updated query() to return 4-tuple | 2025-07-15 |
| DEF-006 | Impossible page numbers (Peter Pan showing 500+) | Medium | Fixed page calculation algorithm | 2025-08-10 |
| DEF-007 | Windows temp file permission in test_watch.py | Low | Skipped on Windows environment | 2025-07-15 |
| DEF-008 | numpy.int64 → Python int conversion bug | Medium | Added explicit type conversion | 2025-07-14 |

## Defect Template

```markdown
### DEF-XXX: [Title]

**Severity:** Critical / High / Medium / Low
**Status:** Open / In Progress / Resolved / Won't Fix
**Reported:** YYYY-MM-DD
**Resolved:** YYYY-MM-DD

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Root Cause:**
[Technical explanation]

**Resolution:**
[How it was fixed]
```

---

*Last Updated: 2025-12-23*
