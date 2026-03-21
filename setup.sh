#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 LoadPilot Setup"
echo "=================="

# Backend with venv
echo ""
echo "📦 Setting up backend with virtual environment..."
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "   ✅ Backend dependencies installed"
else
    echo "   ❌ Failed to install backend dependencies"
    exit 1
fi

# Frontend
if command -v npm &> /dev/null; then
    echo ""
    echo "📦 Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Frontend dependencies installed"
    else
        echo "   ⚠️  Frontend setup failed"
    fi
else
    echo ""
    echo "⚠️  npm not found - skipping frontend setup"
    echo "   Install Node.js from https://nodejs.org to run the UI"
fi

echo ""
echo "=================="
echo "✅ Setup complete!"
echo ""
echo "To start:"
echo "   ./start.sh"
echo ""
echo "Optional - Install Ollama for AI features:"
echo "   brew install ollama"
echo "   ollama pull llama3.2"
