# Consolidation Guide - NBA Intelligence Platform

**Goal:** Merge the best implementations from both folders into a single, production-ready codebase at the root level.

---

## 📊 Comparison Matrix

| Component | nba-intel | nba-intel-platform | Winner |
|-----------|-----------|-------------------|--------|
| **Backend - Common Utilities** | Basic validators | Comprehensive validators, config, logger, key_audit | **platform** ✅ |
| **Backend - Data Ingestion** | Stub implementations | Stub implementations | **TIE** (neither complete) |
| **Backend - Models** | Stub implementations | Stub implementations | **TIE** (neither complete) |
| **Backend - API** | Basic FastAPI structure | Basic FastAPI structure | **TIE** |
| **Frontend - Structure** | Simple pages | Multiple detailed pages | **platform** ✅ |
| **Frontend - Components** | Basic | Complete UI component library | **platform** ✅ |
| **Config Files** | Basic | Detailed with Pydantic models | **platform** ✅ |
| **Documentation** | Good | Excellent (more detailed) | **platform** ✅ |
| **Docker/Infra** | Basic | Basic | **TIE** |

**Verdict:** `nba-intel-platform` is the clear winner. Use it as the base.

---

## 🎯 Step-by-Step Consolidation

### Step 1: Backup Current State
```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"

# Create backup
mkdir -p backups
cp -r nba-intel backups/nba-intel-$(date +%Y%m%d)
cp -r nba-intel-platform backups/nba-intel-platform-$(date +%Y%m%d)
```

### Step 2: Verify nba-intel-platform Completeness

**Files to check before consolidation:**

```bash
cd nba-intel-platform

# Check critical files exist
ls -la \
  src/common/config.py \
  src/common/validators.py \
  src/common/key_audit.py \
  src/common/logger.py \
  app/schedule/page.tsx \
  app/chemistry/page.tsx \
  app/sentiment/page.tsx \
  components/ui/*.tsx \
  KEYS.md \
  MODEL_CARD.md \
  DATA_USE.md
```

### Step 3: Copy Best Implementation to Root

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"

# Copy nba-intel-platform to a new root folder
cp -r nba-intel-platform nba-intelligence-platform

cd nba-intelligence-platform
```

### Step 4: Check for Unique Files in nba-intel

**Scan for files that might be unique/better in nba-intel:**

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"

# Compare key directories
diff -rq nba-intel/src nba-intel-platform/src | grep "Only in nba-intel"
diff -rq nba-intel/configs nba-intel-platform/configs | grep "Only in nba-intel"
diff -rq nba-intel/web nba-intel-platform/app | grep "Only in nba-intel"
```

**Files to manually check:**

1. `nba-intel/src/common/hardware.py` - Check if platform has this
2. `nba-intel/web/app/` - Compare Next.js structure differences
3. Any unique config files
4. Any unique utility functions

### Step 5: Merge Unique Good Parts (if any)

**If nba-intel has unique features worth keeping:**

Example - if hardware.py is better in nba-intel:
```bash
# Copy unique file to consolidated repo
cp nba-intel/src/common/hardware.py \
   nba-intelligence-platform/src/common/hardware.py
```

### Step 6: Update Configuration

**Edit `nba-intelligence-platform/.env.example`:**
```bash
# Ensure all required keys are listed with PUT_KEY_HERE placeholders
cat > nba-intelligence-platform/.env.example << 'EOF'
# Required for real-data mode
NBA_STATS_API_KEY=PUT_KEY_HERE
X_BEARER_TOKEN=PUT_KEY_HERE
REDDIT_CLIENT_ID=PUT_ID_HERE
REDDIT_CLIENT_SECRET=PUT_SECRET_HERE
YOUTUBE_API_KEY=PUT_KEY_HERE
ORS_API_KEY=PUT_KEY_HERE
ODDS_API_KEY=PUT_KEY_HERE

# App configs
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nba_intel
REDIS_URL=redis://localhost:6379/0
SIMPLIFIED_MODE=true
ALLOW_MOCK_DATA=false
REQUIRE_REAL_DATA=true
ENABLE_CHEMISTRY=true
ENABLE_SENTIMENT=false
LOG_LEVEL=INFO
EOF
```

### Step 7: Verify Makefile Targets

```bash
cd nba-intelligence-platform

# Check all targets exist
make -n setup
make -n up
make -n down
make -n key-audit
make -n seed
make -n data
make -n train-pregame
make -n eval
make -n serve
make -n web
```

### Step 8: Test Infrastructure

```bash
# Start services
make up

# Check containers are running
docker ps | grep -E "postgres|redis"

# Test key audit (will fail without real keys - that's expected)
make key-audit
```

### Step 9: Remove Old Folders (After Verification)

**⚠️ ONLY DO THIS AFTER CONFIRMING EVERYTHING WORKS**

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"

# Verify consolidated folder is complete
ls -la nba-intelligence-platform/src/
ls -la nba-intelligence-platform/app/
ls -la nba-intelligence-platform/configs/

# If all looks good, remove old folders
rm -rf nba-intel
rm -rf nba-intel-platform

