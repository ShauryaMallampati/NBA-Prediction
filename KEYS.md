# API Keys & Data Sources Guide

This document lists all required API keys, their purposes, rate limits, and where to obtain them.

## 🏀 NBA Data

### NBA Stats API
- **Environment Variable:** `NBA_STATS_API_KEY`
- **Purpose:** Historical box scores, play-by-play data, player stats
- **Provider:** RapidAPI (NBA API) or stats.nba.com
- **Signup URL:** https://rapidapi.com/api-sports/api/api-nba
- **Rate Limits:** 100 requests/day (free tier), 500/day (basic)
- **Scopes:** Read-only access to game data
- **Test Command:**
  \`\`\`bash
  curl -X GET "https://api-nba-v1.p.rapidapi.com/games?date=2024-01-15" \
    -H "X-RapidAPI-Key: YOUR_KEY_HERE" \
    -H "X-RapidAPI-Host: api-nba-v1.p.rapidapi.com"
  \`\`\`

**Alternative:** Basketball-Reference scraping (no key required, but respect rate limits)

---

## 🌍 Travel & Geography

### OpenRouteService API
- **Environment Variable:** `ORS_API_KEY`
- **Purpose:** Calculate travel distances, time zones, elevation between cities
- **Provider:** OpenRouteService
- **Signup URL:** https://openrouteservice.org/dev/#/signup
- **Rate Limits:** 2,000 requests/day (free tier)
- **Scopes:** Directions API, Geocoding
- **Test Command:**
  \`\`\`bash
  curl -X GET "https://api.openrouteservice.org/v2/directions/driving-car?api_key=YOUR_KEY&start=8.681495,49.41461&end=8.687872,49.420318"
  \`\`\`

---

## 📱 Social Media APIs

### X/Twitter API v2
- **Environment Variable:** `X_BEARER_TOKEN`
- **Purpose:** Team mentions, player sentiment, trending topics
- **Provider:** Twitter Developer Portal
- **Signup URL:** https://developer.twitter.com/en/portal/dashboard
- **Rate Limits:** 
  - Essential: 500k tweets/month
  - Elevated: 2M tweets/month
- **Scopes:** `tweet.read`, `users.read`
- **Test Command:**
  \`\`\`bash
  curl -X GET "https://api.twitter.com/2/tweets/search/recent?query=Lakers" \
    -H "Authorization: Bearer YOUR_BEARER_TOKEN"
  \`\`\`

### Reddit API
- **Environment Variables:** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- **Purpose:** r/nba discussions, player sentiment, injury news
- **Provider:** Reddit Apps
- **Signup URL:** https://www.reddit.com/prefs/apps
- **Rate Limits:** 60 requests/minute
- **Scopes:** `read`, `identity`
- **Test Command:**
  \`\`\`bash
  curl -X POST "https://www.reddit.com/api/v1/access_token" \
    -u "CLIENT_ID:CLIENT_SECRET" \
    -d "grant_type=client_credentials"
  \`\`\`

### YouTube Data API
- **Environment Variable:** `YOUTUBE_API_KEY`
- **Purpose:** Highlight videos, player interviews, sentiment from comments
- **Provider:** Google Cloud Console
- **Signup URL:** https://console.cloud.google.com/apis/library/youtube.googleapis.com
- **Rate Limits:** 10,000 units/day (free tier)
- **Scopes:** YouTube Data API v3
- **Test Command:**
  \`\`\`bash
  curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=NBA+highlights&key=YOUR_KEY"
  \`\`\`

---

## 💰 Odds & Betting (Optional)

### The Odds API
- **Environment Variable:** `ODDS_API_KEY`
- **Purpose:** Closing lines, market sentiment features
- **Provider:** The Odds API
- **Signup URL:** https://the-odds-api.com/
- **Rate Limits:** 500 requests/month (free tier)
- **Scopes:** NBA odds, spreads, totals
- **Test Command:**
  \`\`\`bash
  curl "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey=YOUR_KEY&regions=us"
  \`\`\`

---

## ✅ Key Audit Checklist

Run `make key-audit` to verify all keys are present and functional. The system will:

1. ✓ Check each environment variable is set
2. ✓ Ping each API endpoint to verify authentication
3. ✓ Report rate limit status where available
4. ✗ Fail fast if `REQUIRE_REAL_DATA=true` and keys are missing

---

## 🔒 Security Notes

- **Never commit `.env` to version control**
- Store production keys in secure vaults (Vercel, AWS Secrets Manager, etc.)
- Rotate keys regularly
- Use read-only scopes where possible
- Monitor API usage to avoid unexpected charges

---

## 📊 Data Usage Compliance

- Respect each provider's Terms of Service
- Implement rate limiting and backoff strategies
- Cache responses to minimize API calls
- Aggregate social data; do not store PII
- See `DATA_USE.md` for ethical guidelines
