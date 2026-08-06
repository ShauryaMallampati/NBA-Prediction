# Architecture

How a game becomes a win probability, and what stops future information from
getting in.

## Data flow

```
Kaggle "wyattowalsh/basketball"  →  data/kaggle_nba/Games.csv
        │
        │  scripts/data_prep/process_kaggle_games.py
        ▼
data/nba_games_enhanced.csv       one row per completed game:
        │                         date, game_id, home, away,
        │                         home_pts, away_pts, home_win, margin
        │
        │  RunningWorldState  (src/common/features.py)
        ▼
80 pregame features per game  ──┬──►  EnsembleTrainerV2  →  artifacts/models/pregame/
                                │      (src/models/pregame/train_ensemble_v2.py)
                                │
                                └──►  EnsemblePredictor  →  P(home win)
                                       (src/models/pregame/predictor.py)
```

The same function builds features for training and for prediction. That is the
main structural decision in the project: there is no separate "serving" feature
path that could drift from the training one.

## Pregame feature construction

`RunningWorldState` is an incremental state machine over the game log. It holds
per-team history — Elo, results, scoring, opponents faced, head-to-head, rest —
and exposes two methods:

- `get_team_features(home, away, date)` — reads current state, returns 80 floats.
- `update(home, away, date, home_win, home_pts, away_pts)` — folds one finished
  game into the state.

The 80 features group as follows.

| Group | Count | Examples |
| --- | --- | --- |
| Elo | 6 | `elo_home`, `elo_diff`, `elo_win_prob`, `mov_elo_diff` (margin-of-victory-adjusted) |
| Rolling win% | 8 | `home_win_pct_l5/l10/l20`, `home_home_win_pct`, `away_away_win_pct` |
| Rolling scoring | 12 | `home_pts_avg_l5/l10`, `home_pts_allowed_l10`, `home_net_rating`, `home_margin_avg_l10` |
| Pythagorean | 2 | `home_pythagorean`, `away_pythagorean` (exponent 13.91) |
| Strength of schedule | 4 | `home_sos_l10` (mean opponent Elo), `home_opp_win_pct_l10` |
| Form and trend | 6 | `home_momentum` (win% L5 − win% L20), `home_scoring_trend`, `home_weighted_form` |
| Rest and fatigue | 7 | `home_rest_days`, `rest_differential`, `home_back_to_back`, `home_games_last_7_days` |
| Streaks | 4 | `home_win_streak`, `away_loss_streak` |
| Head-to-head | 3 | `h2h_games`, `h2h_home_win_pct`, `h2h_avg_margin` |
| Calendar context | 5 | `season_phase`, `is_playoff`, `day_of_week`, `home_game_number` |
| Differentials | 10 | `elo`/`win_pct`/`net_rating`/`pythagorean`/`sos` gaps between the two teams |
| Compatibility columns | 13 | fixed constants and derived duplicates kept so older artifacts still load |

`home_momentum` is one of these tabular columns — a difference of two rolling win
percentages. It is unrelated to the sequence model that earlier versions of this
project experimented with, which is not part of this release.

## What stops future information from entering a feature

Three rules, each with a test in `tests/test_chronology.py`.

1. **Read before write.** Every loop that builds features calls
   `get_team_features()` for a game *before* calling `update()` with that game's
   result. A game never contributes to its own features.

2. **Warm-up is strictly earlier.** `scripts/predict.py::warm_up_state` and
   `scripts/eval/evaluate_holdout.py` replay only games with `date < prediction
   date`. Games on the prediction date itself are excluded.

3. **Outcome columns are structurally excluded.** `home_pts`, `away_pts`,
   `home_win`, `margin` and friends exist in the game log — they build the
   training target and update state after a game — but never appear in the
   feature vector. `assert_no_leakage()` in `src/common/features.py` is called by
   the trainer on the schema it is about to fit and by the predictor on the
   schema it loads, so a leaking schema fails loudly at both ends.

### The one caveat worth knowing

The game log has date granularity, not tip-off times. Games sharing a calendar
date are replayed in `(date, game_id)` order, so the second game of a day inherits
the first game's result. Real games on the same date are played at different
times, so this is usually harmless, but it is a convention rather than true
chronology. `sort_games_chronologically()` pins that order with a stable sort, so
at least it is the *same* convention on every run — before that fix, filtering the
log a different way silently reordered same-day games and changed the features.

## Chronological splitting

Training uses `TimeSeriesSplit(n_splits=5)` over the date-ordered feature matrix.
Each fold trains on a prefix and validates on the block immediately after it, so
no fold ever trains on a game later than the game it is scored on.

Two further boundaries:

- The first 500 games are dropped. Rolling windows and Elo need history before
  they mean anything; those rows would otherwise train the model on defaults.
- `cutoff_date` (default `2024-10-01`) removes everything after it from training,
  reserving those seasons for `scripts/eval/evaluate_holdout.py`.

## Model training

Four base models, deliberately not four variations of the same thing — three
boosted-tree implementations plus one bagged model for a different error profile:

| Model | Role |
| --- | --- |
| XGBoost | gradient boosting, depth 7 |
| LightGBM | leaf-wise boosting, 48 leaves |
| CatBoost | ordered boosting, depth 7 |
| ExtraTrees | randomised bagging — decorrelates the boosters |

Each is trained twice: once per CV fold to collect out-of-fold predictions, and
once on the full training period to produce the artifact that ships.

## Calibration

Every base model is wrapped in
`CalibratedClassifierCV(method='isotonic', cv=TimeSeriesSplit(3))` before being
saved. Isotonic regression is fitted chronologically for the same reason as
everything else here. Only the calibrated models are written to disk, so the
probabilities the predictor returns are calibrated by construction.

## Ensemble aggregation

A logistic-regression meta-learner stacks the four calibrated probabilities. Its
inputs are the four out-of-fold probabilities plus six derived signals:

```
[p_xgb, p_lgb, p_cat, p_et,
 p_xgb * p_lgb,          # agreement between the two fastest boosters
 p_cat * p_et,           # agreement across the boosting/bagging divide
 mean, std, max, min]    # consensus level and spread
```

`std` is the useful one: it tells the meta-learner how much the base models
disagree, which is a proxy for how uncertain the prediction is. Features are
standardised with a `StandardScaler` fitted at training time and saved as
`meta_scaler.pkl`.

The gain from stacking over a simple average is small. On the author's training
run the four out-of-fold accuracies were 64.4–65.9% and their unweighted mean
scored 65.86%; the meta-learner scored 65.97%, and that figure is measured on the
rows it was fitted on, so it is optimistic. Treat the stack as a tidier way to
combine models, not as a source of accuracy.

## Prediction

`EnsemblePredictor` loads all seven artifacts, or raises `MissingArtifactsError`
naming every file that is absent. Then, per prediction:

1. `prepare_features()` selects exactly the training columns in the training
   order. Extra columns in the caller's frame are ignored; missing ones raise a
   `ValueError` listing them by name; column order in the input cannot change the
   result.
2. Each calibrated base model produces a probability.
3. The ten meta-features are assembled, scaled, and passed to the meta-learner.
4. Output is `P(home team wins)`.

`scripts/predict.py` wraps this: it replays the historical log up to the
prediction date, builds features for the requested matchups, and emits JSON Lines.

## Evaluation

`scripts/eval/evaluate_holdout.py` is the only honest out-of-sample measurement.
It walks the holdout period in order: predict, record, then update state with the
actual result. It reports accuracy, AUC, log loss and Brier score, alongside the
always-pick-the-home-team baseline — which is the number that matters, because
home teams win around 60% of NBA games and any model must clear that to be worth
running.
