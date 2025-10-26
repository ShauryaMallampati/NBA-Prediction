from __future__ import annotations
import pathlib, pandas as pd, lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, brier_score_loss
from joblib import dump

FEATS = pathlib.Path("artifacts/features/pregame.parquet")
OUT = pathlib.Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    if not FEATS.exists():
        raise SystemExit("Missing pregame features. Run `make data`.")
    df = pd.read_parquet(FEATS)
    if not set(["home_pts","away_pts"]).issubset(df.columns):
        raise SystemExit("Labels missing in feature set; ensure real data or enable mock.")
    X = df[["elo_home", "elo_away", "home_adv_flag"]]
    y = (df["home_pts"] > df["away_pts"]).astype(int)
    model = lgb.LGBMClassifier(
        num_leaves=63, learning_rate=0.05, n_estimators=300, feature_fraction=0.8, random_state=42
    )
    model.fit(X, y)
    calib = CalibratedClassifierCV(model, method="isotonic", cv=3).fit(X, y)
    p = calib.predict_proba(X)[:, 1]
    print("LogLoss:", log_loss(y, p), "Brier:", brier_score_loss(y, p))
    dump(calib, OUT / "pregame_lgbm_calibrated.joblib")

if __name__ == "__main__":
    main()
