#!/bin/bash

# MCP Configuration Information
# This script displays how to integrate the MCP server with Claude Desktop
# 
# NOTE: To start the web app, use: ./start.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "📘 MCP Server Configuration Guide"
echo "=========================================="
echo ""
echo "This PDF Q&A system can be used in two ways:"
echo ""
echo "1️⃣  WEB APPLICATION (Browser)"
echo "   Command: ./start.sh"
echo "   Access:  http://localhost:3000"
echo ""
echo "2️⃣  MCP INTEGRATION (Claude Desktop)"
echo "   The MCP server can be used directly by AI assistants"
echo ""
echo "=========================================="
echo "🤖 Claude Desktop Setup"
echo "=========================================="
echo ""
echo "Configuration file location:"
echo "  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "  Windows: %APPDATA%/Claude/claude_desktop_config.json"
echo ""
echo "Add this configuration:"
echo ""
echo "{
  \"mcpServers\": {
    \"pdf-qa\": {
      \"command\": \"$SCRIPT_DIR/venv/bin/python\",
      \"args\": [\"$SCRIPT_DIR/src/mcp_server.py\"],
      \"env\": {
        \"PERPLEXITY_API_KEY\": \"$(grep PERPLEXITY_API_KEY .env 2>/dev/null | cut -d '=' -f2 || echo 'YOUR_API_KEY_HERE')\"
      }
    }
  }
}"
echo ""
echo "=========================================="
echo "💡 Usage Examples"
echo "=========================================="
echo ""
echo "After configuring Claude Desktop, you can:"
echo "  • Ask Claude to analyze PDFs using MCP tools"
echo "  • Use RAG-based question answering"
echo "  • Extract text from PDFs"
echo "  • Get document metadata"
echo ""
echo "Example: 'Can you analyze document.pdf and answer"
echo "          questions about it?'"
echo ""
echo "=========================================="
echo "🚀 Quick Commands"
echo "=========================================="
echo ""
echo "  ./start.sh     - Start web application"
echo "  ./stop.sh      - Stop web application"
echo ""
echo "=========================================="
