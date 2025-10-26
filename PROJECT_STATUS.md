# NBA Intelligence Platform - Project Status & Consolidation Plan

**Date:** October 26, 2025  
**Hardware Target:** Apple Silicon Mac, 24 GB RAM  
**Status:** Consolidation Required → Move to Production

---

## 🎯 Project Overview

**Goal:** Build a production-quality, locally runnable Full-Stack NBA Intelligence Platform with:
1. **Pregame Predictions** - Player-aware features + decaying-K Elo prior
2. **Live Win Probability** - Possession-by-possession GRU updates
3. **Video Highlights** - Simple foul-candidate detection from clips
4. **Player Chemistry** - Graph Neural Network over lineup networks
5. **Social Signals** - Real social media data for pre-tip calibration & relationship edges

**Critical Requirement:** REAL DATA ONLY. No synthetic placeholders. Fail fast if API keys missing.

---

## 📁 Current State Analysis

### Folder Comparison

#### `/nba-intel/` (Original scaffold - BASIC)
- ✅ Basic structure created
- ✅ Stub implementations exist
- ⚠️ Minimal backend implementation
- ⚠️ Simple frontend (basic Next.js pages)
- ⚠️ Limited validation logic

**Strengths:**
- Clean, simple structure
- Good starting point

**Weaknesses:**
- Lacks comprehensive API implementation
- Missing detailed config management
- Minimal frontend pages
- Basic validator functions

#### `/nba-intel-platform/` (Enhanced - COMPREHENSIVE) ⭐ RECOMMENDED
- ✅ Comprehensive backend with full validators
- ✅ Detailed config management (Pydantic models)
- ✅ Complete API key audit system
- ✅ Rich frontend (schedule, chemistry, sentiment, live, postgame pages)
- ✅ Better component organization
- ✅ More detailed documentation

**Strengths:**
- Complete API key testing (`key_audit.py`)
- Pydantic-based configuration
- Full validator suite with detailed error messages
- Multiple frontend pages ready
- Better logging setup
- Comprehensive utilities

**Weaknesses:**
- None significant - this is the superior implementation

---

## ✅ What's Been Done

### Infrastructure & Setup
- [x] Repository scaffolds created (both folders)
- [x] Docker Compose with PostgreSQL + Redis
- [x] Makefile with targets (setup, up, down, seed, train-*, eval, serve, web)
- [x] pyproject.toml with dependencies
- [x] .env.example with placeholders
- [x] KEYS.md documentation
- [x] Pre-commit hooks configured

### Common Utilities (nba-intel-platform ⭐)
- [x] Config loader with Pydantic models
- [x] Logger setup
- [x] Validators with fail-fast logic
- [x] Key audit system with API connectivity tests
- [x] Hardware detection (MPS/CPU)

### Documentation
- [x] README.md with setup instructions
- [x] KEYS.md with all API requirements
- [x] MODEL_CARD.md framework
- [x] DATA_USE.md ethics guidelines
- [x] reproduce.md

### Frontend (nba-intel-platform ⭐)
- [x] Next.js app structure
- [x] Schedule page stub
- [x] Chemistry analysis page
- [x] Sentiment page
- [x] Live game page
- [x] Postgame page
- [x] Component library (ui components)
- [x] Tailwind configuration

### Backend Stubs
- [x] FastAPI main.py skeleton
- [x] Router structure (health, predictions, live, clips, social)
- [x] Data ingestion stubs (NBA Stats, BR, social APIs, ORS)
- [x] Preprocessing stubs (pregame features, sequences, graph, social, vision)
- [x] Model training stubs (Elo, LightGBM, GRU, Vision, GNN, Sentiment)

---

## ❌ What's NOT Done Yet

