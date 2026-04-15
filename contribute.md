# Contributing to code-review-env

Thanks for contributing.

## Before you start

- Read the project overview in `README.md`.
- Use Python 3.10+.
- Install dependencies:

```bash
pip install -e .
```

## Local validation

Run the existing sanity checks before opening a pull request:

```bash
python run_tests.py
```

## Contribution workflow

1. Fork the repository and create a focused branch.
2. Keep changes small and task-specific.
3. Update documentation when behavior changes.
4. Run tests and verify they pass.
5. Open a pull request with a clear summary and rationale.

## Pull request guidelines

- Explain what changed and why.
- Include testing notes (commands + results).
- Link related issues when available.

## Code style

- Follow existing project patterns.
- Prefer readability and explicit behavior.
- Avoid adding dependencies unless necessary.

## Reporting issues

Use GitHub Issues for:

- Bug reports
- Feature requests
- Documentation improvements
