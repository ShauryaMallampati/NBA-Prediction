# 🔌 API Documentation

Complete API reference for the NBA Prediction Platform backend.

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Predictions](#predictions)
  - [Teams](#teams)
  - [Players](#players)
  - [Live Games](#live-games)
  - [Historical Data](#historical-data)
  - [Model Information](#model-information)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🌐 Base URL

```
http://localhost:8000/api/v1
```

Production: `https://your-domain.com/api/v1`

---

## 🔐 Authentication

Currently, the API is public. Future versions will include API key authentication.

```http
Authorization: Bearer YOUR_API_KEY
```

---

## 📡 Endpoints

### Predictions

#### Get Today's Predictions

Get predictions for all games today.

**Endpoint:** `GET /predictions/today`

**Response:**

```json
{
  "date": "2024-11-12",
  "games_count": 8,
  "predictions": [
    {
      "game_id": "0022400145",
      "date": "2024-11-12",
      "home_team": "BOS",
      "away_team": "LAL",
      "home_win_probability": 0.687,
      "away_win_probability": 0.313,
      "predicted_winner": "BOS",
      "confidence": "high",
      "spread": -7.5,
      "over_under": 223.5,
      "key_factors": [
        "Home court advantage",
        "Recent form (BOS 8-2 last 10)",
        "Head-to-head record (BOS 3-1)"
      ]
    }
  ]
}
```

#### Get Prediction for Specific Game

**Endpoint:** `GET /predictions/game/{game_id}`

**Parameters:**
- `game_id` (string): NBA game ID

**Response:**

```json
{
  "game_id": "0022400145",
  "date": "2024-11-12",
  "home_team": {
    "abbr": "BOS",
    "name": "Boston Celtics",
    "win_probability": 0.687
  },
  "away_team": {
    "abbr": "LAL",
    "name": "Los Angeles Lakers",
    "win_probability": 0.313
  },
  "predicted_winner": "BOS",
  "confidence": "high",
  "spread": -7.5,
  "over_under": 223.5,
  "key_factors": [
    {
      "factor": "Offensive Rating Differential",
      "impact": 0.12,
      "description": "BOS has significantly higher offensive efficiency"
    },
    {
      "factor": "Defensive Rating",
      "impact": 0.09,
      "description": "BOS allows fewer points per 100 possessions"
    }
  ],
  "feature_importance": {
    "offensive_rating": 0.15,
    "defensive_rating": 0.12,
    "pace": 0.08,
    "home_court": 0.06
  }
}
```

#### Get Predictions by Date

**Endpoint:** `GET /predictions/date/{date}`

**Parameters:**
- `date` (string): Date in YYYY-MM-DD format

**Response:** Same as Today's Predictions

---

### Teams

#### Get All Teams

**Endpoint:** `GET /teams`

**Response:**

```json
{
  "teams": [
    {
      "id": 1610612738,
      "abbr": "BOS",
      "name": "Boston Celtics",
      "conference": "East",
      "division": "Atlantic",
      "city": "Boston"
    }
  ]
}
```

#### Get Team Stats

**Endpoint:** `GET /teams/{team_abbr}/stats`

**Parameters:**
- `team_abbr` (string): Team abbreviation (e.g., "BOS")
- `season` (optional): Season year (default: current)

**Response:**

```json
{
  "team": "BOS",
  "season": "2024-25",
  "record": {
    "wins": 45,
    "losses": 20,
    "win_pct": 0.692
  },
  "offensive_stats": {
    "ppg": 118.2,
    "offensive_rating": 119.4,
    "effective_fg_pct": 0.564,
    "true_shooting_pct": 0.601,
    "pace": 99.8
  },
  "defensive_stats": {
    "opp_ppg": 108.7,
    "defensive_rating": 110.2,
    "opp_effective_fg_pct": 0.518
  },
  "advanced_stats": {
    "net_rating": 9.2,
    "offensive_rebound_pct": 0.278,
    "defensive_rebound_pct": 0.731,
    "assist_ratio": 18.5,
    "turnover_ratio": 12.3
  }
}
```

#### Get Team Recent Form

**Endpoint:** `GET /teams/{team_abbr}/form`

**Parameters:**
- `team_abbr` (string): Team abbreviation
- `last_n` (optional): Number of recent games (default: 10)

**Response:**

```json
{
  "team": "BOS",
  "last_n_games": 10,
  "record": {
    "wins": 8,
    "losses": 2,
    "win_pct": 0.8
  },
  "avg_point_diff": 8.4,
  "form_trend": "improving",
  "recent_games": [
    {
      "date": "2024-11-11",
      "opponent": "LAL",
      "result": "W",
      "score": "115-102",
      "point_diff": 13
    }
  ]
}
```

---

### Players

#### Get Player Stats

**Endpoint:** `GET /players/{player_id}/stats`

**Parameters:**
- `player_id` (integer): NBA player ID

**Response:**

```json
{
  "player_id": 1628369,
  "name": "Jayson Tatum",
  "team": "BOS",
  "position": "F",
  "stats": {
    "ppg": 27.8,
    "rpg": 8.2,
    "apg": 4.5,
    "fg_pct": 0.462,
    "three_pt_pct": 0.368,
    "ft_pct": 0.851,
    "per": 24.3,
    "true_shooting_pct": 0.587
  },
  "advanced_stats": {
    "usage_rate": 0.312,
    "offensive_rating": 119.2,
    "defensive_rating": 109.8,
    "vorp": 4.2,
    "win_shares": 8.7
  }
}
```

#### Get Player Injury Status

**Endpoint:** `GET /players/{player_id}/injury`

**Response:**

```json
{
  "player_id": 1628369,
  "name": "Jayson Tatum",
  "team": "BOS",
  "injury_status": "Healthy",
  "injury_description": null,
  "expected_return": null,
  "games_missed": 0
}
```

---

### Live Games

#### Get Live Scores

**Endpoint:** `GET /live/scores`

**Response:**

```json
{
  "games": [
    {
      "game_id": "0022400145",
      "status": "Live",
      "quarter": 3,
      "time_remaining": "7:45",
      "home_team": {
        "abbr": "BOS",
        "name": "Boston Celtics",
        "score": 82
      },
      "away_team": {
        "abbr": "LAL",
        "name": "Los Angeles Lakers",
        "score": 74
      },
      "current_win_probability": {
        "home": 0.78,
        "away": 0.22
      }
    }
  ]
}
```

#### Get Live Game Details

**Endpoint:** `GET /live/game/{game_id}`

**Parameters:**
- `game_id` (string): NBA game ID

**Response:**

```json
{
  "game_id": "0022400145",
  "status": "Live",
  "quarter": 3,
  "time_remaining": "7:45",
  "home_team": {
    "abbr": "BOS",
    "score": 82,
    "leaders": {
      "points": {"player": "Jayson Tatum", "value": 28},
      "rebounds": {"player": "Al Horford", "value": 9},
      "assists": {"player": "Jrue Holiday", "value": 7}
    }
  },
  "away_team": {
    "abbr": "LAL",
    "score": 74,
    "leaders": {
      "points": {"player": "LeBron James", "value": 24},
      "rebounds": {"player": "Anthony Davis", "value": 11},
      "assists": {"player": "LeBron James", "value": 6}
    }
  },
  "win_probability_timeline": [
    {"time": "12:00 Q1", "home": 0.50, "away": 0.50},
    {"time": "6:00 Q1", "home": 0.62, "away": 0.38},
    {"time": "0:00 Q1", "home": 0.68, "away": 0.32}
  ]
}
```

---

### Historical Data

#### Get Historical Predictions

**Endpoint:** `GET /historical/predictions`

**Parameters:**
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)
- `team` (optional): Filter by team abbreviation

**Response:**

```json
{
  "start_date": "2024-10-01",
  "end_date": "2024-11-11",
  "total_predictions": 156,
  "accuracy": 0.626,
  "predictions": [
    {
      "game_id": "0022400001",
      "date": "2024-10-01",
      "home_team": "BOS",
      "away_team": "LAL",
      "predicted_winner": "BOS",
      "actual_winner": "BOS",
      "correct": true,
      "home_win_prob": 0.687
    }
  ]
}
```

#### Get Model Performance

**Endpoint:** `GET /historical/performance`

**Parameters:**
- `metric` (optional): Specific metric (accuracy, precision, recall, f1, auc)

**Response:**

```json
{
  "model_version": "2.1.0",
  "last_updated": "2024-11-12T03:00:00Z",
  "training_data": {
    "games": 5420,
    "date_range": "2019-10-01 to 2024-11-11"
  },
  "performance": {
    "accuracy": 0.626,
    "precision": 0.641,
    "recall": 0.618,
    "f1_score": 0.629,
    "auc_roc": 0.694,
    "log_loss": 0.648
  },
  "by_confidence": {
    "high": {"count": 1245, "accuracy": 0.723},
    "medium": {"count": 2876, "accuracy": 0.614},
    "low": {"count": 1299, "accuracy": 0.524}
  },
  "by_team": [
    {"team": "BOS", "predictions": 82, "accuracy": 0.695},
    {"team": "LAL", "predictions": 82, "accuracy": 0.634}
  ]
}
```

---

### Model Information

#### Get Model Details

**Endpoint:** `GET /model/info`

**Response:**

```json
{
  "model_version": "2.1.0",
  "model_type": "Ensemble (XGBoost + LightGBM + CatBoost)",
  "last_trained": "2024-11-12T03:00:00Z",
  "features": {
    "total": 165,
    "categories": {
      "basic": 27,
      "advanced": 120,
      "sentiment": 8,
      "tracking": 10
    }
  },
  "training_config": {
    "cv_folds": 5,
    "test_size": 0.2,
    "random_state": 42
  },
  "feature_importance_top_10": [
    {"feature": "OFF_RATING", "importance": 0.152},
    {"feature": "DEF_RATING", "importance": 0.124},
    {"feature": "NET_RATING", "importance": 0.098}
  ]
}
```

#### Get Feature Importance

**Endpoint:** `GET /model/features`

**Parameters:**
- `top_n` (optional): Number of top features (default: 50)

**Response:**

```json
{
  "model_version": "2.1.0",
  "total_features": 165,
  "top_features": [
    {
      "name": "OFF_RATING",
      "importance": 0.152,
      "category": "advanced",
      "description": "Offensive rating (points per 100 possessions)"
    },
    {
      "name": "DEF_RATING",
      "importance": 0.124,
      "category": "advanced",
      "description": "Defensive rating (points allowed per 100 possessions)"
    }
  ]
}
```

---

## ⚠️ Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Game with ID 0022400999 not found",
    "status": 404,
    "timestamp": "2024-11-12T15:30:00Z"
  }
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## 🚦 Rate Limiting

- **Free tier**: 100 requests/hour
- **Authenticated**: 1000 requests/hour

Rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1699824000
```

---

## 📚 Example Usage

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get today's predictions
response = requests.get(f"{BASE_URL}/predictions/today")
predictions = response.json()

for game in predictions["predictions"]:
    print(f"{game['away_team']} @ {game['home_team']}")
    print(f"Winner: {game['predicted_winner']} ({game['home_win_probability']:.1%})")
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Get today's predictions
fetch(`${BASE_URL}/predictions/today`)
  .then(res => res.json())
  .then(data => {
    data.predictions.forEach(game => {
      console.log(`${game.away_team} @ ${game.home_team}`);
      console.log(`Winner: ${game.predicted_winner} (${(game.home_win_probability * 100).toFixed(1)}%)`);
    });
  });
```

### cURL

```bash
# Get today's predictions
curl -X GET "http://localhost:8000/api/v1/predictions/today"

# Get specific game prediction
curl -X GET "http://localhost:8000/api/v1/predictions/game/0022400145"

# Get team stats
curl -X GET "http://localhost:8000/api/v1/teams/BOS/stats"
```

---

## 🔄 Webhooks (Coming Soon)

Subscribe to real-time updates:

- Game predictions
- Live score updates
- Injury reports
- Model updates

---

## 📊 Data Freshness

- **Predictions**: Generated daily at 10 AM EST
- **Team stats**: Updated after each game
- **Player stats**: Updated daily at 2 AM EST
- **Injury reports**: Updated every 4 hours
- **Live scores**: Real-time (15-second polling)

---

## 🆘 Support

For API issues:
- Open an issue on [GitHub](https://github.com/ShauryaMallampati/NBA-Prediction/issues)
- Check [FAQ](docs/FAQ.md)
- Contact: support@your-domain.com

---

**Last Updated:** 2024-11-12
