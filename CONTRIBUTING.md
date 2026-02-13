# Contributing

Thanks for checking this out — contributions are welcome.

## Quick setup

```bash
poetry install
npm install
cp .env.example .env
```

## What to run before a PR

```bash
npm run lint
npm run typecheck
npm run build
poetry run pytest -q
```

If you changed data or model code, include a short note about the dataset snapshot
and any new artifacts you generated (paths + sizes).

## Style vibes (keep it human)

- Match the existing code style; keep changes tight and readable.
- Comments should be short, human, and actually useful (no filler).
- Avoid “magic” defaults that invent data. If something’s missing, surface it.

## Secrets & data

- Never commit real API keys. Use `.env` locally.
- Big data stays out of git. If needed, describe how to reproduce it.

## Pull requests

- Explain the problem and the solution in a few sentences.
- Call out any breaking changes or data migrations.
