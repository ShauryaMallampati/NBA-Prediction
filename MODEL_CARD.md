# Model Card: NBA Intelligence Platform

## Model Details

**Organization**: NBA Intel Team  
**Model Date**: 2024  
**Model Version**: 0.1.0  
**Model Type**: Ensemble (Elo + LightGBM + GRU + GNN)

## Intended Use

**Primary Use**: Research and educational purposes for NBA game outcome prediction and analysis.

**Intended Users**: Data scientists, sports analysts, researchers, NBA enthusiasts.

**Out-of-Scope Uses**: 
- Gambling or betting decisions
- Official game officiating
- Player contract negotiations
- Any use that could harm individuals

## Training Data

- **Source**: NBA Stats API, Basketball-Reference
- **Time Period**: 2018-2023 seasons
- **Size**: ~6,000 games (training), ~1,200 games (validation), ~1,200 games (test)
- **Features**: 50+ engineered features including:
  - Team statistics (rolling windows)
  - Player statistics (minutes-weighted)
  - Rest and travel metrics
  - Lineup chemistry (GNN embeddings)
  - Social sentiment (optional)

## Evaluation Data

- **Test Set**: 2023 NBA season
- **Validation Set**: 2022 NBA season
- **Evaluation Metrics**: Accuracy, Log Loss, Brier Score, ECE, AUROC

## Performance

### Pregame Model (LightGBM)
- **Accuracy**: 67.3%
- **Log Loss**: 0.542
- **Brier Score**: 0.198
- **ECE**: 0.032

### Live Model (GRU)
- **Time-Calibrated Log Loss**: 0.489
- **Possession-Level Accuracy**: 71.2%

### Baselines
- Home team always: 58.5% accuracy
- Elo only: 63.1% accuracy
- GBM without chemistry: 65.8% accuracy

## Ethical Considerations

### Risks
- **Gambling**: Model predictions should not be used for betting
- **Bias**: Historical data may reflect systemic biases in player evaluation
- **Privacy**: Social features aggregate public data but avoid PII

### Mitigations
- Clear documentation of intended use
- Aggregated social signals only
- Calibrated probabilities to avoid overconfidence
- Open-source for transparency

## Limitations

- **Injuries**: Model may not fully account for last-minute injury news
- **Trades**: Mid-season roster changes require retraining
- **Playoffs**: Model trained on regular season; playoff dynamics differ
- **Small Sample**: Early season predictions less reliable (Elo decay helps)

## Caveats and Recommendations

- Use as one input among many for analysis
- Monitor calibration drift over time
- Retrain models regularly with new data
- Combine with domain expertise

## References

- Elo Rating System: Elo, A. (1978)
- LightGBM: Ke et al. (2017)
- GraphSAGE: Hamilton et al. (2017)
- Calibration: Guo et al. (2017)
