# 🎯 NBA Player Props Betting Strategy

**Source:** Reddit discussion analysis (10-month conversation with experienced bettor "7FOOT7")  
**Focus:** Player props (PTS, AST, REB, STEALS, BLOCKS, combos) - NOT parlays or lottery tickets  
**Goal:** Achieve 53%+ win rate on straight bets (1 leg) or alt lines (3 legs max)  

---

## 🔑 Key Insights from Expert Bettor

### The Core Problem You're Solving
**Old approach (❌ Lottery warrior):** Long parlays, hoping for all legs to hit  
**New approach (✅ Sharp edge):** Straight bets with 53%+ win rate + alt line adjustments

> "I'm tired of being a lotto warrior and want to transition to straights or at the worst 3 legs maximum (alt lines)"

### The Robot's Value Proposition
Your model's job is to:
1. **Save time** - Find best opportunities daily WITHOUT manual analysis
2. **Outperform sportsbooks** - Beat average odds by comparing to sharp books
3. **Identify edges** - Find where model prediction > market line
4. **Track ROI** - Log performance to verify 53%+ win rate is real

> "Your robot is a good idea and has value" - because it automates the expertise

---

## 💰 Betting Framework

### Market Reality
- **Sportsbook odds** (FanDuel, DraftKings): Set by average bettor, wider margins
- **Sharp book odds** (Vegas, Pinnacle): Set by professionals, tighter margins
- **Your edge:** Model prediction vs sharp book odds, not vs sportsbook

**Example:**
```
Your model:  Brown 25+ = 55% probability
Sportsbook:  Brown 23.5 = 50.5% implied prob
Sharp book:  Brown 23.5 = 52% implied prob

Edge only exists if comparing to sharp odds:
- vs sportsbook: 55% - 50.5% = +4.5% edge ✓
- vs sharp book: 55% - 52% = +3% edge (real edge)
```

### Bet Types to Focus On
**✅ Straight props:** PTS, AST, REB, STEALS, BLOCKS individually  
**✅ Combos:** e.g., 20+ PTS + 5+ AST (natural correlation)  
**✅ Alt lines:** Same prop, adjusted odds (e.g., 27+ PTS instead of 23.5)  
**❌ Parlays:** Too risky, lower expected value  

### Win Rate Target
**53% minimum** to be profitable (accounting for -110 juice):
- Break even: 52.4% (to overcome sportsbook margin)
- Profitable: 53%+ (net positive EV)

---

## 📊 The Expert's Thought Process (Your Model Should Codify This)

### Case Study: Jaylen Brown vs CHI (Next 2 Games)

**The Expert's Analysis:**
```
Context: BOS blowout expected vs CHI
Question: Will Brown get to 25+ before resting?

Data:
- Played 21/26 games (normal availability)
- 11x scored 25+ (50% of games)
- Last 2 games: 11, 14 (downtrend? or just variance?)
- Prediction: "Yes, Brown 25+ because..."
  - 50% historical rate
  - CHI weak defense
  - But blowout risk = rest risk
  - Gut says "ok" but need better confidence

Decision: Wait for lineup confirmation, reassess day-of
```

**What Your Model Should Do:**
1. **Track recent form** - Not just average, but trend (11, 14 recent = watch)
2. **Opponent matchup** - CHI defense difficulty vs Brown's profile
3. **Blowout risk** - If BOS -12 favorites, Brown rest risk when up 20
4. **Game flow** - Close game = play all 4 quarters; blowout = bench by Q4
5. **Adjust confidence** - Start with historical 50%, adjust for matchup + context

### The Blowout Problem
> "If it's a blowout, does he get to 24 before he gets rested?"

**This is domain expertise your model must capture:**
- If expected win probability (team level) > 75% AND line < 20 pts → high rest risk in Q4
- Adjust player props down: if normal 25+ is 50%, with rest risk maybe 45%
- Show to user: "Model: 25+ = 50%, but 30% rest risk in Q4 = net 35% confidence"

---

## 🏗️ System Architecture for Betting

### Phase 1: Core Predictions (Tasks #8-15)
```
Input Data:
├── Player stats (PTS, AST, REB, STEALS, BLOCKS)
├── Recent form (last 10 games trend)
├── Opponent matchup (def ranking vs player specialty)
├── Rest/fatigue (back-to-back, travel, minutes load)
├── Game context (expected pace, blowout prob)
└── Historical props (Brown 25+ 50%, 30+, etc)

↓ Feature Engineering

Player Props Features:
├── Season average per stat
├── 3/5/10-game rolling average
├── vs opponent difficulty
├── Rest days, travel fatigue
├── Game blowout probability
└── Recent trend (up/down/flat)

↓ LightGBM Model

Predictions:
├── PTS: 22.5 (confidence 55%)
├── AST: 5.5 (confidence 60%)
├── REB: 7.5 (confidence 52%)
├── STEALS: 1.5 (confidence 45%)
└── BLOCKS: 0.5 (confidence 40%)
    + Rest risk flags
```

