# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run/Test Commands
- Run system: `python run_interactive.py`
- Run test mode: `python run_test.py`
- Run tests: `pytest src/tests/`
- Run single test: `pytest src/tests/test_file.py::test_function_name`
- Run tests with coverage: `pytest --cov=src src/tests/`

## Code Style Guidelines
- Imports: Standard libraries first, then third-party, then project modules (grouped by category)
- Types: Use type hints for function arguments and return values
- Naming: snake_case for functions/variables, CamelCase for classes
- Error handling: Use try/except with specific exceptions; prefer logging over printing
- Docstrings: Use triple quotes with Args/Returns sections for function documentation
- Comments: In Polish language, explaining complex logic
- Use f-strings for string formatting
- Logging: Use Python's logging module with appropriate levels (INFO, WARNING, ERROR)