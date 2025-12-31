# Top-Tier NBA Prediction Platform - Complete Implementation Plan

## Executive Summary

**Goal:** Transform NBA prediction platform into a top-tier system with 70%+ accuracy and premium frontend
**Timeline:** 12 weeks (3 months) comprehensive implementation
**Data Sources:** Open-source (nba_api package - FREE, no API key needed)
**Approach:** Both model accuracy AND frontend polish equally prioritized

---

## Current State

**Model Performance:**
- Accuracy: 63.83% (calibrated)
- ROC-AUC: 0.6701
- Data: 5,291 games × 30 features
- Beats Vegas: +9.83%

**Frontend:**
- Basic dark theme
- 3 main pages (Predictions, Live, Schedule)
- Limited visualizations
- Basic error handling

**Gaps:**
- Model accuracy below 70% target
- Limited feature engineering (30 features)
- No injury/availability data
- Basic frontend UX
- No historical accuracy tracking
- Limited real-time features

---

## Phase 1: Model Accuracy Improvements (Target: 63% → 70%+)

### Task 1.1: Advanced Feature Engineering
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `src/data/preprocess/build_advanced_features.py` (new)
- `src/data/preprocess/build_temporal_features.py` (new)
- `src/data/preprocess/build_pregame_features.py` (modify)

**New Features to Add (15+):**
1. Player injury/availability (last 5 games) - from nba_api
2. Opponent-adjusted team metrics (OAPOW-style)
3. Home/away splits by month/season
4. Recent form with exponential decay (recent games weighted more)
5. Head-to-head matchup history (last 10 meetings)
6. Rest differential (home_rest_days - away_rest_days)
7. Back-to-back impact by team (team-specific B2B performance)
8. Playoff indicator (different patterns in playoffs)
9. Streak indicators (current win/loss streak)
10. Team strength rankings (Elo tier-based: top 10, middle 10, bottom 10)
11. Player minutes-weighted team stats
12. Clutch performance metrics (last 5 minutes of close games)
13. Fatigue indicators (games in last 7 days)
14. Pace-adjusted metrics
15. Offensive/defensive rating differentials

**Temporal Features:**
1. Recency weighting (exponential decay: `weight = exp(-days_ago / 30)`)
2. Seasonal adjustments (early season vs late season patterns)
3. Month-based win percentages
4. Day-of-week effects (teams perform differently on different days)
5. Time-of-season indicators (games 1-20 vs 41-60 vs 61-82)
6. Momentum indicators (last 3/5/10 games performance)

**Data Source:** nba_api package (FREE, no key needed)
- Use `nba_api.stats.endpoints` for game data
- Use `nba_api.stats.endpoints.scoreboard` for injury/availability
- Use `nba_api.stats.endpoints.playergamelogs` for player stats

**Expected Impact:** +1-2% accuracy

---

### Task 1.2: Ensemble Model Implementation
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `src/models/pregame/train_ensemble.py` (new)
- `src/models/pregame/ensemble_predictor.py` (new)

**Implementation:**
1. Train three models separately:
   - XGBoost (current best: 63.83%)
   - LightGBM (often beats XGBoost on tabular data)
   - CatBoost (handles categoricals better)
2. Use time-series cross-validation (not random split)
3. Calculate weights based on CV accuracy
4. Weighted voting: `prediction = w1*xgb + w2*lgb + w3*catboost`
5. Return ensemble prediction with confidence intervals

**Expected Impact:** +1-2% accuracy

---

### Task 1.3: Hyperparameter Optimization
**Priority:** MEDIUM
**Estimated Time:** 3-4 days
**Files:**
- `src/models/pregame/optimize_hyperparameters.py` (new)

**Implementation:**
1. Use Optuna for automated hyperparameter tuning
2. Optimize for each model (XGBoost, LightGBM, CatBoost):
   - learning_rate
   - max_depth
   - lambda (L2 regularization)
   - gamma (minimum split loss)
   - subsample
   - colsample_bytree
3. Use time-series cross-validation (not random split)
4. Early stopping to prevent overfitting
5. Save best hyperparameters

**Expected Impact:** +0.5-1% accuracy

---

