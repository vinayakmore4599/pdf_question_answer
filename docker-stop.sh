#!/bin/bash

# Docker stop script for MCP PDF Q&A Application

echo "🛑 Stopping MCP PDF Q&A Application..."
echo ""

docker-compose down

echo ""
echo "=========================================="
echo "✅ All containers stopped"
echo "=========================================="
echo ""
echo "To start again: ./docker-start.sh"
echo "To remove volumes: docker-compose down -v"
echo "=========================================="
