#!/bin/bash

# Docker startup script for MCP PDF Q&A Application

echo "🐳 Starting MCP PDF Q&A Application with Docker..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please add your PERPLEXITY_API_KEY"
        echo ""
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Check if PERPLEXITY_API_KEY is set
source .env
if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo "❌ Error: PERPLEXITY_API_KEY not set in .env file"
    echo "Please add your Perplexity API key to the .env file"
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check backend health
echo "🔍 Checking backend health..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend may still be starting..."
fi

# Check frontend
echo "🔍 Checking frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "=========================================="
echo "✨ Application is running!"
echo "=========================================="
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "   All services:  docker-compose logs -f"
echo "   Backend only:  docker-compose logs -f backend"
echo "   Frontend only: docker-compose logs -f frontend"
echo ""
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo "=========================================="
