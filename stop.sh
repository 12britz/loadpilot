#!/bin/bash

echo "🛑 Stopping LoadPilot..."

pkill -f "uvicorn main:app" 2>/dev/null && echo "   ✅ Backend stopped" || echo "   - Backend not running"
pkill -f "vite" 2>/dev/null && echo "   ✅ Frontend stopped" || echo "   - Frontend not running"

echo "✅ All services stopped"

# Optional: clear database
if [ "$1" = "--clean" ]; then
    rm -f "$(dirname "$0")/backend/loadpilot.db"
    echo "🗑️  Database cleared"
fi
