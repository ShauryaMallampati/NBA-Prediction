#!/bin/bash
# Quick start script for NBA Intelligence Platform

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  NBA Intelligence Platform - Startup   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Parse arguments
MODE=${1:-compose}

if [ "$MODE" = "compose" ]; then
    echo -e "${YELLOW}Starting with Docker Compose...${NC}"
    echo ""
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        cat > .env << EOF
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=nba_intel
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
EOF
        echo -e "${GREEN}✓ .env file created${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build
    
    echo ""
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✓ Services started!${NC}"
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo -e "  ${GREEN}Frontend${NC}:  http://localhost:3000/predictions"
    echo -e "  ${GREEN}API${NC}:       http://localhost:8000/docs"
    echo -e "  ${GREEN}Database${NC}:  localhost:5432"
    echo -e "  ${GREEN}Cache${NC}:     localhost:6379"
    echo ""
    echo -e "${YELLOW}Monitor logs:${NC}"
    echo "  API:      docker logs -f nba_intel_api"
    echo "  Web:      docker logs -f nba_intel_web"
    echo "  Database: docker logs -f nba_intel_postgres"
    echo ""

elif [ "$MODE" = "dev" ]; then
    echo -e "${YELLOW}Starting in development mode...${NC}"
    echo ""
    
    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}❌ Poetry not found. Please install Poetry.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Starting Backend...${NC}"
    poetry run python -m src.services.api.main &
    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    
    echo ""
    echo -e "${YELLOW}Starting Frontend...${NC}"
    cd nba-intel-platform
    NEXT_PUBLIC_BACKEND_URL=http://localhost:8000 npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    cd ..
    
    echo ""
    echo -e "${BLUE}Services:${NC}"
    echo -e "  ${GREEN}Frontend${NC}:  http://localhost:3000/predictions"
    echo -e "  ${GREEN}API${NC}:       http://localhost:8000/docs"
    echo ""
    
    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
    
elif [ "$MODE" = "stop" ]; then
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
    
elif [ "$MODE" = "logs" ]; then
    echo -e "${YELLOW}Showing logs...${NC}"
    docker-compose logs -f
    
elif [ "$MODE" = "test" ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    poetry run pytest tests/ -v
    
else
    echo -e "${RED}Unknown mode: $MODE${NC}"
    echo ""
    echo "Usage: ./startup.sh [MODE]"
    echo ""
    echo "Modes:"
    echo "  compose  - Run with Docker Compose (default)"
    echo "  dev      - Run in development mode"
    echo "  stop     - Stop Docker services"
    echo "  logs     - Show Docker logs"
    echo "  test     - Run tests"
    exit 1
fi

