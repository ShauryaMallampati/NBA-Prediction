#!/usr/bin/env python3
"""Train the supported pregame ensemble using games before 2024-10-01."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.pregame.train_ensemble import EnsembleTrainer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=Path, required=True, help="Completed-game CSV/Parquet")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/models/pregame"))
    parser.add_argument("--estimators", type=int, default=300)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()
    try:
        trainer = EnsembleTrainer(args.output_dir, n_estimators=args.estimators, threads=args.threads)
        features, labels = trainer.load_data(args.games)
        trainer.train_all(features, labels, cv_folds=args.folds)
        trainer.save_models()
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Training failed: {exc}\n")
    print(f"Saved models to {args.output_dir}. Training diagnostics are not held-out results.")


if __name__ == "__main__":
    main()
