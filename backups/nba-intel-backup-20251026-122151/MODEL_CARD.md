# Model Card

- Pregame: LightGBM + decaying‑K Elo + isotonic calibration.
- Live: GRU sequence model for possession‑level win probability.
- Vision: MobileNetV3‑Small for 3–6 s highlight/foul‑candidate clips.
- Chemistry: GraphSAGE lineup graph → embeddings for pregame.
- Social: X/Reddit/YouTube aggregates for pre‑tip calibration.

Metrics: log loss, Brier, AUROC, ECE; per‑class P/R/F1 for vision.