# Backups still exist in backups/ folder
ls -la backups/
```

---

## 🔍 Manual Verification Checklist

### Backend Files
- [ ] `src/common/config.py` - Comprehensive Pydantic config
- [ ] `src/common/validators.py` - Real data validators with fail-fast
- [ ] `src/common/key_audit.py` - API connectivity tests
- [ ] `src/common/logger.py` - Proper logging setup
- [ ] `src/data/ingest/` - All API clients stubbed
- [ ] `src/data/preprocess/` - All feature builders stubbed
- [ ] `src/models/` - All model trainers stubbed
- [ ] `src/services/api/main.py` - FastAPI app with routers

### Frontend Files
- [ ] `app/schedule/page.tsx` - Schedule page
- [ ] `app/chemistry/page.tsx` - Chemistry analysis
- [ ] `app/sentiment/page.tsx` - Sentiment dashboard
- [ ] `app/live/page.tsx` - Live game tracker
- [ ] `app/postgame/page.tsx` - Post-game analysis
- [ ] `components/ui/` - Complete component library
- [ ] `components/game-card.tsx` - Game display component
- [ ] `components/nav-header.tsx` - Navigation

### Config & Infra
- [ ] `docker-compose.yml` - PostgreSQL + Redis
- [ ] `Makefile` - All targets present
- [ ] `pyproject.toml` - All dependencies listed
- [ ] `.env.example` - All keys with placeholders
- [ ] `configs/config.yaml` - Main config
- [ ] `configs/params_*.yaml` - Model hyperparameters

### Documentation
- [ ] `README.md` - Complete setup instructions
- [ ] `KEYS.md` - Detailed API key requirements
- [ ] `MODEL_CARD.md` - Model documentation
- [ ] `DATA_USE.md` - Ethics & compliance
- [ ] `reproduce.md` - Reproduction steps

---

## 🚨 Common Issues & Solutions

### Issue 1: Missing Dependencies
```bash
# If Python deps missing
cd nba-intelligence-platform
poetry install
# OR
pip install -e .

# If Node deps missing
cd nba-intelligence-platform
npm install
```

### Issue 2: Docker Containers Won't Start
```bash
# Clean up old containers
docker-compose down -v
docker system prune -f

# Restart
make up
```

### Issue 3: Port Conflicts
```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # FastAPI
lsof -i :3000  # Next.js

# Kill processes if needed
kill -9 <PID>
```

### Issue 4: Environment Variables Not Loading
```bash
# Verify .env exists and has content
cat .env | grep -v "^#" | grep -v "^$"

# Source it manually if needed
export $(cat .env | grep -v "^#" | xargs)
```

---

## 📝 Post-Consolidation Tasks

### 1. Initialize Git (if not already)
```bash
cd nba-intelligence-platform

# If not a git repo yet
git init
git add .
git commit -m "Initial consolidated codebase from nba-intel-platform"

# Add remote if you have one
git remote add origin <your-repo-url>
```

### 2. Set Up API Keys
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and fill in real keys
nano .env  # or your preferred editor
```

### 3. Run First Tests
```bash
# Key audit (will show which keys are missing)
make key-audit

# Try to start services
make up

# Check if services are healthy
docker-compose ps
```

### 4. Document What's Missing
```bash
# Create a NEXT_STEPS.md
cat > NEXT_STEPS.md << 'EOF'
# Next Implementation Steps

## Immediate (This Week)
1. [ ] Obtain all API keys (see KEYS.md)
2. [ ] Implement nba_stats_client.py with real data fetching
3. [ ] Test data ingestion with small sample
4. [ ] Implement Elo baseline model

## Next Week
1. [ ] Complete pregame feature engineering
2. [ ] Train LightGBM model
3. [ ] Connect schedule page to API
4. [ ] Write first unit tests

## Following Week
1. [ ] Implement live win probability model
2. [ ] Build chemistry GNN
3. [ ] Complete frontend integration
4. [ ] Run ablation studies
EOF
```

---

## ✅ Final Verification

**Before deleting old folders, confirm:**

```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction/nba-intelligence-platform"

# 1. All critical files exist
test -f src/common/config.py && echo "✅ Config exists"
test -f src/common/validators.py && echo "✅ Validators exist"
test -f app/schedule/page.tsx && echo "✅ Frontend exists"
test -f docker-compose.yml && echo "✅ Docker config exists"
test -f Makefile && echo "✅ Makefile exists"

# 2. Dependencies are installable
poetry install --dry-run && echo "✅ Python deps OK"
npm install --dry-run && echo "✅ Node deps OK"

# 3. Services can start
make up && echo "✅ Docker services OK"

# 4. Makefile targets work
make -n seed && echo "✅ Makefile targets OK"
```

**If all checks pass → Safe to delete old folders**

---

## 🎯 Consolidation Completion Criteria

- [ ] nba-intelligence-platform folder exists with complete codebase
- [ ] All best implementations from both folders are included
- [ ] No unique good code was lost in the merge
- [ ] Docker services start successfully
- [ ] Makefile targets are all present and syntactically correct
- [ ] .env.example has all required keys
- [ ] KEYS.md documents all APIs
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Python package installs without errors
- [ ] Git repo is initialized with initial commit
- [ ] Backups of old folders exist in backups/
- [ ] Old folders (nba-intel, nba-intel-platform) are removed

---

## 📞 Support & Next Steps

**After consolidation:**
1. See `PROJECT_STATUS.md` for full project overview
2. See `NEXT_STEPS.md` for implementation roadmap
3. See `KEYS.md` for API key requirements
4. See `README.md` for setup instructions

**If you encounter issues:**
1. Check Docker logs: `docker-compose logs`
2. Check Python import errors: `python -c "import src.common.config"`
3. Restore from backup if needed: `cp -r backups/nba-intel-platform-YYYYMMDD nba-intelligence-platform`

---

**Ready to consolidate?** Start with Step 1 (Backup) and work through systematically.
