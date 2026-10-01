# Contributing

Contributions are welcome when they preserve the verified pregame pipeline and its reproducibility constraints.

## Quick setup

```bash
poetry install --only main,dev
```

## What to run before a PR

```bash
poetry run python -m compileall -q src scripts tests
poetry run ruff check src scripts tests
poetry run pytest -q
poetry build
```

If you change data or model code, include the dataset snapshot provenance and any generated artifact paths, hashes, and sizes.

## Code style

- Keep changes focused and readable.
- Explain non-obvious invariants and tradeoffs in comments rather than restating the code.
- Surface missing data, invalid artifacts, and unsupported states explicitly instead of substituting made-up defaults.

## Secrets & data

- Never commit real API keys. Use local environment variables.
- Big data stays out of git. If needed, describe how to reproduce it.

## Pull requests

- Explain the problem and the solution in a few sentences.
- Call out any breaking changes or data migrations.
