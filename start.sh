#!/bin/bash

# Train Commute Optimizer - Quick Start Script
echo "🚂 Train Commute Optimizer - Quick Start"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if Node is available
if ! command -v node &> /dev/null; then
    echo "⚠️  Warning: Node.js is not installed"
    echo "   Frontend will not be available without Node.js"
    echo ""
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  Warning: uv is not installed"
    echo "   Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Falling back to pip..."
    USE_UV=false
else
    USE_UV=true
fi

echo "📦 Installing backend dependencies..."
if [ "$USE_UV" = true ]; then
    uv sync
else
    pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn[standard] pydantic python-dotenv requests
fi

# Check if database exists
if [ ! -f "train_data.db" ]; then
    echo ""
    echo "⚠️  Database not found!"
    echo "   Run: python cli.py fetch"
    echo "   This will download train data (takes ~30 seconds)"
    echo ""
    read -p "Fetch data now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python cli.py fetch
    fi
fi

# Install frontend dependencies if Node is available
if command -v node &> /dev/null; then
    echo ""
    echo "📦 Installing frontend dependencies..."
    cd web
    npm install
    cd ..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo ""
echo "Backend (Terminal 1):"
if [ "$USE_UV" = true ]; then
    echo "  uv run uvicorn app:app --reload"
else
    echo "  python app.py"
fi
echo ""

if command -v node &> /dev/null; then
    echo "Frontend (Terminal 2):"
    echo "  cd web && npm run dev"
    echo ""
    echo "Then open: http://localhost:3456"
else
    echo "Backend Only (no frontend):"
    echo "  Open: http://localhost:8000/api/docs"
fi

echo ""
echo "📖 See WEB_UI_README.md for full documentation"
echo ""