### Data Ingestion (Critical - Real Data Required)
- [ ] **nba_stats_client.py** - Complete implementation with real API calls
- [ ] **br_loader.py** - Polite scraper with rate limiting
- [ ] **social_x.py** - Twitter/X API v2 integration
- [ ] **social_reddit.py** - Reddit API client
- [ ] **social_youtube.py** - YouTube Data API client
- [ ] **travel_ors.py** - OpenRouteService distance/timezone calculations
- [ ] Data validators to confirm non-empty tables

### Feature Engineering
- [ ] **build_pregame_features.py** - Full implementation:
  - Minutes-weighted player stats (BPM/RAPM/PIE)
  - Rest/travel features (B2B, distance, timezone, elevation)
  - Decaying-K Elo calculations
  - Chemistry embeddings integration
  - Social sentiment features
- [ ] **build_live_sequences.py** - Possession-level feature extraction
- [ ] **build_lineup_graph.py** - Graph construction with time-decayed edges
- [ ] **build_social_aggregates.py** - NLP pipeline with DistilBERT
- [ ] **build_vision_index.py** - FFmpeg clip generation
- [ ] **join_social_to_graph.py** - Social edge weight computation

### Models (Core ML Work)
- [ ] **Elo model** - Full decaying-K implementation
- [ ] **LightGBM pregame** - Training with calibration
- [ ] **GRU live model** - Sequence training on MPS
- [ ] **Vision classifier** - MobileNetV3/EfficientNet-B0 training
- [ ] **Chemistry GNN** - GraphSAGE/GAT implementation
- [ ] **Sentiment/Stance** - DistilBERT fine-tuning
- [ ] **Model fusion** - Pregame prior × live likelihood
- [ ] **Postgame feedback loop** - Write-back to training data

### API Endpoints (Implementation)
- [ ] GET /predictions - Complete with SHAP explanations
- [ ] GET /game/{id}/live - WebSocket/polling for possession updates
- [ ] POST /game/{id}/clips/index - Video ingestion
- [ ] GET /game/{id}/clips - Timestamp retrieval
- [ ] GET /explain/{id} - Feature importance visualization
- [ ] GET /social/team - Team sentiment aggregates
- [ ] GET /social/duos - Player relationship features

### Frontend (Full Implementation)
- [ ] Schedule page - Connect to API, show probabilities
- [ ] Game Center - Live chart with WebSocket updates
- [ ] Postgame - Calibration curves, downloadable exports
- [ ] Chemistry viz - Graph visualization of lineups
- [ ] Sentiment dashboard - Social media insights

### Training & Evaluation
- [ ] Season-wise cross-validation (N-5..N-2 train, N-1 val, N test)
- [ ] Ablation studies (Elo, +chem, +social, +both)
- [ ] Calibration plots & reliability diagrams
- [ ] SHAP global/per-game explanations
- [ ] Notebooks with analysis

### Testing
- [ ] Unit tests for all feature builders
- [ ] Unit tests for models
- [ ] Integration test (end-to-end smoke test)
- [ ] Acceptance criteria validation

### Workers & Scheduling
- [ ] Celery/APScheduler nightly jobs
- [ ] Data refresh automation
- [ ] Model retraining on drift
- [ ] Clip reindexing jobs

---

## 🎯 Consolidation Plan

