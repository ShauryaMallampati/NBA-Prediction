# Contributing

Contributions welcome.

## Setup

```bash
poetry install
```

That is the whole setup. There is no frontend, no `.env`, no database, and no
services to start. The test suite needs no data and no trained model artifacts.

## Before opening a PR

```bash
poetry run python -m compileall src scripts
poetry run pytest -q
```

Both run in CI on every push and pull request.

## Ground rules

The point of this repository is that its claims hold up, so:

- **Don't add a number you can't point at.** Every accuracy figure in the docs
  names the script that produced it and says what it measured. If you add a
  result, say whether it is cross-validation, in-sample, or holdout, and over
  which games.
- **Don't let a future game into a feature.** Read state before you update it,
  filter warm-up windows with a strict `<`, and keep outcome columns out of the
  schema. `assert_no_leakage()` exists for this; `tests/test_chronology.py`
  guards it.
- **Don't paper over a failure.** No bare `except:` to keep a script running, no
  placeholder constants standing in for real values, no defaults that invent
  data. If something is missing, raise and say what is missing.
- **Tests should be able to fail.** Don't mock the thing under test, and don't
  compute an expected value by calling the function you are testing.

## Style

Match the surrounding code. Comments should explain why, not restate the line
below them.

## Data and secrets

- Never commit API keys. Nothing in this repository needs one.
- Game logs and model artifacts stay out of git — they are gitignored. Describe
  how to regenerate them instead.
