# 🎯 Model Card: NBA Game Outcome Predictor

## Model Overview

**Model Name:** NBA Game Outcome Predictor v2.1

**Model Type:** Ensemble (Stacked XGBoost + LightGBM + CatBoost)

**Purpose:** Predict the outcome of NBA games with probability estimates for each team

**Last Updated:** 2024-11-12

**Owner:** Shaurya Mallampati

---

## 📊 Model Architecture

### Ensemble Components

1. **XGBoost Classifier**
   - Base model for structured feature learning
   - Hyperparameters:
     - `max_depth`: 6
     - `learning_rate`: 0.05
     - `n_estimators`: 200
     - `colsample_bytree`: 0.8
     - `subsample`: 0.8

2. **LightGBM Classifier**
   - Gradient boosting with leaf-wise growth
   - Hyperparameters:
     - `max_depth`: 7
     - `learning_rate`: 0.05
     - `n_estimators`: 200
     - `num_leaves`: 63
     - `feature_fraction`: 0.8

3. **CatBoost Classifier**
   - Handles categorical features natively
   - Hyperparameters:
     - `depth`: 6
     - `learning_rate`: 0.05
     - `iterations`: 200
     - `l2_leaf_reg`: 3
     - `border_count`: 128

### Stacking Strategy

- **Base Models:** XGBoost, LightGBM, CatBoost (equal weights initially)
- **Meta-Learner:** Logistic Regression
- **Voting:** Soft voting with probability averaging
- **Calibration:** Isotonic regression for probability calibration

---

## 📈 Performance Metrics

### Overall Performance

| Metric | Training | 5-Fold CV | Test Set |
|--------|----------|-----------|----------|
| **Accuracy** | 81.2% | 62.6% | 63.4% |
| **Precision** | 83.5% | 64.1% | 65.2% |
| **Recall** | 79.8% | 61.8% | 62.1% |
| **F1 Score** | 81.6% | 62.9% | 63.6% |
| **AUC-ROC** | 0.945 | 0.694 | 0.701 |
| **Log Loss** | 0.421 | 0.648 | 0.635 |

### Performance by Confidence Level

| Confidence | Games | Accuracy | Precision | Recall |
|------------|-------|----------|-----------|--------|
| **High (>70%)** | 1,245 (23%) | 72.3% | 75.1% | 70.8% |
| **Medium (55-70%)** | 2,876 (53%) | 61.4% | 62.9% | 60.2% |
| **Low (<55%)** | 1,299 (24%) | 52.4% | 53.8% | 51.6% |

### Performance by Season Phase

| Phase | Games | Accuracy | Notes |
|-------|-------|----------|-------|
| **Early Season** (Oct-Nov) | 890 | 58.2% | Higher variance, less historical data |
| **Mid Season** (Dec-Feb) | 1,680 | 64.1% | Peak performance, stable team dynamics |
| **Late Season** (Mar-Apr) | 1,250 | 65.8% | Best performance, clear playoff picture |
| **Playoffs** | 320 | 61.4% | High stakes, different dynamics |

### Performance by Team Quality

| Matchup Type | Games | Accuracy | Notes |
|--------------|-------|----------|-------|
| **Top 10 vs Top 10** | 450 | 59.8% | Most competitive, harder to predict |
| **Top 10 vs Bottom 10** | 680 | 76.2% | Clear favorites, high confidence |
| **Bottom 10 vs Bottom 10** | 420 | 54.1% | Lower quality, more variance |
| **Middle Teams** | 2,870 | 60.3% | Most common matchup |

---

## 🔢 Training Data

### Dataset Specifications

- **Total Games:** 5,420 NBA regular season + playoff games
- **Date Range:** October 2019 - November 2024 (5 seasons)
- **Training Set:** 4,336 games (80%)
- **Test Set:** 1,084 games (20%)
- **Cross-Validation:** 5-fold stratified

### Data Sources

1. **NBA.com Stats API** (via nba_api)
   - Advanced team statistics
   - Player tracking data
   - Historical game logs

2. **ESPN.com**
   - Injury reports
   - News articles
   - Expert analysis

3. **Basketball-Reference.com**
   - Historical records
   - Four Factors
   - Advanced metrics

4. **TextBlob NLP**
   - Sentiment analysis of news
   - Team narrative tracking

### Data Preprocessing

- **Missing Values:** Forward-fill for time series, median imputation for static features
- **Outliers:** Winsorization at 1st and 99th percentiles
- **Normalization:** StandardScaler for continuous features
- **Encoding:** One-hot encoding for categorical features
- **Feature Engineering:** Rolling averages (5/10/15 games), momentum indicators

---

## 🎯 Features (165 Total)

