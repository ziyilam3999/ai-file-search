# Contributing

Thanks for your interest in contributing to `ai-file-search`.

## Before you start

- Open an issue first for non-trivial changes so scope can be discussed before code is written
- Check existing issues and PRs to avoid duplicate work

## Development

Requires Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/ziyilam3999/ai-file-search.git
cd ai-file-search
poetry install
poetry run python complete_setup.py   # one-time: downloads models + initializes indexes
```

Once setup is complete, the tools in the README Quick Start section are ready to run.

## Proposing a change

1. Create a branch: `git checkout -b feat/short-description`
2. Make focused commits (conventional-commit prefixes preferred: `feat:`, `fix:`, `docs:`, `chore:`)
3. Run the syntax check locally: `python -m compileall -q .`
4. Push and open a PR
5. CI runs the same syntax check — must pass

## Style

- Keep PRs focused on one concern
- Python 3.12+ features are fine to use
- Format with `black` before committing (configured in `pyproject.toml`)
- Update the README when user-facing behavior changes

## License

By contributing, you agree your contributions are licensed under the MIT License (see `LICENSE`).