### Task 1.4: Advanced Calibration
**Priority:** MEDIUM
**Estimated Time:** 2-3 days
**Files:**
- `src/models/pregame/calibrate.py` (modify)

**Implementation:**
1. Upgrade from Sigmoid to Platt + Isotonic Regression
2. Use `sklearn.calibration.CalibratedClassifierCV`
3. Calibrate each model separately
4. Calibrate ensemble prediction
5. Add confidence intervals (prediction intervals)
6. Create calibration curves visualization

**Expected Impact:** +0.25-0.5% accuracy

---

### Task 1.5: Data Collection Enhancements
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `src/data/ingest/injury_fetcher.py` (new)
- `src/data/ingest/lineup_fetcher.py` (new)
- `src/data/ingest/referee_fetcher.py` (new)

**Implementation:**
1. **Injury Fetcher:**
   - Use nba_api to fetch injury reports
   - Parse player availability status
   - Store in database/cache
   - Impact on predictions (adjust probabilities)

2. **Lineup Fetcher:**
   - Use nba_api to fetch starting lineups
   - Store lineup data
   - Use in feature engineering

3. **Referee Fetcher:**
   - Use nba_api to fetch referee assignments
   - Analyze referee bias (home/away calls)
   - Use in feature engineering

**Data Source:** nba_api package (FREE)
- `nba_api.stats.endpoints.scoreboard` for injury reports
- `nba_api.stats.endpoints.commonteamroster` for lineups
- `nba_api.stats.endpoints.boxscore` for referee data

**Expected Impact:** +0.5-1% accuracy

---

## Phase 2: Frontend Enhancements

### Task 2.1: Predictions Page Redesign
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `app/predictions/page.tsx` (major redesign)
- `components/prediction-card.tsx` (new)
- `components/confidence-meter.tsx` (new)
- `components/feature-importance.tsx` (new)

**New Components:**
1. **Prediction Card:**
   - Large confidence meters with color gradients (green/yellow/red)
   - Win probability visualization (circular progress)
   - Team logos and colors
   - Vegas line comparison
   - Expected outcome text ("Lakers 67% likely to win by 4.2 points")

2. **Confidence Meter:**
   - Visual confidence indicator (0-100%)
   - Color-coded (green: high, yellow: medium, red: low)
   - Animated transitions

3. **Feature Importance:**
   - Top 5 feature importance visualization (bar charts)
   - Interactive tooltips
   - SHAP values display

**Design Elements:**
- Premium dark theme (slate-900 base)
- Gradient accents (cyan, orange, blue, red)
- Glowing shadows on hover
- Smooth animations (framer-motion)
- Responsive design (mobile-first)
- Loading states (skeletons)
- Error handling (error boundaries)

---

### Task 2.2: Live Game Dashboard Enhancement
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `app/live/page.tsx` (major enhancement)
- `components/win-probability-chart.tsx` (new)
- `components/live-scoreboard.tsx` (enhance)

**New Features:**
1. Interactive win probability curve (updates every possession)
2. Key momentum changes (highlighted on chart)
3. Play-by-play milestone alerts
4. Timeout/substitution tracking
5. Score differential impact on probability
6. Quarter-by-quarter probability shifts
7. Key player performance indicators
8. Win probability history (entire game)

**Visualizations:**
- Interactive win probability curve (recharts)
- Score timeline
- Key moments markers
- Team performance metrics

---

### Task 2.3: Advanced Analytics Page
**Priority:** MEDIUM
**Estimated Time:** 1 week
**Files:**
- `app/analytics/page.tsx` (major enhancement)
- `components/accuracy-chart.tsx` (new)
- `components/calibration-curve.tsx` (new)

**New Features:**
1. Model performance dashboard
2. Historical accuracy by team
3. Historical accuracy by confidence level
4. Best/worst prediction categories
5. ROI tracking (if betting)
6. Feature importance over time
7. Calibration curves
8. Prediction distribution charts

---

### Task 2.4: Schedule Page Enhancements
**Priority:** MEDIUM
**Estimated Time:** 3-4 days
**Files:**
- `app/schedule/page.tsx` (enhance)
- `components/injury-indicator.tsx` (new)
- `components/matchup-analysis.tsx` (new)

