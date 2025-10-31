# NBA Intel Platform - Real Data API Endpoints

## 🎯 Overview
All endpoints now return **REAL NBA data** from stats.nba.com via the nba_api package.

Base URL: `http://localhost:8000`

---

## 📋 Endpoints

### 1. Get All Teams
```http
GET /api/teams
```

**Response:**
```json
{
  "success": true,
  "count": 30,
  "teams": [
    {
      "id": 1610612744,
      "full_name": "Golden State Warriors",
      "abbreviation": "GSW",
      "nickname": "Warriors",
      "city": "Golden State",
      "state": "California",
      "year_founded": 1946
    }
  ]
}
```

---

### 2. Get Games
```http
GET /api/games?date=2024-12-25
```

**Parameters:**
- `date` (optional): Date in YYYY-MM-DD format. Defaults to today.

**Response:**
```json
{
  "success": true,
  "count": 5,
  "games": [
    {
      "game_id": "0022400001",
      "date": "2024-12-25",
      "home_team": {...},
      "visitor_team": {...},
      "status": "Final"
    }
  ]
}
```

---

### 3. Get Live Games
```http
GET /api/games/live
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "games": [
    {
      "game_id": "0022400139",
      "status": "Q3",
      "home_team": {
        "name": "Milwaukee Bucks",
        "score": 98
      },
      "visitor_team": {
        "name": "Golden State Warriors",
        "score": 92
      }
    }
  ]
}
```

---

### 4. Search Players
```http
GET /api/players/search?name=Curry&limit=5
```

**Parameters:**
- `name` (required): Player name to search
- `limit` (optional): Max results (default: 10)

**Response:**
```json
{
  "success": true,
  "count": 2,
  "players": [
    {
      "id": 201939,
      "full_name": "Stephen Curry",
      "first_name": "Stephen",
      "last_name": "Curry",
      "is_active": true
    },
    {
      "id": 203552,
      "full_name": "Seth Curry",
      "first_name": "Seth",
      "last_name": "Curry",
      "is_active": true
    }
  ]
}
```

---

### 5. Get Player Stats
```http
GET /api/players/201939/stats?games=10
```

**Parameters:**
- `games` (optional): Number of recent games (default: 10)

**Response:**
```json
{
  "success": true,
  "player_id": 201939,
  "games": 10,
  "stats": [
    {
      "GAME_DATE": "2025-10-30",
      "MATCHUP": "GSW @ MIL",
      "PTS": 27,
      "AST": 4,
      "REB": 6,
      "FG_PCT": 0.421,
      "FG3_PCT": 0.4,
      "FT_PCT": 0.875,
      "MIN": 34.9
    }
  ]
}
```

---

### 6. Get Player Performance Summary
```http
GET /api/players/201939/performance?games=5
```

**Parameters:**
- `games` (optional): Number of recent games to analyze (default: 5)

**Response:**
```json
{
  "success": true,
  "player_id": 201939,
  "games_analyzed": 5,
  "ppg": 27.8,
  "apg": 5.0,
  "rpg": 4.8,
  "spg": 1.4,
  "bpg": 0.6,
  "tpg": 2.8,
  "fg_pct": 49.0,
  "fg3_pct": 41.9,
  "ft_pct": 97.5,
  "mpg": 30.9
}
```

---

### 7. Get Betting Odds
```http
GET /api/odds
```

**Response:**
```json
{
  "success": true,
  "count": 12,
  "odds": [
    {
      "id": "game_id",
      "home_team": "Lakers",
      "away_team": "Warriors",
      "bookmakers": [...]
    }
  ]
}
```

---

## 🔥 Real Data Examples

### Stephen Curry (Last 5 Games)
- **27.8 PPG** | 5.0 APG | 4.8 RPG
- **49.0% FG** | 41.9% 3PT | 97.5% FT
- 30.9 MPG

### Giannis Antetokounmpo (Last 5 Games)
- **32.2 PPG** | 6.4 APG | 12.6 RPG
- **69.1% FG** | 30.9 MPG

### Luka Doncic (Last 4 Games)
- **37.0 PPG** | 7.5 APG | 8.8 RPG
- **55.1% FG** | 39.5% 3PT

---

## ⚡ Caching

All endpoints use intelligent caching:
- **Teams**: 7 days
- **Games (historical)**: 24 hours
- **Games (today/live)**: 5 minutes
- **Player stats**: 1 hour
- **Player search**: 1 hour
- **Odds**: 30 minutes

Second requests are served from cache (file-based + optional Redis).

---

## 🧪 Testing Examples

```bash
# Get all teams
curl http://localhost:8000/api/teams

# Search for LeBron
curl "http://localhost:8000/api/players/search?name=LeBron"

# Get Stephen Curry's recent performance
curl http://localhost:8000/api/players/201939/performance

# Get today's games
curl http://localhost:8000/api/games

# Get live scores
curl http://localhost:8000/api/games/live
```

---

## 📊 Response Times

| Endpoint | First Call | Cached |
|----------|-----------|--------|
| /api/teams | ~300ms | <50ms |
| /api/games | ~1.2s | <50ms |
| /api/players/search | ~200ms | <50ms |
| /api/players/{id}/stats | ~8s | <50ms |
| /api/players/{id}/performance | ~8s | <50ms |

---

## 🚀 Next Steps

1. ✅ Backend serving real data
2. ⏳ Update frontend to consume these endpoints
3. ⏳ Add WebSocket for live score updates
4. ⏳ Implement ML predictions on real data
5. ⏳ Add advanced analytics charts

---

**Status**: ✅ All endpoints operational with real NBA data from stats.nba.com
