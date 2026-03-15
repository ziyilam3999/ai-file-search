# Contributing to AI File Search

Thanks for your interest in contributing!

## Getting Started

1. Fork and clone the repo
2. Install dependencies: `poetry install`
3. Run setup: `python complete_setup.py`
4. Run tests: `poetry run pytest tests/test_quick.py -v`

## Development

```bash
poetry install           # Install dependencies
poetry run pytest        # Run full test suite
poetry run pytest tests/test_quick.py  # Quick tests (no models needed)
python run_app.py        # Launch web UI
python cli.py "query"    # CLI search
```

## Submitting Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Ensure quick tests pass: `poetry run pytest tests/test_quick.py -v`
4. Submit a pull request

## Guidelines

- Keep PRs focused on a single change
- Add tests for new features in `tests/`
- Follow existing Python conventions
- Document new CLI commands or configuration options

## Bug Reports

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Whether ML models are downloaded
