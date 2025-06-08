This repository uses Ruff for linting and pytest for tests.

When modifying files:
1. Install development dependencies with `pip install -e .[dev]`.
2. Run `ruff check src tests` and fix any reported issues.
3. Run `pytest -q` to ensure tests pass.

Only commit changes once these checks succeed.