### Phase 1: Merge to Root (Week 1)
1. **Copy `nba-intel-platform/` → root** (it's superior)
2. **Delete both old folders** after verification
3. **Keep best implementations:**
   - ✅ All from `nba-intel-platform/` (backend, frontend, configs)
   - Check if any unique files from `nba-intel/` need merging

### Phase 2: Data & Features (Week 2-3)
1. Implement real data ingestion (NBA Stats, BR, social APIs)
2. Build complete feature pipelines
3. Add validators for non-empty tables
4. Test with small real data slice (2019 season sample)

### Phase 3: Models (Week 4-5)
1. Train Elo baseline
2. Train LightGBM with calibration
3. Train GRU live model
4. Train vision classifier
5. Train chemistry GNN
6. Implement fusion logic

### Phase 4: API & Frontend (Week 6)
1. Complete all API endpoints
2. Connect frontend to backend
3. Add WebSocket for live updates
4. Implement SHAP visualizations

### Phase 5: Evaluation & Testing (Week 7)
1. Run ablation studies
2. Generate calibration plots
3. Write evaluation notebooks
4. Complete unit & integration tests

### Phase 6: Polish & Deploy (Week 8)
1. Final documentation pass
2. Demo video creation
3. Performance optimization
4. Acceptance testing

---

## 📋 Immediate Action Items

### Priority 1 (This Week)
1. ✅ **Consolidate folders** - Move nba-intel-platform to root
2. ✅ **Update todo list** with detailed breakdowns
3. **Fill .env with real API keys** (see KEYS.md)
4. **Run `make key-audit`** to verify connectivity
5. **Implement nba_stats_client.py** with real data fetching

### Priority 2 (Next Week)
1. Complete feature builders
2. Train first models (Elo + LightGBM)
3. Connect one frontend page to API

---

## 🔑 Required API Keys Status

**Required:**
- [ ] `NBA_STATS_API_KEY` - NBA Stats API access
- [ ] `X_BEARER_TOKEN` - Twitter/X API v2
- [ ] `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` - Reddit API
- [ ] `YOUTUBE_API_KEY` - YouTube Data API
- [ ] `ORS_API_KEY` - OpenRouteService (travel distance)

**Optional:**
- [ ] `ODDS_API_KEY` - Market odds for calibration

**Status:** ⚠️ Need to obtain all keys before real data can flow

---

## 🎯 Success Metrics

### Acceptance Criteria
- [ ] `make seed` downloads real seasons, validators confirm non-empty
- [ ] `make train-pregame` completes in <60 minutes on 24GB Mac
- [ ] `GET /predictions?date=...` returns calibrated probabilities + SHAP
- [ ] Live endpoint streams possession updates
- [ ] Vision indexes ≥3 labeled highlights
- [ ] Chemistry GNN reduces ECE on validation season
- [ ] Social features run only with keys + ENABLE_SENTIMENT=true
- [ ] All frontend pages render without errors

### Performance Targets
- Pregame log-loss reduction vs Elo: >5% absolute improvement
- ECE (calibration error): <0.05
- Live model log-loss: competitive with FiveThirtyEight
- Vision classifier: >80% accuracy on highlight detection
- Training time: <60 minutes total on 24GB Mac

---

## 📊 Technical Debt & Improvements

### Known Issues
1. Mock data mode not fully wired (only used in tests)
2. SIMPLIFIED_MODE needs smaller real data slices
3. Social module needs more robust entity linking
4. Video processing memory optimization needed for long clips

### Future Enhancements
1. GPU acceleration for larger models (when available)
2. Real-time streaming for live games
3. Mobile app (React Native)
4. Public API deployment
5. Betting strategy backtesting module

---

## 📚 Resources & References

### Documentation
- `README.md` - Quick start guide
- `KEYS.md` - API key requirements
- `MODEL_CARD.md` - Model documentation
- `DATA_USE.md` - Ethics & compliance
- `reproduce.md` - Exact reproduction steps

### Research Papers Cited
- Network effects in NBA (SURFACE)
- ML for basketball outcomes (MDPI)
- GNN for sports prediction (PMC)
- Twitter sentiment analysis (ACM, Fenix Técnico Lisboa)

---

## 🚀 Next Steps

**This Week:**
1. Run consolidation (move nba-intel-platform to root)
2. Obtain API keys
3. Implement first data ingestion module
4. Train Elo baseline on small real data

**Next Week:**
1. Complete feature engineering
2. Train LightGBM model
3. Connect first frontend page
4. Write unit tests

**Goal:** Working pregame predictions on real data within 2 weeks.

---

**Last Updated:** October 26, 2025  
**Status:** Ready for consolidation → Implementation phase
