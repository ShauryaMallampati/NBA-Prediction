"""Evaluate frozen model artifacts on later games from a local historical snapshot.

No data is downloaded and no model is trained by this command. Earlier games in
this same snapshot warm up the feature history; completed evaluation games can
inform features for subsequent games, but never their own prediction.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.pregame.predictor import EnsemblePredictor
from src.models.pregame.train_ensemble import EnsembleTrainer


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def package_versions() -> dict[str, str]:
    """Record the installed distribution, including the CPU-only XGBoost variant."""
    versions = {name: importlib.metadata.version(name) for name in
                ("numpy", "pandas", "scikit-learn", "lightgbm", "catboost")}
    for name in ("xgboost-cpu", "xgboost"):
        try:
            versions[name] = importlib.metadata.version(name)
            break
        except importlib.metadata.PackageNotFoundError:
            continue
    else:
        raise RuntimeError("No XGBoost distribution is installed")
    return versions


def metrics(labels, probabilities) -> dict:
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities, dtype=float)
    if labels.ndim != 1 or not len(labels) or labels.shape != probabilities.shape:
        raise ValueError("Labels and probabilities must be nonempty, matching vectors")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Labels must contain only 0 or 1")
    if (not np.isfinite(probabilities).all()
            or (probabilities < 0).any() or (probabilities > 1).any()):
        raise ValueError("Probabilities must be finite and between 0 and 1")
    return {
        "accuracy": float(accuracy_score(labels, probabilities >= 0.5)),
        "roc_auc": float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) == 2 else None,
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
    }


def evaluate(games_path: Path, model_dir: Path, start: str, end: str,
             expected_source_sha256: str | None = None) -> dict:
    games_path, model_dir = Path(games_path), Path(model_dir)
    source_hash = digest(games_path)
    if expected_source_sha256 is not None and source_hash != expected_source_sha256:
        raise ValueError("Input snapshot SHA-256 does not match the requested snapshot")
    if games_path.suffix == ".csv":
        raw = pd.read_csv(games_path, dtype={"game_id": "string"})
    elif games_path.suffix == ".parquet":
        raw = pd.read_parquet(games_path)
    else:
        raise ValueError("Raw games must be a CSV or Parquet snapshot")
    predictor = EnsemblePredictor(model_dir)
    training = predictor.metadata.get("training_data")
    if not isinstance(training, dict) or not training.get("end_date") or not training.get("start_date"):
        raise ValueError("Model metadata must record training_data start_date and end_date")
    first, last = pd.Timestamp(start), pd.Timestamp(end)
    training_start, training_end = pd.Timestamp(training["start_date"]), pd.Timestamp(training["end_date"])
    if pd.isna(first) or pd.isna(last) or pd.isna(training_start) or pd.isna(training_end):
        raise ValueError("Evaluation and training dates must be valid")
    if any(value.tz is not None for value in (first, last, training_start, training_end)):
        raise ValueError("Use timezone-free game dates for evaluation and training provenance")
    if training.get("source_sha256") and training["source_sha256"] != source_hash:
        raise ValueError("Input snapshot SHA-256 differs from recorded training provenance")
    if first > last or first <= training_end:
        raise ValueError("Evaluation must start strictly after training and end no earlier than it starts")

    frame = EnsembleTrainer.prepare_game_rows(raw)
    if "game_id" not in frame or frame["game_id"].isna().any() or frame["game_id"].duplicated().any():
        raise ValueError("Raw games must have unique, nonmissing game_id values")
    if frame["date"].min() > training_start:
        raise ValueError("Include the training-period history to initialize pregame features")
    # Use the same feature functions as training, on the complete ordered history.
    frame = EnsembleTrainer.engineer_game_rows(frame)
    selected = frame.loc[(frame["date"] >= first) & (frame["date"] <= last)].copy()
    if selected.empty:
        raise ValueError("No completed games in the evaluation window")
    probabilities = predictor.predict(selected)
    labels = selected["home_win"].to_numpy(dtype=int)
    baselines = {
        "always_home": metrics(labels, np.ones(len(labels))),
        "pregame_elo": metrics(labels, selected["elo_win_prob"].to_numpy()),
    }
    rate = training.get("home_win_rate")
    if isinstance(rate, (int, float)) and np.isfinite(rate) and 0 <= rate <= 1:
        baselines["training_home_win_rate"] = metrics(labels, np.full(len(labels), rate))
    return {
        "schema_version": 1,
        "evaluation_scope": "later_games_fixed_models_sequential_feature_updates",
        "games": len(selected),
        "start_date": selected["date"].min().date().isoformat(),
        "end_date": selected["date"].max().date().isoformat(),
        "training_data": training,
        "input_sha256": source_hash,
        "matches_recorded_training_snapshot": (
            source_hash == training["source_sha256"] if training.get("source_sha256") else None),
        "model_sha256": {name: digest(model_dir / name) for name in
                         ("ensemble_metadata.json", "xgb_model.pkl", "lgb_model.pkl", "cat_model.pkl")},
        "feature_names": predictor.feature_names,
        "threshold": 0.5,
        "ensemble": metrics(labels, probabilities),
        "baselines": baselines,
        "environment": {
            "python": platform.python_version(),
            **package_versions(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--start", required=True, help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Inclusive YYYY-MM-DD")
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(args.games, args.model_dir, args.start, args.end, args.expected_source_sha256)
    except (OSError, ValueError, ImportError) as exc:
        parser.exit(1, f"Evaluation failed: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
