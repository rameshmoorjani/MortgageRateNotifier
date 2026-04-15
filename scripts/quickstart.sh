#!/bin/bash
# Quick Start Script for Production Deployment
# Usage: bash quickstart.sh

set -e

echo "=============================================================================="
echo "MORTGAGE RATE NOTIFIER - PRODUCTION QUICK START"
echo "=============================================================================="
echo ""

# Check Python
echo "[STEP 1] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "[OK] $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "[STEP 2] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "[STEP 3] Activating virtual environment..."
source venv/bin/activate
echo "[OK] Virtual environment activated"

# Install dependencies
echo ""
echo "[STEP 4] Installing dependencies..."
pip install -q -r requirements.txt
echo "[OK] Dependencies installed"

# Create logs directory
echo ""
echo "[STEP 5] Creating logs directory..."
mkdir -p logs
echo "[OK] Logs directory ready"

# Check .env
echo ""
echo "[STEP 6] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found"
    echo "Create .env with at minimum:"
    echo "  OPENAI_API_KEY=your-api-key-here"
else
    if grep -q "OPENAI_API_KEY" .env; then
        echo "[OK] .env file configured"
    else
        echo "[ERROR] OPENAI_API_KEY not found in .env"
        exit 1
    fi
fi

# Check users.json
echo ""
echo "[STEP 7] Checking user data..."
if [ ! -f "users.json" ]; then
    echo "[WARNING] users.json not found"
    echo "Create users.json with your user list"
else
    USER_COUNT=$(python3 -c "import json; print(len(json.load(open('users.json'))))")
    echo "[OK] users.json found with $USER_COUNT users"
fi

# Run tests
echo ""
echo "[STEP 8] Running validation tests..."
if python3 test_rag_system.py > /dev/null 2>&1; then
    echo "[OK] RAG system test passed"
else
    echo "[WARNING] RAG system test failed - check OPENAI_API_KEY"
fi

if python3 test_rag_batch.py > /dev/null 2>&1; then
    echo "[OK] Batch processing test passed"
else
    echo "[WARNING] Batch processing test failed"
fi

# Summary
echo ""
echo "=============================================================================="
echo "QUICK START COMPLETE"
echo "=============================================================================="
echo ""
echo "Next steps:"
echo "  1. Configure environment (if needed): nano .env"
echo "  2. Prepare users: nano users.json"
echo "  3. Test run: python3 start_production.py --mode once --users users.json"
echo "  4. Daily schedule: python3 start_production.py --mode daily --users users.json"
echo ""
echo "For help: python3 start_production.py --help"
echo "For detailed guide: see PRODUCTION_DEPLOYMENT.md"
echo ""
