# Quick Start Guide: NBA RapidAPI Integration

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Setup

Your RapidAPI key is already configured:
```bash
# Check .env file
cat .env | grep NBA_STATS_API_KEY
```

### Step 2: Test the Integration

```bash
cd /Users/shauryamallampati/Desktop/NBA\ prediction
python scripts/test_rapid_api.py
```

This will test all 14 NBA APIs and ~80 endpoints.

### Step 3: Collect Data

#### Option A: Interactive Menu
```bash
python scripts/collect_nba_data.py
```

Then select:
- `1` - Today's data snapshot
- `7` - Complete comprehensive collection

#### Option B: Python Script
```python
from scripts.collect_nba_data import NBADataCollector

collector = NBADataCollector()

# Collect today's data
data = collector.collect_daily_snapshot()

# Or collect everything
collector.collect_daily_snapshot()
collector.collect_season_data("2024")
collector.collect_betting_training_data()
collector.create_training_dataset()
```

### Step 4: Use in Your Code

```python
from src.services.api.rapid_api_client import rapid_api_client

# Get today's games and odds
scoreboard = rapid_api_client.get_nba_scoreboard()
odds = rapid_api_client.get_nba_odds()
injuries = rapid_api_client.get_injury_reports()

# Get player data
players = rapid_api_client.get_all_players(search="lebron")
stats = rapid_api_client.get_daily_leaders()

# Get betting data
events = rapid_api_client.get_events_for_today()
markets = rapid_api_client.get_all_markets()
```

---

## 📊 Available Data

### 1. Game Data
- Live scores and box scores
- Schedule (full season)
- Historical games
- Quarter-by-quarter stats

### 2. Player Data
- Rosters and bios
- Game-by-game stats
- Season statistics
- Daily leaders
- Fantasy projections

### 3. Team Data
- Team info and rosters
- Standings
- Schedule
- Season performance

### 4. Betting Data
- Live odds (moneyline, spreads, totals)
- Player props (points, rebounds, assists)
- Futures (championship, MVP)
- Multiple bookmakers
- Historical odds

### 5. Injury Data
- Real-time injury reports
- Player status (Out, Questionable, Probable)
- Updated 3x daily

### 6. News & Media
- Latest articles from ESPN, Yahoo, Bleacher Report
- Team-specific news
- Player updates

---

## 🎯 Common Use Cases

### Use Case 1: Daily Predictions
```python
from src.data.ingest.enhanced_rapid_api import enhanced_ingestion

# Get today's complete dataset
data = enhanced_ingestion.fetch_complete_dataset()

# Extract features
games = data["games"]
injuries = data["injuries"]
odds = data["betting"]["live_odds"]

# Make predictions with your model
predictions = your_model.predict(games, injuries, odds)
```

### Use Case 2: Training Data Collection
```python
from scripts.collect_nba_data import NBADataCollector

collector = NBADataCollector()

# Collect last 30 days
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=30)

collector.collect_historical_data(
    start.strftime("%Y-%m-%d"),
    end.strftime("%Y-%m-%d"),
    save_interval=1
)

# Create consolidated training set
collector.create_training_dataset()
```

### Use Case 3: Betting Strategy Backtesting
```python
# Get historical games with real odds
backtest_data = rapid_api_client.get_sim_month()

# Test your strategy
for game in backtest_data["games"]:
    prediction = your_model.predict(game)
    actual = game["result"]
    # Calculate profit/loss
```

### Use Case 4: Player Prop Analysis
```python
# Get today's events
events = rapid_api_client.get_events_for_today()

# Get props for each event
for event in events["events"]:
    props = rapid_api_client.get_player_odds_for_event(event["id"])
    
    # Analyze player vs line
    for player_prop in props:
        player_stats = rapid_api_client.get_all_stats(
            player_ids=[player_prop["player_id"]]
        )
        # Your analysis here
```

---

## 📁 Output Files

All data is saved to:
```
data/raw/rapid_api/
├── nba_snapshot_2024-11-16.json       # Daily snapshot
├── nba_season_2024_2025.json          # Season data
├── nba_betting_training_data.json     # Betting backtest data
├── nba_team_lakers.json                # Team-specific
└── nba_player_lebron_james.json       # Player-specific

data/processed/
└── nba_training_dataset.json          # Consolidated training data
```

---

## 🔧 Integration with Existing Code

### Replace Old API Calls

**Before:**
```python
# Old way
from nba_api import stats

games = stats.scoreboard.get_games()
```

**After:**
```python
# New unified way
from src.services.api.rapid_api_client import rapid_api_client

games = rapid_api_client.get_nba_scoreboard()
```

### Use Enhanced Ingestion

**Before:**
```python
# Multiple API calls
game_data = fetch_games()
player_data = fetch_players()
odds_data = fetch_odds()
injury_data = fetch_injuries()
```

**After:**
```python
# One call gets everything
from src.data.ingest.enhanced_rapid_api import enhanced_ingestion

complete_data = enhanced_ingestion.fetch_complete_dataset(
    include_historical=True
)
```

---

## 🎓 Training Your Models

### Collect Training Data
```bash
# Run the comprehensive data collection
python scripts/collect_nba_data.py
# Select option 7

# This will collect:
# - Today's games, scores, odds
# - Current season data
# - Betting backtest data
# - And create consolidated training dataset
```

### Load Training Data
```python
import json

# Load consolidated dataset
with open("data/processed/nba_training_dataset.json") as f:
    training_data = json.load(f)

# Extract features for your model
games = []
for dataset in training_data["datasets"]:
    if "games" in dataset["data"]:
        games.extend(dataset["data"]["games"])

# Train your model
X, y = prepare_features(games)
model.fit(X, y)
```

---

## ⚡ Performance Tips

1. **Cache responses**: Save API responses to avoid repeated calls
2. **Batch requests**: Collect multiple days at once
3. **Use pagination**: Get more data per request
4. **Schedule collection**: Run during off-peak hours
5. **Monitor rate limits**: Track your API usage

---

## 📊 Data Monitoring

Check your data quality:
```python
# View collection summary
with open("data/raw/rapid_api/historical_collection_summary.json") as f:
    summary = json.load(f)
    print(f"Collected {summary['total_days']} days")
    print(f"Date range: {summary['collection_period']}")
```

---

## 🚨 Troubleshooting

### Rate Limit Issues
```python
# Add delays between requests
import time

for date in date_range:
    collector.collect_daily_snapshot(date)
    time.sleep(1)  # 1 second delay
```

### Missing Data
```python
# Check what data is available
from src.services.api.rapid_api_client import rapid_api_client

# Test individual endpoint
result = rapid_api_client.get_nba_scoreboard()
if not result:
    print("No games scheduled for today")
```

---

## ✅ Next Steps

1. ✅ **APIs Integrated**: All 14 APIs, 80+ endpoints
2. ✅ **Data Collection**: Scripts ready
3. ✅ **Documentation**: Complete guide

**Now you can:**
- 🏀 Collect comprehensive NBA data
- 📊 Train models with real data
- 💰 Build betting strategies
- 🎯 Make accurate predictions

**Start collecting:**
```bash
python scripts/test_rapid_api.py        # Test everything
python scripts/collect_nba_data.py      # Collect data
```

---

## 📞 Support

- **API Issues**: Check RapidAPI dashboard
- **Code Issues**: Check logs in `logs/`
- **Documentation**: See `docs/RAPID_API_INTEGRATION.md`

---

**You're all set! Start building powerful NBA prediction models with comprehensive data! 🚀🏀**
