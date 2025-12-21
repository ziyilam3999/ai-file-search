# Testing

Test plans, coverage reports, and quality assurance documentation.

## Test Suite Overview

| Test File | Category | Tests | Status |
|-----------|----------|-------|--------|
| test_ask.py | Unit | Ask module tests | Passing |
| test_embedding.py | Unit | Embedding/search tests | Passing |
| test_extract.py | Unit | Document extraction tests | Passing |
| test_watch.py | Unit | File watcher tests | 24/25 Passing |
| test_ui.py | Integration | Streamlit UI tests | 5/5 Passing |
| test_complete_system.py | Integration | Full system tests | Passing |
| test_regression.py | Regression | Citation accuracy tests | 6/6 Passing |
| test_quick.py | Smoke | Fast validation tests | 5/5 Passing |

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run quick smoke tests (recommended before commits)
python tests/test_quick.py

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Run specific test file
pytest tests/test_embedding.py -v
```

## Test Categories

### 1. Unit Tests
- **test_ask.py**: Question answering module
- **test_embedding.py**: Vector search and indexing
- **test_extract.py**: PDF/DOCX/TXT extraction
- **test_watch.py**: File watcher functionality

### 2. Integration Tests
- **test_ui.py**: Streamlit UI components
- **test_complete_system.py**: End-to-end workflows

### 3. Regression Tests
- **test_regression.py**: Citation accuracy validation
  - System requirements (database/FAISS sync)
  - Embedding system accuracy
  - Relevance filtering (threshold 1.2)
  - Citation authenticity
  - Performance benchmarks

### 4. Smoke Tests
- **test_quick.py**: Fast validation (5 tests, ~3 minutes)
  - System files check
  - Embedder functionality
  - Citation accuracy
  - Search functionality
  - Answer generation

## Performance Benchmarks

| Test | Target | Achieved |
|------|--------|----------|
| Index build | < 60s | 40.34s |
| Query response | < 200ms | 17.4ms |
| Answer generation | < 60s | ~46s |
| Full test suite | < 10min | 8m 13s |

## Test Configuration

Configuration file: `tests/test_config.yaml`

```yaml
test_settings:
  relevance_threshold: 1.2
  min_answer_length: 100
  test_queries:
    - "parking hosting rules"
    - "token economy"
    - "Alice in Wonderland"
```

## Coverage Report

| Module | Coverage |
|--------|----------|
| core/ask.py | High |
| core/embedding.py | High |
| core/extract.py | High |
| core/config.py | Medium |
| core/llm.py | Medium |
| daemon/watch.py | High |

## Known Test Issues

| Issue | Status | Notes |
|-------|--------|-------|
| test_watch.py Windows temp file | Skipped | Permission issue on Windows |
| LLM tests slow | Expected | CPU inference ~46s per test |

## Adding New Tests

1. Place test files in `tests/` directory
2. Name files with `test_` prefix
3. Use pytest fixtures from `conftest.py`
4. Add to appropriate category in this document

---

*Last Updated: 2025-12-21*
