# NBA Intel

Production‑minded, locally runnable Full‑Stack NBA Intelligence Platform with strict Real‑Data Rule and Apple‑silicon MPS acceleration.

**Generated:** 2025-10-26

## Run
1. `make setup && make up`
2. `cp .env.example .env` and fill keys (see **KEYS.md**)
3. `make key-audit`
4. `make seed`
5. `make data`
6. `make train-pregame`
7. `make train-live`
8. `make train-vision`
9. `make train-chemistry`
10. `make social-build` (if sentiment enabled)
11. `make eval`
12. `make serve && make web` → http://localhost:3000

See `DATA_USE.md` and `MODEL_CARD.md`.
