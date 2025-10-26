# 🎯 NBA Predictor - Quick Reference Card

## 📍 Current Status
- **Repository:** https://github.com/ShauryaMallampati/NBA-Prediciton
- **Location:** `/Users/shauryamallampati/Desktop/NBA prediction/`
- **Latest Commit:** 23a740a (Project refocus on player props)
- **Todo:** 32 tasks, betting-focused

---

## 🚀 Quick Start (5 steps)

```bash
# 1. Navigate to project
cd "/Users/shauryamallampati/Desktop/NBA prediction"

# 2. Activate environment
source venv/bin/activate

# 3. Fill in API keys
cp .env.example .env
nano .env  # Add ODDS_API_KEY first

# 4. Test connectivity
make key-audit

# 5. Start implementing
make seed  # Download data
```

---

## 📋 Core Tasks (Do in Order)

| # | Task | Est. Time | Status |
|---|------|-----------|--------|
| 8️⃣ | Setup .env with ODDS_API_KEY | 30 min | ⏳ |
| 9️⃣ | Run make key-audit | 15 min | ⏳ |
| 🔟 | Build player props features | 4 hours | ⏳ |
| 1️⃣1️⃣ | Implement Basketball-Reference scraper | 3 hours | ⏳ |
| 1️⃣2️⃣ | Build travel distance + fatigue scoring | 2 hours | ⏳ |
| 1️⃣3️⃣ | Player props feature pipeline | 3 hours | ⏳ |
| 1️⃣4️⃣ | Player-level Elo model | 2 hours | ⏳ |
| 1️⃣5️⃣ | Train LightGBM per-stat | 4 hours | ⏳ |
| 1️⃣6️⃣ | **CRITICAL:** Live odds comparison engine | 5 hours | 🔥 |
| 1️⃣7️⃣ | Blowout + rest risk detector | 3 hours | 🔥 |
| 1️⃣8️⃣ | **CRITICAL:** Betting performance tracker | 4 hours | 🔥 |

**Total MVP:** ~35 hours (1-2 weeks)

---

## 🔑 Key API Keys Needed

| Key | Priority | Purpose | Where to Get |
|-----|----------|---------|--------------|
| `ODDS_API_KEY` | 🔴 CRITICAL | Sportsbook odds | https://odds-api.com |
| `NBA_STATS_API_KEY` | 🔴 CRITICAL | Player stats | https://www.nba.com/stats/api |
| `ORS_API_KEY` | 🟡 HIGH | Rest/travel analysis | https://openrouteservice.org |
| `X_BEARER_TOKEN` | 🟢 OPTIONAL | Injury signals | X.com/developers |
| Others | 🟢 OPTIONAL | Not needed for MVP | - |

---

## 📊 Success Metrics (v1.0)

- ✅ 53%+ win rate on straight bets
- ✅ +$2,400+ ROI on $100 units (backtest)
- ✅ <5 recommended bets per day
- ✅ Model beats sportsbooks vs sharp odds
- ✅ <3 min daily workflow (check dashboard, click bets)

---

## 🎯 Three Key Features to Build

### 1. Player Props Predictor
```
Inputs: Recent form (11, 14, 25 pts), opponent, rest, blowout risk
Output: 55% probability Brown 25+ pts
```

### 2. Odds Comparison Engine (CORE VALUE)
```
Model: 55% | FanDuel: 50.5% implied | Sharp: 52% implied
Edge: +3% vs sharp (recommendation: OVER)
```

### 3. Betting Dashboard
```
Today's recommendations:
  1. Brown 25+ (55% conf, +3% edge, OVER)
  2. Luka 8+ AST (58% conf, +4% edge, OVER)
  3. Curry 3+ 3PM (60% conf, +5% edge, OVER)

Portfolio: 53.4% win rate | +$2,400 ROI | 876-771 record
```

---

## 📚 Key Documentation

| File | Purpose | Read When |
|------|---------|-----------|
| `BETTING_STRATEGY.md` | Full strategy guide (405 lines) | Understanding the approach |
| `REFOCUS_SUMMARY.md` | What changed & why | Quick update |
| `KEYS.md` | API key setup links | Getting credentials |
| `README.md` | Main docs | Onboarding |

---

## 💻 Useful Commands

```bash
# Check git status
git status

# View last commits
git log --oneline -5

# Make changes and push
git add .
git commit -m "feat: your description"
git push

# Activate environment
source venv/bin/activate

# Test Docker
make up    # Start Postgres + Redis
make down  # Stop

# Run tests
make test

# Check linting
make lint
```

---

## 🚨 Critical Path to MVP

**Week 1:**
- ✅ Setup ODDS_API_KEY
- ✅ Build player props features
- ✅ Train LightGBM models

**Week 2:**
- ✅ Build odds comparison engine
- ✅ Add blowout/rest risk detection
- ✅ Create betting dashboard
- ✅ Backtest on 2019-2020 season

**Results:**
- 53%+ win rate ✓
- +$2,400 backtest ROI ✓
- Ready to release v1.0 ✓

---

## 📞 If Something Goes Wrong

| Problem | Solution |
|---------|----------|
| `poetry install` fails | `poetry cache clear PyPI --all && poetry install` |
| Port 8000/3000 in use | `lsof -i :8000` then `kill -9 <PID>` |
| Docker won't start | `docker-compose down -v && docker-compose up` |
| Import errors | `source venv/bin/activate` then try again |
| Git push fails | `git pull origin main` first, resolve conflicts |

---

## 🎓 Remember the Expert's Advice

> "Your robot's job is to save me time finding bets and beat sportsbooks. If you can do that, it has value."

**Focus on:**
1. ✅ Time savings (user finds opportunities instantly)
2. ✅ Edge calculation (accurate vs sharp odds)
3. ✅ Performance tracking (prove 53%+ win rate works)
4. ✅ Alt lines (give user options with edge)

**Don't over-engineer:**
- ❌ Complex ensemble models (simple LightGBM works)
- ❌ Parlays (user doesn't want)
- ❌ Team-level predictions (user wants player props)

---

## 🎯 Next Action Right Now

**Task #8: Setup .env with ODDS_API_KEY**

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"
cp .env.example .env
nano .env

# Add ODDS_API_KEY from https://odds-api.com
# Save (Ctrl+X, Y, Enter)

# Test it works
make key-audit
```

---

**Updated:** October 26, 2025  
**Status:** Ready to build betting robot 🤖  
**Estimated time to MVP:** 2 weeks  
**Expected outcome:** 53%+ win rate, +$2,400+ annual ROI  

Let's go! 🚀
