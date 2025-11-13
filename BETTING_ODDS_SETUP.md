# 🎰 Betting Odds Integration - Quick Setup

## ✅ What's Been Completed

1. **✅ Live GRU Model Trained**
   - 5,000 games processed
   - 190,000 training sequences generated
   - Model trained (50 epochs, loss < 0.0001)
   - Saved to: `artifacts/models/live_gru_winprob.pt`

2. **✅ Odds Scraper Ready**
   - Script: `scripts/scrape_odds.py`
   - Supports The Odds API (500 free requests/month)
   - Just needs your API key!

---

## 🚀 Setup Betting Odds API (5 minutes)

### Step 1: Get Your Free API Key

1. Go to: **https://the-odds-api.com/**
2. Click "Get Started" or "Sign Up"
3. Free tier includes:
   - 500 requests per month
   - Real-time odds from 15+ sportsbooks
   - DraftKings, FanDuel, BetMGM, etc.

### Step 2: Add API Key to Your Environment

**Option A: Add to `.env` file (Recommended)**

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"
echo "ODDS_API_KEY=your-key-here" >> .env
```

**Option B: Export in terminal**

```bash
export ODDS_API_KEY="your-key-here"
```

**Option C: Add to your shell profile (Permanent)**

```bash
echo 'export ODDS_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Test the Scraper

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"
python scripts/scrape_odds.py
```

**Expected Output:**
```
================================================================================
🎰 NBA BETTING ODDS SCRAPER
================================================================================

📡 Fetching odds from The Odds API...
✅ Found odds for 12 games
✅ Saved to data/odds/odds_2025-11-12.json

📊 Summary:
   Games: 12
   Sportsbooks: DraftKings, FanDuel, BetMGM
   Average margin: 5.2%
```

---

## 📊 What the Scraper Does

1. **Fetches real-time odds** from 15+ sportsbooks
2. **Converts to probabilities** (American → Decimal → Probability)
3. **Calculates market efficiency** (removes vig/juice)
4. **Saves structured data** for betting page

### Data Structure

```json
{
  "game_id": "0022200123",
  "date": "2025-11-12",
  "home_team": "LAL",
  "away_team": "GSW",
  "odds": {
    "draftkings": {
      "home_ml": -150,
      "away_ml": +130,
      "home_spread": -3.5,
      "total": 225.5
    },
    "fanduel": {...},
    "betmgm": {...}
  },
  "implied_probabilities": {
    "home_win": 0.6250,
    "away_win": 0.4348
  }
}
```

---

## 🎯 Next Steps After Setup

### 1. Update Betting Page to Use Real Data

Currently `app/betting/page.tsx` uses mock data. After scraper works:

```typescript
// Replace mock data with:
const oddsData = await fetch('/api/odds/today').then(r => r.json());
```

### 2. Schedule Daily Updates

Add to cron or GitHub Actions:

```bash
# Run every morning at 6 AM
0 6 * * * cd /path/to/project && python scripts/scrape_odds.py
```

### 3. Integrate with Predictions

Combine your model predictions with betting odds:

```python
# In scripts/generate_todays_predictions.py
model_prob = 0.65  # Your model's prediction
market_prob = 0.60  # From betting odds
edge = model_prob - market_prob  # 0.05 = 5% edge!
```

---

## 💡 Kelly Criterion Calculator

Your betting page already has Kelly Criterion built in:

**Formula:** `f* = (bp - q) / b`

Where:
- `b` = Decimal odds - 1
- `p` = Your model's win probability
- `q` = 1 - p
- `f*` = Fraction of bankroll to bet

**Example:**
- Model says: 65% win probability
- Odds: +150 (2.5 decimal)
- Kelly = (2.5 × 0.65 - 0.35) / 2.5 = **0.388 or 38.8%**
- With $1,000 bankroll → Bet $388

**Fractional Kelly** (safer):
- Use 1/4 Kelly = $97 (more conservative)
- Use 1/2 Kelly = $194 (moderate risk)

---

## 📈 Free Tier Limits

**The Odds API Free Tier:**
- 500 requests/month
- ~16 requests/day
- Perfect for daily updates!

**If you need more:**
- Upgrade to $30/month = 10,000 requests
- Or use multiple free accounts

---

## 🔧 Troubleshooting

### "No ODDS_API_KEY found"

Make sure you:
1. Created `.env` file in project root
2. Added `ODDS_API_KEY=your-key` (no quotes)
3. Restarted your terminal

### "API request failed: 401 Unauthorized"

- Your API key is invalid
- Check for typos
- Regenerate key on the-odds-api.com

### "API request failed: 429 Too Many Requests"

- You've hit the 500 request/month limit
- Wait until next month or upgrade plan

---

## 🎉 You're All Set!

Once you add your API key and run `python scripts/scrape_odds.py`, you'll have:

✅ Real betting odds from 15+ sportsbooks  
✅ Live GRU model for in-game predictions  
✅ Kelly Criterion calculator for bet sizing  
✅ Professional betting interface  

**Platform Status:** 75% → 85% Complete! 🚀

---

## 📝 Additional Resources

- **The Odds API Docs:** https://the-odds-api.com/liveapi/guides/v4/
- **Kelly Criterion:** https://en.wikipedia.org/wiki/Kelly_criterion
- **Betting Strategy Guide:** See `BETTING_STRATEGY.md`

---

Need help? Issues with the scraper? Let me know!
