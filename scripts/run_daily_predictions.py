"""Write predictions from an existing feature snapshot; no live data is fetched."""

import argparse
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.paths import Paths
from src.models.pregame.predictor import EnsemblePredictor
from src.services.prediction_service import prediction_records

logger = logging.getLogger(__name__)


def save_predictions(predictions, target_date, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{target_date.isoformat()}.jsonl"
    created_at = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as handle:
        for prediction in predictions:
            record = {**prediction, "created_at": created_at}
            handle.write(json.dumps(record, allow_nan=False) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--features", type=Path, default=Paths.ARTIFACTS / "features/pregame.parquet")
    parser.add_argument("--model-dir", type=Path, default=Paths.MODELS / "pregame")
    parser.add_argument("--output-dir", type=Path, default=Paths.DATA / "predictions")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        predictor = EnsemblePredictor(args.model_dir)
        predictions = prediction_records(predictor, args.features, args.date)
        path = save_predictions(predictions, args.date, args.output_dir)
    except (OSError, ValueError, ImportError) as exc:
        logger.error("Prediction failed: %s", exc)
        return 1
    logger.info("Wrote %d predictions to %s", len(predictions), path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