**New Features:**
1. Player availability indicators
2. Injury report integration
3. Matchup analysis (H2H history)
4. Prediction confidence badges
5. Vegas line comparison
6. Expected score predictions
7. Key factors preview
8. Filter by team, date range, confidence

---

### Task 2.5: Player Props Page Enhancement
**Priority:** MEDIUM
**Estimated Time:** 1 week
**Files:**
- `app/betting/page.tsx` (major enhancement)
- `components/bet-recommendation-card.tsx` (new)
- `components/kelly-calculator.tsx` (new)

**New Features:**
1. Real-time player prop predictions
2. Kelly Criterion bet sizing calculator
3. Edge detection (our probability vs market)
4. Confidence levels (High/Medium/Low)
5. Historical player performance vs opponent
6. Rest risk indicators
7. Player availability status
8. Betting recommendations with expected value

---

## Phase 3: Advanced Features

### Task 3.1: Historical Accuracy Tracking
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `src/services/accuracy_tracker.py` (new)
- `src/services/database.py` (new)
- `app/api/accuracy/route.ts` (new)

**Implementation:**
1. Track all predictions vs actual outcomes
2. Calculate accuracy by team, confidence level, date range
3. Store in database (SQLite or PostgreSQL)
4. API endpoint: `/api/accuracy?team=GSW&start_date=2024-01-01`
5. Frontend visualization of accuracy over time

---

### Task 3.2: SHAP Explanations
**Priority:** MEDIUM
**Estimated Time:** 1 week
**Files:**
- `src/models/pregame/explain.py` (new)
- `app/api/explain/route.ts` (new)
- `components/shap-visualization.tsx` (new)

**Implementation:**
1. Calculate SHAP values for each prediction
2. Generate feature importance visualization
3. Create explanation text ("Lakers favored because of home court advantage (+3.2%), recent form (+2.1%), rest advantage (+1.5%)")
4. API endpoint: `/api/explain?game_id=xxx`
5. Frontend visualization of SHAP values

---

### Task 3.3: Real-Time Updates
**Priority:** MEDIUM
**Estimated Time:** 1 week
**Files:**
- `src/services/websocket.py` (new)
- `app/api/ws/route.ts` (new)

**Implementation:**
1. WebSocket support for live game updates
2. Polling fallback (every 30 seconds)
3. Real-time probability updates
4. Score updates
5. Key moment alerts

---

## Phase 4: Infrastructure & Testing

### Task 4.1: Testing
**Priority:** HIGH
**Estimated Time:** 1 week
**Files:**
- `tests/unit/test_ensemble.py` (new)
- `tests/unit/test_features.py` (new)
- `tests/integration/test_api.py` (new)
- `tests/e2e/test_predictions.py` (new)

**Test Coverage:**
1. Unit tests for all models (target: 90%+ coverage)
2. Integration tests for API endpoints
3. Frontend component tests
4. End-to-end tests for critical flows
5. Model accuracy validation tests
6. Data pipeline tests

---

### Task 4.2: Monitoring & Logging
**Priority:** MEDIUM
**Estimated Time:** 3-4 days
**Files:**
- `src/services/monitoring.py` (new)
- `src/common/logger.py` (enhance)

**Features:**
1. Model performance monitoring
2. API response time monitoring
3. Error tracking and alerting
4. Prediction accuracy tracking
5. Data quality monitoring
6. Structured logging (JSON format)

---

## Phase 5: Deployment & Production

### Task 5.1: Deployment Setup
**Priority:** MEDIUM
**Estimated Time:** 1 week
**Files:**
- `Dockerfile` (enhance)
- `docker-compose.yml` (enhance)
- `.github/workflows/ci.yml` (new)

**Features:**
1. Docker containerization
2. CI/CD pipeline (GitHub Actions)
3. Environment variable management
4. Health checks
5. Error handling and recovery
6. Rate limiting
7. SSL/TLS certificates
8. Backup and recovery
9. Scaling strategy

---

## Open-Source Data Sources

### Primary Data Source: nba_api Package (FREE)
**No API key required!**
- Package: `nba-api` (already in pyproject.toml)
- Documentation: https://github.com/swar/nba_api
- Features:
  - Game data (scores, schedules)
  - Player statistics
  - Team statistics
  - Play-by-play data
  - Injury reports (via scoreboard)
  - Lineup data
  - Referee assignments

