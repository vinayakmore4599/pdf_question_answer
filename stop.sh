#!/bin/bash

# PDF Q&A Application Shutdown Script
# Stops both backend and frontend servers

echo "🛑 Stopping PDF Q&A Application..."
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to kill processes on a port
kill_port() {
    local port=$1
    local name=$2
    
    echo "🔍 Checking port $port ($name)..."
    
    # Kill by port
    lsof -ti:$port 2>/dev/null | while read pid; do
        echo "   Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null || true
    done
}

# Kill by saved PIDs
if [ -f "output/logs/backend.pid" ]; then
    BACKEND_PID=$(cat output/logs/backend.pid)
    echo "🔍 Stopping backend (PID: $BACKEND_PID)..."
    kill -9 $BACKEND_PID 2>/dev/null || true
    rm output/logs/backend.pid
fi

if [ -f "output/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat output/logs/frontend.pid)
    echo "🔍 Stopping frontend (PID: $FRONTEND_PID)..."
    kill -9 $FRONTEND_PID 2>/dev/null || true
    rm output/logs/frontend.pid
fi

# Kill by port (backup method)
kill_port 8000 "Backend"
kill_port 3000 "Frontend"

# Kill any remaining processes
pkill -9 -f "python backend/api.py" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
pkill -9 -f "npm run dev" 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ All servers stopped successfully"
echo "=========================================="

# Verify ports are free
sleep 1
if lsof -i:8000,3000 &> /dev/null; then
    echo "⚠️  Warning: Some processes may still be running"
    lsof -i:8000,3000
else
    echo "✓ Ports 8000 and 3000 are now free"
fi