### Phase 2: Odds Comparison (Tasks #16, #25)
```
Your predictions vs Market lines:
├── Fetch FanDuel/DraftKings current lines (ODDS_API)
├── Parse implied probabilities
├── Calculate edge: (model prob - market prob)
├── Flag +EV opportunities
└── Suggest alt lines for better value

Example Output:
Brown 25+ PTS
├── Model prediction: 55% (high confidence)
├── FanDuel line: 23.5 (50.5% implied)
├── Sharp line: 23.5 (52% implied)
├── Edge: +3% (vs sharp)
├── Recommendation: OVER 23.5 ✓
├── Alt line available: 27+ at -110 (48% implied) - Edge +7% ✓✓
└── Suggested bet: 27+ (better value)
```

### Phase 3: Betting & Tracking (Tasks #18, #30)
```
Daily workflow:
1. 11:00 PM: Generate next day predictions
2. Compare to live odds, flag opportunities
3. User reviews recommendations
4. User places bets on platform (manual or webhook)
5. Post-game: Log actual outcomes
6. Dashboard updates: ROI, win rate, P&L

Performance dashboard:
├── Total bets: 200
├── Win rate: 53.4%
├── Profit: +$2,400 (on $100 unit bets)
├── By stat: PTS 54% | AST 51% | REB 55%
├── By odds tier: Close lines 52% | Big gaps 56%
└── Monthly P&L curve
```

---

## 🎮 User Journey (Your Robot's Daily Workflow)

### Before Lineup Lock (T-15 minutes)
```
1. App opens dashboard
2. See: "Top 5 betting opportunities for today"
   ├── Jaylen Brown 25+ PTS (55% confidence, +3% edge vs sharp)
   ├── Luka Doncic 8+ AST (58% confidence, +4% edge)
   ├── Nikola Jokic 12+ REB (52% confidence, +1.5% edge)
   ├── Stephen Curry 3+ 3PM (60% confidence, +5% edge)
   └── Shai 5+ AST (51% confidence, +0.5% edge - skip, close call)

3. User clicks "Why 25+?" for Brown
   → SHAP explanation: "Recently 50% of games, CHI weak, but blowout risk"
   → See: Historical Brown data, opponent analysis, blowout probability

4. User decides: "I trust 25+ and 8+ AST, skip others"

5. Takes both bets on FanDuel before lock

6. App logs: Brown 25+, Luka 8+, confidence 55%/58%
```

### Post-Game (T+1 day)
```
1. App automatically logs outcomes:
   Brown: 26 PTS ✓ (won)
   Luka: 7 AST ✗ (lost)
   
2. Updates portfolio: +1-1 = net $0, but still +$500 week

3. Monthly report: "53.4% win rate through October"
```

---

## 🎯 Alt Line Strategy (Expert's Preference)

> "I'm content right now with needed to poke in one or two more corners to get a read"

This is about **alt lines** - same player/stat, different thresholds:

**Example: Brown PTS**
```
Standard line:        23.5 @ -110  (50.5% implied)
Alt lines:
  └─ 19.5 @ +110     (47.6% implied)  ← Easier hit, lower payout
  └─ 21.5 @ -105     (51.2% implied)
  └─ 23.5 @ -110     (50.5% implied)  ← This one
  └─ 25.5 @ -110     (47.6% implied)  ← Harder hit, better payout
  └─ 27.5 @ +120     (45.5% implied)  ← Very hard, very high payout
```

**Your Model's Job:**
- Predict Brown 25+ at 55% probability
- Show user: "Standard 23.5 has +3% edge, but 25.5 has +7% edge"
- User picks 25.5 for better payoff/confidence trade
- Or model suggests: "If you like 19.5 better (easier win), take that instead"

---

## 🚨 Critical Metrics for MVP (v1.0)

### Must Have for Release
1. **Prediction accuracy** - Calibration curve shows model well-calibrated
2. **Edge calculation** - Correct edge vs sharp book odds
3. **Win rate tracking** - Prove 53%+ with real bets
4. **ROI positive** - Show +$ profit over season
5. **User recommends <5 bets/day** - Quality over quantity (saves time)

### Success Criteria
- Backtest on 2019-2020 season: 53%+ win rate
- Real-world test on next 2 weeks: 52%+ win rate (accounts for variance)
- User says: "This robot saves me 30 min/day finding bets and I trust it"

---

## 📋 Implementation Priority (Reordered for Betting)

### MVP Core (Do First)
1. ✅ **Setup API keys** - Especially ODDS_API (FanDuel/DraftKings)
2. ✅ **Player props features** - Recent form, matchup, rest, blowout context
3. ✅ **LightGBM per-stat** - Separate models for PTS, AST, REB, etc.
4. ✅ **Odds comparison engine** - Fetch live lines, calculate edge
5. ✅ **Betting dashboard** - Show today's opportunities, past ROI
6. ✅ **Performance tracking** - Log bets, update P&L daily

