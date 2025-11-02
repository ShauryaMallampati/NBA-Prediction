#!/bin/bash
# 🏀 NBA Intelligence Platform - Easy Start Script
# Runs both backend API and frontend together

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🏀 NBA Intelligence Platform Starting..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required files exist
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Make sure you're in the project root."
    exit 1
fi

if [ ! -d "nba-intel-platform" ]; then
    echo "❌ Error: nba-intel-platform directory not found."
    exit 1
fi

# Kill any existing processes on ports 8000 and 3000
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        kill $(lsof -t -i:8000) 2>/dev/null || true
    fi
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        kill $(lsof -t -i:3000) 2>/dev/null || true
    fi
    exit
}

trap cleanup SIGINT SIGTERM

echo "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo "${BLUE}│${NC} 🔧 Starting Backend API (FastAPI on port 8000)          ${BLUE}│${NC}"
echo "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Start backend in background
cd "$PROJECT_ROOT"
poetry run python src/services/api/main.py &
BACKEND_PID=$!
echo "${GREEN}✅ Backend process started (PID: $BACKEND_PID)${NC}"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

echo "${GREEN}✅ Backend API running on http://localhost:8000${NC}"
echo "${GREEN}✅ API Docs available at http://localhost:8000/docs${NC}"
echo ""

echo "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo "${BLUE}│${NC} 🎨 Starting Frontend (Next.js on port 3000)             ${BLUE}│${NC}"
echo "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Start frontend in background
cd "$PROJECT_ROOT/nba-intel-platform"
npm run dev &
FRONTEND_PID=$!
echo "${GREEN}✅ Frontend process started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

echo ""
echo "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
echo "${GREEN}✅ NBA INTELLIGENCE PLATFORM IS RUNNING! ✅${NC}"
echo "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""
echo "🌐 Access the application:"
echo "   ${GREEN}▶ Dashboard:        http://localhost:3000${NC}"
echo "   ${GREEN}▶ Predictions:      http://localhost:3000/predictions${NC}"
echo "   ${GREEN}▶ Live Games:       http://localhost:3000/live${NC}"
echo "   ${GREEN}▶ API Docs:         http://localhost:8000/docs${NC}"
echo ""
echo "📊 Model Info:"
echo "   ${YELLOW}▶ Accuracy: 63.83%${NC}"
echo "   ${YELLOW}▶ ROC-AUC: 0.6701${NC}"
echo "   ${YELLOW}▶ Features: 30 engineered${NC}"
echo ""
echo "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait
