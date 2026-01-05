# Testing

Test plans, coverage reports, and quality assurance documentation.

## Test Suite Overview

| Test File | Category | Tests | Status |
|-----------|----------|-------|--------|
| test_ask.py | Unit | Ask module tests | Passing |
| test_embedding.py | Unit | Embedding/search tests | Passing |
| test_extract.py | Unit | Document extraction tests | Passing |
| test_watch.py | Unit | File watcher tests | 24/25 Passing |
| test_core_utils.py | Unit | Core utilities (citations, file opening) | Passing |
| test_core_config.py | Unit | Configuration logic | Passing |
| test_user_config.py | Unit | Platform-aware user config | 33/33 Passing |
| test_ui.py | Integration | Streamlit UI tests | 5/5 Passing |
| test_ui_components.py | Unit | UI components (rendering, styles) | Passing |
| test_ui_backend.py | Unit | Flask API endpoints | Passing |
| test_index_manager.py | Unit | Watch path management | 4/4 Passing |
| test_confluence.py | Unit | Confluence integration | Passing |
| test_complete_system.py | Integration | Full system tests | Passing |
| test_regression.py | Regression | Citation accuracy tests | 6/6 Passing |
| test_faiss_sync.py | Unit | FAISS/SQLite synchronization | Passing |
| test_quick.py | Smoke | Fast validation tests | 5/5 Passing |

**Total: 186 passed, 20 skipped** (as of 2026-01-05)

## Test Infrastructure

### conftest.py (Shared Fixtures)

The test suite uses `tests/conftest.py` to provide shared fixtures and ensure test isolation:

```python
# Key fixtures available to all tests:

@pytest.fixture(autouse=True)
def cleanup_mocked_modules():
    """Automatically cleans up mocked modules before/after each test."""

@pytest.fixture
def isolated_index_manager(temp_config_dir):
    """Provides fully isolated IndexManager with temp config/db."""

@pytest.fixture
def temp_watch_dir(tmp_path):
    """Provides temporary directory for watch path testing."""

@pytest.fixture
def flask_test_client():
    """Provides Flask test client with mocked dependencies."""
```

### Mock Management Pattern

Tests that require module-level mocking (e.g., for heavy imports) follow this pattern:

```python
# 1. Save original modules
_ORIGINAL_MODULES = {name: sys.modules.get(name) for name in _MOCK_MODULES}

# 2. Apply mocks
for name in _MOCK_MODULES:
    sys.modules[name] = MagicMock()

# 3. Import target module
from target_module import something

# 4. IMMEDIATELY restore modules
for name, original in _ORIGINAL_MODULES.items():
    if original is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = original
```

This pattern prevents mock pollution between test files.

## Running Tests

```bash
# Run fast tests only (default, skips model loading)
pytest -q

# Run all tests (including slow model-loading tests)
pytest -q -m ""
# or
pytest -q --slow

# Run only slow tests
pytest -q -m slow

# Run quick smoke tests (recommended before commits)
python tests/test_quick.py

# Run with coverage
pytest tests/ --cov=core --cov-report=html

# Run specific test file
pytest tests/test_embedding.py -v

# Verify index synchronization
python tools/verify_index_sync.py check      # Check for sync issues
python tools/verify_index_sync.py repair     # Fix orphaned vectors
python tools/verify_index_sync.py stats      # Show detailed statistics
```

### Test Markers

- **`@pytest.mark.slow`**: Tests that load models or build large indexes (excluded by default)
  - `test_llm_integration.py`: LLM model loading
  - `test_integration.py`: Full system integration
  - `bench_llm_performance.py`: Performance benchmarks
  - `test_query_performance.py`: Query benchmarks
  - `test_embedding_watch_integration.py`: Embedding system integration

## Test Categories

### 1. Unit Tests
- **test_ask.py**: Question answering module
- **test_embedding.py**: Vector search and indexing
- **test_extract.py**: PDF/DOCX/TXT extraction
- **test_watch.py**: File watcher functionality
- **test_core_utils.py**: Utility functions (citation formatting, file opening)
- **test_core_config.py**: Configuration management
- **test_ui_components.py**: UI rendering logic and components
- **test_llm_integration.py**: LLM model loading and generation (renamed from test_phi3_integration.py)
- **bench_llm_performance.py**: Performance benchmarks (renamed from bench_phi3_performance.py)

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
| Answer generation | < 60s | 63s (improved from 126s) |
| Full test suite | < 10min | 8m 13s |

### Model Benchmarking Tool

**Purpose:** Compare different LLM models for speed/quality trade-offs

**Tool:** `tools/benchmark_models.py` (requires Ollama)

**Models Tested:**
- Phi-3.5-mini (current production model)
- Qwen2.5 (1.5b, 0.5b variants)
- Gemma2 (2b variant)

**Usage:**
```bash
# Install Ollama first
# Pull models: ollama pull phi3.5
poetry run python tools/benchmark_models.py
```

**Output:** Comparison table with first token time, generation speed, answer quality

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

## Maintenance & Diagnostics

### Index Synchronization Verification
Run after removing watch paths or encountering "Index/DB out of sync" errors:

```bash
# Check for orphaned vectors
python tools/verify_index_sync.py check

# Fix automatically
python tools/verify_index_sync.py repair

# View detailed statistics
python tools/verify_index_sync.py stats
```

**When to use:**
- After removing watch paths via Settings UI
- When queries return "Index/DB out of sync" errors
- Before major reindexing operations
- As part of regular maintenance (monthly recommended)

## Adding New Tests

1. Place test files in `tests/` directory
2. Name files with `test_` prefix
3. Use pytest fixtures from `conftest.py`
4. Add to appropriate category in this document

---

*Last Updated: 2025-12-21*