### Nice-to-Have (Do Later)
- Social media sentiment for injury signals
- Video analysis for recent form
- Celery workers for auto-recommendations
- Email alerts

### Not Needed
- Team-level chemistry GNN (low impact for props)
- Complex ensemble models (simple LightGBM works)
- Multi-leg parlay logic (skip by design)

---

## 🔧 Code Examples

### Blowout Risk Detection
```python
def calculate_rest_risk(team_win_prob: float, point_spread: float) -> float:
    """
    Estimate player rest risk in Q4 based on blowout probability.
    
    Args:
        team_win_prob: Model's team win probability (0-1)
        point_spread: Expected point spread from oddsmakers
    
    Returns:
        rest_risk (0-1): Probability player sits in Q4
    """
    # If high confidence blowout, high rest risk
    if team_win_prob > 0.75 and abs(point_spread) > 12:
        return 0.35  # 35% chance benched by Q4
    elif team_win_prob > 0.65 and abs(point_spread) > 10:
        return 0.20
    else:
        return 0.05  # Close game, unlikely rest

def adjust_props_confidence(base_confidence: float, rest_risk: float) -> float:
    """Apply rest risk penalty to player prop confidence."""
    return base_confidence * (1 - rest_risk)

# Example: Brown 25+ normally 55%, but 35% rest risk in blowout
confidence = adjust_props_confidence(0.55, 0.35)
# Returns: 0.55 * 0.65 = 0.36 (adjust down significantly)
```

### Edge Calculation
```python
def calculate_edge(
    model_probability: float,
    market_line: float,
    odds: float = -110
) -> float:
    """
    Calculate edge in player prop bet.
    
    Args:
        model_probability: Your model's prediction (0-1)
        market_line: Over/Under threshold (e.g., 23.5)
        odds: American odds (-110, +110, etc.)
    
    Returns:
        edge_percentage: Edge as % (positive = good bet)
    """
    # Convert odds to implied probability
    if odds < 0:
        market_prob = abs(odds) / (abs(odds) + 100)
    else:
        market_prob = 100 / (odds + 100)
    
    # Edge = model prob - market prob
    edge = model_probability - market_prob
    return edge * 100  # Return as percentage

# Example: Brown 25+ (55% model vs 50.5% market) = +4.5% edge
edge = calculate_edge(0.55, 25.5, -110)
# Returns: 4.5
```

---

## 📈 Backtest Results Template (For Release)

```
NBA Player Props Model - 2019-2020 Season Backtest

Straight Props (1 leg, -110 odds):
├── Total bets: 1,647
├── Wins: 876
├── Losses: 771
├── Win rate: 53.2% ✓
├── ROI: +$1,205 (on $100 unit bets) ✓
└── By stat:
    ├── PTS: 54.1% win rate, +$620 ROI
    ├── AST: 52.8% win rate, +$380 ROI
    ├── REB: 52.5% win rate, +$205 ROI
    ├── STEALS: 51.2% win rate, -$80 ROI
    └── BLOCKS: 49.8% win rate, -$120 ROI

Combo Props (2+ stats, -110 odds):
├── Total bets: 324
├── Wins: 168
├── Losses: 156
├── Win rate: 51.9%
└── ROI: +$45

RECOMMENDATION: Deploy with focus on PTS/AST combos
```

---

## 🎓 Key Learnings from Expert

1. **Domain matters** - "You need to find a way to code that expertise"
   - Blowout detection isn't just about win probability
   - Player sitting patterns, matchups, fatigue all matter

2. **Sharp books are baseline** - Compare vs Pinnacle/Vegas, not FanDuel
   - Your edge only exists vs professional odds

3. **Consistency beats parlays** - 53% on straights > hoping for 3/3 parlay legs
   - One good edge per day beats lottery thinking

4. **Alt lines are your leverage** - Same stat, better odds = better ROI
   - Show user multiple odds tiers with edge

5. **Save time is the value** - Model lets user find best opportunities instantly
   - Without robot = manual analysis 2-3 hours/day
   - With robot = 10 minutes to review + click

---

## 🚀 Next Immediate Task

**Task #8 (Updated):** Setup API Keys
- Focus on **ODDS_API_KEY** for FanDuel/DraftKings
- Get sharp book odds comparison (Pinnacle if available)
- Test with: `curl "https://api.odds-api.com/v4/sports/basketball_nba/odds?..."`

Then **Task #10:** Implement player props feature engineering (not team-level)

---

**Updated:** October 26, 2025  
**Strategy Focus:** Player Props Straight Bets → 53%+ Win Rate → Positive ROI  
**Your Robot's Job:** Save time, beat sportsbooks, track performance  

Next: Fill .env with ODDS_API_KEY and test connectivity! 🔑
