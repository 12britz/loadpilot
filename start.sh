#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting LoadPilot"
echo "====================="

# Kill existing processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

sleep 1

# Check for venv
VENV_DIR="$SCRIPT_DIR/backend/venv"
VENV_ACTIVATE=""
if [ -d "$VENV_DIR" ]; then
    VENV_ACTIVATE="source $VENV_DIR/bin/activate"
    echo "Using virtual environment"
else
    echo "No virtual environment found, using system Python"
fi

# Start backend
echo ""
echo "⚡ Starting backend (FastAPI)..."
cd "$SCRIPT_DIR/backend"

if [ -n "$VENV_ACTIVATE" ]; then
    $VENV_ACTIVATE && uvicorn main:app --host 0.0.0.0 --port 8000 &
else
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!

sleep 3

if ps -p $BACKEND_PID > /dev/null 2>&1 || curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "   ✅ Backend running on http://localhost:8000"
    echo "   📖 API Docs: http://localhost:8000/docs"
else
    echo "   ❌ Backend failed to start"
    exit 1
fi

# Start frontend if npm available
if command -v npm &> /dev/null; then
    echo ""
    echo "⚡ Starting frontend (React)..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
    
    sleep 3
    
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "   ✅ Frontend running on http://localhost:3000"
    else
        echo "   ⚠️  Frontend failed to start"
    fi
else
    echo ""
    echo "⚠️  npm not found - frontend not started"
fi

echo ""
echo "====================="
echo "✅ LoadPilot is running!"
echo ""
echo "   Backend:  http://localhost:8000"
if command -v npm &> /dev/null; then
    echo "   Frontend: http://localhost:3000"
fi
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping LoadPilot..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    echo "✅ Stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait
