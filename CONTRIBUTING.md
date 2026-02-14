# Contributing

Thanks for checking this out — contributions are welcome.

## Quick setup

```bash
poetry install
```

## What to run before a PR

```bash
poetry run pytest -q
```

If you changed data or model code, include a short note about the dataset snapshot
and any new artifacts you generated (paths + sizes).

## Code style

- Match the existing style - keep things clean and easy to follow
- Write comments that actually help (imagine you're explaining to a friend)
- Don't hide problems with made-up defaults - surface issues clearly

## Secrets & data

- Never commit real API keys. Use local environment variables.
- Big data stays out of git. If needed, describe how to reproduce it.

## Pull requests

- Explain the problem and the solution in a few sentences.
- Call out any breaking changes or data migrations.
