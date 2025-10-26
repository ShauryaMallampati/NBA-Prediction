# Keys

| Provider | Env Var(s) | Signup | Minimal Scope | Quick test |
|---------|-------------|--------|---------------|------------|
| NBA Stats | NBA_STATS_API_KEY | https://www.nba.com/stats/help/ | read | `curl -H "x-nba-stats-token:$NBA_STATS_API_KEY" "https://stats.nba.com/stats/scoreboardv3?GameDate=2024-10-25"` |
| X API v2 | X_BEARER_TOKEN | https://developer.x.com/ | tweets:read | `curl -H "Authorization: Bearer $X_BEARER_TOKEN" "https://api.x.com/2/tweets/search/recent?query=NBA"` |
| Reddit | REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET | https://www.reddit.com/prefs/apps/ | read | `curl -u $REDDIT_CLIENT_ID:$REDDIT_CLIENT_SECRET -d grant_type=client_credentials https://www.reddit.com/api/v1/access_token` |
| YouTube | YOUTUBE_API_KEY | https://console.cloud.google.com/apis | youtube.readonly | `curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=NBA&type=video&key=$YOUTUBE_API_KEY"` |
| OpenRouteService | ORS_API_KEY | https://openrouteservice.org/dev/ | directions | `curl -H "Authorization: $ORS_API_KEY" -H "Content-Type: application/json" -d '{"coordinates":[[-118.2673,34.0430],[-122.3877,37.7680]]}' https://api.openrouteservice.org/v2/directions/driving-car` |

Fail‑fast if `REQUIRE_REAL_DATA=true` and keys missing. Mock allowed only with `ALLOW_MOCK_DATA=true`.
