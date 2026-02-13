# API Keys & Secrets

This project supports optional integrations. All keys live in your local `.env` file and should **never** be committed.

## Required for live ingestion
- `NBA_STATS_API_KEY` — RapidAPI NBA Stats (https://rapidapi.com/)
- `ODDS_API_KEY` — The Odds API (https://the-odds-api.com/)
- `RAPIDAPI_KEY` — RapidAPI key for fallback sources

## Optional integrations
- `SUPABASE_URL`, `SUPABASE_KEY` — Supabase project connection
- `X_BEARER_TOKEN` — X/Twitter API bearer token
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — Reddit app credentials
- `YOUTUBE_API_KEY` — YouTube Data API
- `ORS_API_KEY` — OpenRouteService for travel fatigue

## Safety rules
- Keep keys in `.env` (see `.env.example`).
- If a key is ever exposed, rotate it immediately.
- Use least-privileged keys where possible.
