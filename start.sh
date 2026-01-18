#!/bin/bash

# PDF Q&A Application Startup Script
# Starts both backend (port 8000) and frontend (port 3000)

set -e

echo "🚀 Starting PDF Q&A Application..."
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Start Backend (MCP Proxy)
echo "📦 Starting MCP proxy server (port 8000)..."
source venv/bin/activate
nohup python backend/mcp_proxy.py > output/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ MCP Proxy started (PID: $BACKEND_PID)"
echo ""

# Wait a bit for backend to start
sleep 2

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo ""
fi

# Start Frontend
echo "🎨 Starting frontend server (port 3000)..."
cd frontend
nohup npm run dev > ../output/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

# Save PIDs for stopping later
echo "$BACKEND_PID" > output/logs/backend.pid
echo "$FRONTEND_PID" > output/logs/frontend.pid

echo "=========================================="
echo "✨ Application is running!"
echo "=========================================="
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  output/logs/backend.log"
echo "   Frontend: output/logs/frontend.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo "=========================================="
