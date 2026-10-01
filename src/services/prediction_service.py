"""Shared file-to-prediction path for the CLI and HTTP API."""

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.models.pregame.predictor import EnsemblePredictor


def prediction_records(
    predictor: EnsemblePredictor,
    features_path: str | Path,
    target_date: date,
    home_team: str | None = None,
    away_team: str | None = None,
) -> list[dict[str, Any]]:
    """Predict only matching dated rows from a prepared feature snapshot.

    This function does not fetch live data or construct pregame features from
    box scores. The caller supplies a snapshot with the model's saved schema.
    """
    path = Path(features_path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing prepared features: {path}")
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
    elif path.suffix == ".csv":
        frame = pd.read_csv(path, dtype={"game_id": "string"})
    else:
        raise ValueError("Features must be a .parquet or .csv file")

    aliases = {}
    for name in ("home", "away"):
        if f"{name}_team" not in frame.columns and name in frame.columns:
            aliases[name] = f"{name}_team"
    frame = frame.rename(columns=aliases)
    required = {"game_id", "date", "home_team", "away_team"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Feature snapshot is missing identifiers: {sorted(missing)}")
    dates = pd.to_datetime(frame["date"], errors="raise")
    if dates.isna().any():
        raise ValueError("Feature snapshot contains missing dates")
    frame = frame.loc[dates.dt.date == target_date].copy()
    for column, requested in (("home_team", home_team), ("away_team", away_team)):
        if requested is not None:
            frame = frame.loc[frame[column].astype(str).str.casefold() == requested.casefold()]
    if frame.empty:
        return []
    if frame[list(required)].isna().any().any():
        raise ValueError("Game identifiers and team names cannot be missing")
    if frame["game_id"].duplicated().any():
        raise ValueError("Feature snapshot contains duplicate game IDs")
    if (frame["home_team"] == frame["away_team"]).any():
        raise ValueError("A team cannot play itself")

    predictions = predictor.predict_with_features(frame, top_n=5)
    return [
        {
            "game_id": str(row["game_id"]),
            "date": target_date.isoformat(),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
            "home_win_prob": prediction["prediction"],
            "away_win_prob": 1.0 - prediction["prediction"],
            "top_features": {
                feature["feature"]: {"importance": feature["importance"], "value": feature["value"]}
                for feature in prediction["top_features"]
            },
        }
        for row, prediction in zip(frame.to_dict("records"), predictions, strict=True)
    ]
