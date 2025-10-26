# 🎉 NBA Predictor - Setup Complete!

**Repository Name:** NBA Predictor  
**Location:** `/Users/shauryamallampati/Desktop/NBA prediction/`  
**Status:** ✅ Git initialized | ✅ venv configured | ✅ Poetry ready

---

## ✅ What's Been Setup

### 1. Git Repository
- **Initialized:** Git repo with main branch
- **Initial Commit:** Consolidation of both implementations (321 files)
- **Backups:** Both old folders preserved in `backups/` folder

**View commit:**
```bash
git log --oneline -1
```

### 2. Python Virtual Environment
- **Type:** venv
- **Location:** `venv/`
- **Python Version:** 3.10.14
- **Status:** Active and ready

**Activate anytime:**
```bash
source venv/bin/activate
```

### 3. Poetry & Dependencies
- **Poetry Version:** 2.2.1
- **Status:** Installed and ready
- **Dependencies:** All Python packages installed

**Check installed packages:**
```bash
poetry show
```

---

## 🚀 Quick Start

### 1. Activate Environment
```bash
cd "/Users/shauryamallampati/Desktop/NBA prediction"
source venv/bin/activate
```

### 2. Setup API Keys
```bash
cp .env.example .env
nano .env  # Fill in your real API keys
```

### 3. Start Docker Services
```bash
docker-compose up -d
```

### 4. Test API Keys
```bash
make key-audit
```

### 5. Download Data
```bash
make seed
```

### 6. Run Backend
```bash
make serve  # Starts FastAPI on http://localhost:8000
```

### 7. Run Frontend (in another terminal)
```bash
make web   # Starts Next.js on http://localhost:3000
```

---

## 📁 Repository Structure

```
NBA Predictor/
├── .git/                    # Git repository
├── venv/                    # Python virtual environment
├── src/                     # Python source code
│   ├── common/             # Config, validators, logging
│   ├── data/               # Data ingestion & preprocessing
│   ├── models/             # ML models (pregame, live, chemistry, etc)
│   └── services/           # FastAPI backend
├── app/                    # Next.js frontend
├── components/             # React components
├── tests/                  # Unit & integration tests
├── notebooks/              # Analysis notebooks
├── configs/                # YAML configuration files
├── Makefile                # Command shortcuts
├── pyproject.toml          # Python dependencies
├── package.json            # Node dependencies
├── docker-compose.yml      # PostgreSQL + Redis
└── backups/                # Timestamped backups
```

---

## 🔑 Important Commands

**All commands assume you're in the root directory with venv activated**

### Development
```bash
make setup         # Install all dependencies
make up            # Start Docker (PostgreSQL, Redis)
make down          # Stop Docker
make key-audit     # Test all API keys
```

### Data & Features
```bash
make seed          # Download and prepare data
make data          # Build all features
```

### Training
```bash
make train-pregame     # Train pregame model
make train-live        # Train live win probability
make train-chemistry   # Train chemistry GNN
make train-vision      # Train vision classifier
make train-sentiment   # Train sentiment model (if keys present)
```

### Running Application
```bash
make serve         # Start FastAPI backend (port 8000)
make web           # Start Next.js frontend (port 3000)
make eval          # Run evaluations and generate plots
```

### Testing & Quality
```bash
make test          # Run all tests
make lint          # Run linters (ruff, mypy)
```

---

## 🎯 Next Steps (In Order)

1. **Fill in .env with API keys** (see `KEYS.md` for signup links)
   ```bash
   cp .env.example .env
   nano .env
   ```

2. **Test API connectivity**
   ```bash
   make key-audit
   ```

3. **Start Docker services**
   ```bash
   make up
   ```

4. **Begin data ingestion** (see task #9-11 in todo list)
   ```bash
   make seed
   ```

5. **Build features and train models** (see tasks #12-26)

6. **Run application** (see tasks #27-32)

---

## 📚 Documentation Files

- **`README.md`** - Main project documentation
- **`KEYS.md`** - API key requirements and signup links
- **`OVERVIEW.md`** - Complete project overview with roadmap
- **`MODEL_CARD.md`** - Model specifications and metrics
- **`DATA_USE.md`** - Data ethics and usage policy
- **`PROJECT_STATUS.md`** - Detailed project status
- **`CONSOLIDATION_GUIDE.md`** - How consolidation was done
- **`CONSOLIDATION_COMPLETE.md`** - Consolidation summary

---

## 🐛 Troubleshooting

### Can't activate venv?
```bash
python3 -m venv venv
source venv/bin/activate
```

### Poetry install fails?
```bash
poetry install --no-root
# Or clear cache and try again
poetry cache clear PyPI --all
poetry install
```

### Port already in use?
```bash
# Check what's using port 8000 or 3000
lsof -i :8000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

### Docker won't start?
```bash
docker-compose down -v
docker-compose up -d
```

---

## 📞 Support

- Check `README.md` for quick start
- See `KEYS.md` for API setup
- Review `OVERVIEW.md` for full roadmap
- Check todo list for task details

---

**Setup Date:** October 26, 2025  
**Project Status:** Ready for Development  
**Next Milestone:** API Keys → Data Ingestion → First Model Training

---

## Quick Git Commands

```bash
# Check status
git status

# View commits
git log --oneline

# Create new branch for feature work
git checkout -b feature/my-feature

# Stage and commit changes
git add .
git commit -m "Your message"

# View changes
git diff

# Push to remote (once set up)
git push origin main
```

**Ready to code!** 🚀