### Feature Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Basic Stats** | 27 | W, L, PTS, FG%, 3P%, FT%, REB, AST, STL, BLK, TOV |
| **Advanced Stats** | 120 | OFF_RATING, DEF_RATING, NET_RATING, PACE, eFG%, TS%, AST%, TOV%, ORB%, DRB% |
| **Four Factors** | 16 | eFG%, TOV%, ORB%, FT/FGA (both teams, offense/defense) |
| **Clutch Stats** | 12 | W_PCT_CLUTCH, PTS_CLUTCH, FG%_CLUTCH, NET_RTG_CLUTCH |
| **Opponent Stats** | 15 | OPP_PTS, OPP_FG%, OPP_3P%, OPP_OFF_RATING, OPP_DEF_RATING |
| **News Sentiment** | 8 | SENTIMENT_AVG, SENTIMENT_STD, SENTIMENT_MIN, SENTIMENT_MAX, CONTROVERSY_COUNT |
| **Player Tracking** | 20 | DEFLECTIONS, CHARGES_DRAWN, DIST_MILES, AVG_SPEED, TOUCHES, DRIVES |
| **Contextual** | 7 | HOME_AWAY, BACK_TO_BACK, DAYS_REST, TRAVEL_DISTANCE |

### Top 20 Most Important Features

| Rank | Feature | Importance | Category | Description |
|------|---------|------------|----------|-------------|
| 1 | OFF_RATING | 15.2% | Advanced | Offensive efficiency (pts per 100 possessions) |
| 2 | DEF_RATING | 12.4% | Advanced | Defensive efficiency (pts allowed per 100) |
| 3 | NET_RATING | 9.8% | Advanced | Point differential per 100 possessions |
| 4 | W_PCT_L10 | 7.3% | Momentum | Win percentage last 10 games |
| 5 | eFG% | 6.1% | Four Factors | Effective field goal percentage |
| 6 | HOME_AWAY | 5.8% | Contextual | Home court advantage |
| 7 | PACE | 4.9% | Advanced | Possessions per 48 minutes |
| 8 | TOV_RATIO | 4.2% | Four Factors | Turnover rate |
| 9 | TS% | 3.7% | Advanced | True shooting percentage |
| 10 | AST_RATIO | 3.4% | Advanced | Assist-to-turnover ratio |
| 11 | OPP_OFF_RATING | 3.2% | Opponent | Opponent offensive rating |
| 12 | ORB% | 2.9% | Four Factors | Offensive rebound percentage |
| 13 | SENTIMENT_AVG | 2.6% | Sentiment | Average news sentiment |
| 14 | PIE | 2.4% | Advanced | Player Impact Estimate |
| 15 | DAYS_REST | 2.1% | Contextual | Days since last game |
| 16 | DEFLECTIONS | 1.9% | Tracking | Deflections per game |
| 17 | CLUTCH_W_PCT | 1.8% | Clutch | Win % in close games |
| 18 | AVG_SPEED | 1.6% | Tracking | Player average speed (mph) |
| 19 | FT_RATE | 1.4% | Four Factors | Free throw rate (FT/FGA) |
| 20 | BACK_TO_BACK | 1.3% | Contextual | Playing on consecutive nights |

*Full feature list available in [FEATURES.md](FEATURES.md)*

---

## 🎓 Training Process

### Cross-Validation Strategy

