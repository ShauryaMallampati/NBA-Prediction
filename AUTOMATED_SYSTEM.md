# 🤖 Automated Prediction System

## Quick Start

### 1️⃣ Make Predictions for Today's Games
```bash
python scripts/predict_today.py
```
**Output**: `predictions/predictions_2025-12-01.json`

### 2️⃣ Validate Yesterday's Predictions (Run after 1 AM)
```bash
python scripts/validate_predictions.py
```
**Output**: 
- Shows accuracy for yesterday's predictions
- Saves to `predictions/results/results_2025-11-30.json`
- Shows overall accuracy across all dates

### 3️⃣ Run Automated Agent (24/7 Operation)
```bash
python scripts/automated_agent.py
```
**Schedule**:
- ⏰ **09:00 AM Daily** - Make predictions for today's games
- ⏰ **01:00 AM Daily** - Validate yesterday's predictions
- ⏰ **02:00 AM Monday** - Collect new games for training
- ⏰ **03:00 AM Monday** - Retrain models with new data

### 4️⃣ Manual Continuous Training
```bash
python scripts/continuous_training.py
```
**What it does**:
- Collects 500 total games (adds to existing 250)
- Automatically retrains models
- Updates model version

---

## How It Works

### 🎯 Prediction Flow
1. Agent fetches today's NBA games from NBA API
2. Prepares pre-game features for each matchup
3. Gets predictions from 4 models (RF, GB, LR, Ensemble)
4. Saves predictions with confidence scores

**Example Prediction**:
```json
{
  "game_id": "0022400123",
  "home_team": "Lakers",
  "away_team": "Warriors",
  "home_win_prob": 0.67,
  "away_win_prob": 0.33,
  "predicted_winner": "Lakers",
  "confidence": 0.67
}
```

### 🔍 Validation Flow
1. Agent runs at 1 AM (after all games finished)
2. Fetches actual game scores from NBA API
3. Compares predictions vs actual results
4. Calculates daily accuracy
5. Updates overall accuracy report

**Example Validation**:
```json
{
  "date": "2025-12-01",
  "validated_games": 10,
  "correct_predictions": 7,
  "accuracy": 0.70
}
```

### 🔄 Continuous Learning
**Weekly Cycle**:
- Monday 2 AM: Collect past week's games
- Monday 3 AM: Retrain models with new data
- Models improve as more data is collected

**Growth Path**:
- Start: 250 games → 53% accuracy
- After 1 month: 500+ games → Improved accuracy
- After 3 months: 1000+ games → Production-ready

---

## Example Usage

### Day 1: Monday Morning
```bash
# Make predictions for today
$ python scripts/predict_today.py

🏀 NBA PREDICTIONS FOR TODAY
================================================================================
Found 8 games today
🎯 MAKING PREDICTIONS FOR TODAY'S GAMES

Game 1/8: Warriors @ Lakers
  ✅ Prediction: Lakers wins (67.3% confidence)
     Home: 67.3% | Away: 32.7%

Game 2/8: Celtics @ Heat
  ✅ Prediction: Celtics wins (58.1% confidence)
     Home: 41.9% | Away: 58.1%

...

💾 Saved predictions to: predictions/predictions_2025-12-01.json
```

### Day 2: Tuesday 1 AM (Automated)
```bash
# Validation runs automatically
🔍 PREDICTION VALIDATION AGENT
================================================================================
📂 Loading predictions from predictions/predictions_2025-12-01.json
🔍 Validating 8 predictions...

  Checking Warriors @ Lakers...
    ✅ CORRECT - Predicted: Lakers, Actual: Lakers
  
  Checking Celtics @ Heat...
    ❌ WRONG - Predicted: Celtics, Actual: Heat

...

✅ VALIDATION COMPLETE
Date: 2025-12-01
Games Validated: 8
Correct Predictions: 6
Accuracy: 75.0%

📊 OVERALL ACCURACY REPORT
2025-12-01: 6/8 (75.0%)
2025-12-02: 5/7 (71.4%)
2025-12-03: 8/10 (80.0%)

OVERALL ACCURACY: 19/25 (76.0%)
```

### Week 1: Monday 2 AM (Automated)
```bash
# Continuous training runs automatically
🔄 CONTINUOUS TRAINING SYSTEM
📊 STEP 1: Collecting More Games
🎯 Target: Collect 500 total games
📊 Current: 250 games
➕ Need to collect: 250 more games

📥 Fetching 500 games from NBA...
✅ Successfully collected play-by-play data

🎓 STEP 2: Retraining Models
Random Forest: 54.23% ± 5.12%
Gradient Boosting: 54.45% ± 4.98%
Logistic Regression: 47.89% ± 5.67%
Ensemble: 55.12% ± 4.85%

✅ CONTINUOUS TRAINING COMPLETE!
📊 Total Games: 500
🎓 Models retrained and saved
```

---

## File Structure

```
predictions/
├── predictions_2025-12-01.json      # Daily predictions
├── predictions_2025-12-02.json
└── results/
    ├── results_2025-12-01.json      # Daily validation results
    └── results_2025-12-02.json

logs/
└── automated_agent.log              # Agent activity log

models/ensemble/
├── pregame_models.pkl               # Production models
├── pregame_scaler.pkl
└── training_metadata.json           # Training history
```

---

## Production Deployment

### Option 1: Run Locally (Development)
```bash
# Start the automated agent
python scripts/automated_agent.py

# Let it run 24/7 in background
nohup python scripts/automated_agent.py > logs/agent.log 2>&1 &
```

### Option 2: Cloud Deployment (Production)
```bash
# Deploy to AWS/Azure/GCP
# Set up cron jobs for:
# - 9 AM: predictions
# - 1 AM: validation  
# - Weekly: retraining
```

### Option 3: Docker (Recommended)
```bash
# Build container
docker build -t nba-prediction-agent .

# Run agent
docker run -d --name nba-agent nba-prediction-agent
```

---

## Monitoring

### Check Agent Status
```bash
# View logs
tail -f logs/automated_agent.log

# Check predictions
ls -l predictions/

# View accuracy
python scripts/validate_predictions.py
```

### Performance Metrics
- **Prediction Accuracy**: Target 55-60% (better than random 50%)
- **Validation Lag**: < 2 hours after games finish
- **Training Frequency**: Weekly with 50+ new games
- **Model Update**: Automatic when accuracy improves

---

## Troubleshooting

### No games today
```
⚠️ No games today
```
**Solution**: Normal for NBA off-days. Agent will retry tomorrow.

### Validation fails
```
❌ No predictions found for 2025-12-01
```
**Solution**: Run predictions first before validation.

### Training fails
```
❌ Training failed: Insufficient data
```
**Solution**: Need at least 200 games. Run `collect_200_games.py` first.

---

## Next Steps

1. ✅ **Today**: Make predictions for today's games
2. ✅ **Tomorrow 1 AM**: Validate predictions automatically
3. ✅ **Next Week**: Collect 250 more games, retrain models
4. ⏳ **Next Month**: Deploy to cloud for 24/7 operation
5. ⏳ **Future**: Add betting odds, injury reports, live updates

---

## Commands Cheat Sheet

```bash
# Predictions
python scripts/predict_today.py              # Today's predictions

# Validation  
python scripts/validate_predictions.py       # Check yesterday's accuracy

# Automated Agent
python scripts/automated_agent.py            # Run 24/7

# Manual Training
python scripts/continuous_training.py        # Collect + retrain

# Original Training
python scripts/train_final.py                # Train from scratch
python scripts/verify_production_models.py   # Test models
```