### Secondary Data Sources (Optional)
1. **Basketball-Reference** (FREE, scraping)
   - No API key needed
   - Rate limit: 3 seconds between requests
   - Use for historical data

2. **The Odds API** (FREE tier available)
   - For betting odds
   - Free tier: 500 requests/month
   - Already integrated

---

## Dependencies to Add

### Python Packages
```toml
# Already in pyproject.toml
optuna = "^3.4.0"  # Hyperparameter optimization
shap = "^0.49.0"   # Model explanations
catboost = "^1.2.8"  # Ensemble model
nba-api = "1.5.2"  # NBA data (FREE)

# Need to add
plotly = "^5.18.0"  # Interactive visualizations
websockets = "^12.0"  # Real-time updates
```

### Node Packages
```json
{
  "dependencies": {
    "recharts": "^2.10.0",  // Charts
    "framer-motion": "^10.16.0",  // Animations
    "@tanstack/react-query": "^5.0.0",  // Data fetching
    "zustand": "^4.4.0",  // State management
    "date-fns": "^2.30.0"  // Date utilities
  }
}
```

---

## Execution Order

### Week 1-2: Model Foundation
1. Advanced feature engineering
2. Ensemble model implementation
3. Data collection enhancements

### Week 3-4: Model Optimization
1. Hyperparameter optimization
2. Advanced calibration
3. Historical accuracy tracking

### Week 5-6: Frontend Foundation
1. Predictions page redesign
2. Live game dashboard enhancement
3. Schedule page enhancements

### Week 7-8: Frontend Advanced
1. Analytics page
2. Player props page
3. SHAP explanations

### Week 9-10: Advanced Features
1. Real-time updates
2. WebSocket implementation
3. Advanced matchup analysis

### Week 11-12: Infrastructure
1. Testing
2. Monitoring
3. Deployment

---

## Success Metrics

### Model Performance
- Accuracy: 63.83% → 70%+ (target)
- ROC-AUC: 0.6701 → 0.72+ (target)
- Precision: 64% → 68%+ (target)
- Recall: 78% → 80%+ (target)

### Frontend
- Page load time: < 2 seconds
- API response time: < 500ms
- Mobile responsiveness: 100%
- Error rate: < 1%
- User engagement: Time on page > 2 minutes

### Features
- Historical accuracy: Tracked for all predictions
- Injury reports: 100% coverage
- Real-time updates: < 30 second latency
- SHAP explanations: Available for all predictions

---

## Risk Mitigation

### Model Overfitting
- Use time-series cross-validation
- Early stopping
- Regularization
- Ensemble methods

### Data Quality Issues
- Data validation
- Missing data handling
- Outlier detection
- Data quality monitoring

### Frontend Performance
- Code splitting
- Lazy loading
- Caching
- CDN for static assets
q
### API Performance
- Caching (Redis)
- Database optimization
- Rate limiting
- Load balancing

---

## Next Steps

1. **Review and approve this plan**
2. **Set up project tracking** (GitHub Projects)
3. **Create feature branches** for each phase
4. **Start with Phase 1** (Model Improvements)
5. **Iterate based on results**
6. **Deploy incrementally**

---

## Files Summary

### New Files to Create (30+ files)
- Model: 5 files
- Features: 3 files
- Frontend: 10+ files
- Services: 5 files
- Tests: 10+ files
- Infrastructure: 5+ files

### Files to Modify (15+ files)
- Model: 3 files
- Features: 2 files
- Frontend: 8 files
- Services: 2 files
- Infrastructure: 2 files

**Total: 45+ files to create/modify**

---

## Timeline Estimate

**Total: 12 weeks (3 months) for complete implementation**

- Phase 1 (Model): 4 weeks
- Phase 2 (Frontend): 4 weeks
- Phase 3 (Advanced Features): 2 weeks
- Phase 4 (Infrastructure): 1 week
- Phase 5 (Deployment): 1 week

---

This plan provides a comprehensive roadmap to transform your NBA prediction platform into a top-tier system with 70%+ accuracy and a premium frontend, using only open-source data sources (nba_api package - FREE, no API key needed).