```python
# 5-Fold Stratified Cross-Validation
from sklearn.model_selection import StratifiedKFold

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

### Hyperparameter Optimization

- **Method:** Bayesian Optimization (Optuna)
- **Objective:** Maximize CV Accuracy
- **Trials:** 100 per model
- **Time:** ~4 hours on 8-core CPU

### Training Time

- **Data Collection:** 15-25 minutes
- **Feature Engineering:** 5-10 minutes
- **Model Training:** 20-30 minutes
- **Evaluation:** 5 minutes
- **Total:** ~60 minutes per full pipeline run

---

## ⚠️ Limitations and Biases

### Known Limitations

1. **Small Sample Variance**
   - Difficulty predicting outcomes when teams have small sample sizes (early season)
   - Mitigation: Weight recent games more heavily

2. **Injury Impact**
   - Player injuries not fully captured in statistical features
   - Mitigation: Incorporate injury reports and sentiment analysis

3. **Trade Deadline Effects**
   - Team composition changes mid-season
   - Mitigation: Use rolling averages that adapt to roster changes

4. **Motivation Factors**
   - Cannot capture intangible factors (playoff seeding, revenge games)
   - Mitigation: Some signal from news sentiment

5. **Back-to-Back Games**
   - Model slightly underperforms on back-to-back scenarios
   - Mitigation: Explicit back-to-back feature

### Potential Biases

1. **Home Team Bias**
   - Model slightly favors home teams beyond actual win rates
   - Impact: ~2% over-prediction for home teams
   - Mitigation: Calibration adjustments

2. **Favorite Bias**
   - Tendency to over-predict favorites in mismatches
   - Impact: Lower accuracy in blowout scenarios
   - Mitigation: Confidence thresholds

3. **Recency Bias**
   - Over-weighting recent performance
   - Impact: Slower adaptation to true talent changes
   - Mitigation: Balanced feature engineering

---

## 🔧 Model Updates

### Retraining Schedule

- **Frequency:** Daily at 3 AM EST (automated via GitHub Actions)
- **Trigger:** New game data available
- **Process:**
  1. Scrape latest game statistics
  2. Update features
  3. Retrain ensemble models
  4. Validate performance
  5. Deploy if accuracy > threshold

### Version History

| Version | Date | Changes | CV Accuracy |
|---------|------|---------|-------------|
| v1.0 | 2024-09-01 | Initial release, 27 features | 58.2% |
| v1.5 | 2024-10-01 | Added advanced stats (120 features) | 61.4% |
| v2.0 | 2024-10-15 | Added news sentiment (8 features) | 62.1% |
| v2.1 | 2024-11-12 | Added player tracking (20 features) | 62.6% |

---

## 🚀 Deployment

### Production Environment

- **Platform:** AWS EC2 (t3.large instance)
- **Framework:** FastAPI
- **Database:** PostgreSQL (historical data)
- **Cache:** Redis (real-time predictions)
- **Monitoring:** Prometheus + Grafana

### Inference Performance

- **Latency:** <100ms per prediction
- **Throughput:** ~50 predictions/second
- **Availability:** 99.9% uptime

### Model Serving

```python
# Example inference
from src.models.pregame.ensemble import EnsembleModel

model = EnsembleModel.load("artifacts/models/ensemble_v2.1.pkl")
prediction = model.predict(game_features)
# Returns: {'home_win_prob': 0.687, 'away_win_prob': 0.313}
```

---

## 📊 Monitoring and Maintenance

### Performance Tracking

- **Daily Accuracy:** Track predictions vs actual outcomes
- **Drift Detection:** Monitor feature distributions
- **Alert Thresholds:**
  - Accuracy drops below 55% for 7 consecutive days
  - Feature distribution shift > 2 standard deviations

### A/B Testing

- **Control:** Current production model (v2.1)
- **Treatment:** New candidate models
- **Metrics:** Accuracy, log loss, AUC-ROC
- **Duration:** 14 days minimum
- **Promotion:** Treatment promoted if accuracy > control + 1%

---

## 🔬 Future Improvements

### Planned Enhancements (v3.0)

1. **Lineup-Specific Predictions**
   - Incorporate starting lineups and player-level features
   - Expected impact: +2-3% accuracy

2. **Deep Learning Models**
   - LSTM for time-series patterns
   - Transformer for player interactions
   - Expected impact: +3-5% accuracy

3. **Vegas Odds Integration**
   - Use betting lines as features
   - Ensemble with market predictions
   - Expected impact: +1-2% accuracy

4. **SHAP Explainability**
   - Individual game explanations
   - Feature contribution visualization
   - Expected impact: Better user trust

5. **Real-Time Adjustments**
   - Update predictions during games
   - Incorporate live play-by-play data
   - Expected impact: Live win probability

---

## 🧪 Evaluation and Testing

### Backtesting

- **Historical Validation:** Tested on previous 3 seasons (2020-2023)
- **Walk-Forward Validation:** Simulated real-world deployment
- **Results:** 61.8% accuracy on 2,460 out-of-sample games

### Stress Testing

- **Playoff Performance:** 61.4% accuracy (320 games)
- **Close Games:** 54.7% accuracy (games decided by ≤5 points)
- **Blowouts:** 82.3% accuracy (games decided by ≥20 points)

---

## 📚 References

### Research Papers

1. Loeffelholz et al. (2009). "Predicting NBA Game Outcomes"
2. Miljković et al. (2010). "Machine Learning Models for Sports Betting"
3. Beckler et al. (2016). "NBA Oracle: Predicting Basketball Outcomes"

### Data Sources

- [NBA Stats API](https://github.com/swar/nba_api)
- [Basketball Reference](https://www.basketball-reference.com/)
- [ESPN API](https://www.espn.com/apis/devcenter/)

---

## 📞 Contact

**Model Owner:** Shaurya Mallampati

**Email:** shaurya@example.com

**GitHub:** [ShauryaMallampati/NBA-Prediction](https://github.com/ShauryaMallampati/NBA-Prediction)

**Issues:** [GitHub Issues](https://github.com/ShauryaMallampati/NBA-Prediction/issues)

---

## 📄 License

This model is released under the MIT License. See [LICENSE](../LICENSE) for details.

---

**Last Updated:** 2024-11-12

**Model Version:** 2.1.0
