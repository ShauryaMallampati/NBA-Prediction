# API Documentation

Backend API reference for pregame predictions.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/health`

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "models_loaded": true
}
```

### Pregame Predictions

**GET** `/predictions`

Query params:
- `date` (optional, YYYY-MM-DD)
- `home_team` (optional, team abbreviation)
- `away_team` (optional, team abbreviation)

Response:

```json
[
  {
    "game_id": "0022400145",
    "date": "2024-11-12",
    "home_team": "BOS",
    "away_team": "LAL",
    "home_win_prob": 0.687,
    "away_win_prob": 0.313,
    "top_features": {
      "home_elo": {"importance": 0.12, "value": 1623.4}
    }
  }
]
```
