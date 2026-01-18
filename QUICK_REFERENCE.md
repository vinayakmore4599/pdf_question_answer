# 🎯 Quick Reference Guide

## One-Page Architecture Overview

### System at a Glance

```
┌─────────────┐
│   Browser   │ ← You use this: http://localhost:3000
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│HTTP Proxy   │ ← Port 8000: backend/mcp_proxy.py
└──────┬──────┘
       │ JSON-RPC (stdio)
       ▼
┌─────────────┐
│ MCP Server  │ ← Core engine: src/mcp_server.py
└──────┬──────┘
       │
       ├─────► PDF Processor (extract text)
       ├─────► RAG System (vector search)
       └─────► Perplexity AI (generate answer)
```

## 🚀 Quick Start Commands

```bash
# Start everything
./start.sh

# Stop everything  
./stop.sh

# Check status
curl http://localhost:8000/
open http://localhost:3000

# View logs
tail -f output/logs/backend.log
```

## 📂 Important Files

### You'll Edit These Often
- `frontend/src/App.jsx` - UI changes
- `frontend/src/App.css` - Styling
- `.env` - API keys

### Core Backend (Don't touch unless needed)
- `src/mcp_server.py` - MCP protocol
- `src/rag_system.py` - Vector search
- `src/perplexity_client.py` - AI calls

### Configuration
- `requirements.txt` - Python packages
- `frontend/package.json` - Node packages

### Scripts
- `start.sh` - Start app ✅ USE THIS
- `stop.sh` - Stop app
- `start_all.sh` - Show MCP config for Claude

## 🔧 Common Tasks

### Add a New Python Package
```bash
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Add a New Frontend Package
```bash
cd frontend
npm install package-name
cd ..
```

### Change API Key
```bash
# Edit .env
PERPLEXITY_API_KEY=new_key_here

# Restart
./stop.sh && ./start.sh
```

### Clear Cached PDFs
```bash
rm -rf output/uploads/*
rm -rf output/cache/*
```

### View Errors
```bash
# Backend errors
cat output/logs/backend.log

# Frontend errors
# Check browser console (F12)
```

## 🎨 Customization Points

### Change UI Colors
**File:** `frontend/src/App.css`
```css
.chat-message.user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* Change these colors ↑ */
}
```

### Change Chunk Size (RAG)
**File:** `src/config.py`
```python
chunk_size: int = 1000  # Increase for larger chunks
chunk_overlap: int = 200  # Increase for more context
```

### Change Number of Retrieved Chunks
**File:** `backend/mcp_proxy.py`
```python
result = await mcp_client.call_tool(
    "answer_question_rag",
    {
        "top_k": 3  # Change to 5 for more context
    }
)
```

### Change AI Model
**File:** `src/config.py`
```python
model: str = "sonar"  # Change to other Perplexity model
```

## 🐛 Quick Debugging

### Problem: Port already in use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
./stop.sh
```

### Problem: Frontend won't connect
```bash
# Check backend is running
curl http://localhost:8000/

# Check CORS in backend/mcp_proxy.py
# Should have: "http://localhost:3000"
```

### Problem: MCP subprocess crashes
```bash
# Test MCP server directly
source venv/bin/activate
python src/mcp_server.py
# Type: {"jsonrpc":"2.0","id":1,"method":"tools/list"}
# Should see: JSON response with tools
```

### Problem: PDF won't upload
```bash
# Check uploads directory
ls -la output/uploads/

# Check file size (max usually ~50MB)
ls -lh your-file.pdf
```

## 📊 Performance Tips

### Speed Up Indexing
- **Cache enabled by default**
- First query: ~2-5 seconds (builds index)
- Next queries: ~0.5-1 second (uses cache)

### Reduce Token Usage
- Lower `top_k` from 3 to 2
- Reduce `chunk_size` from 1000 to 800

### Handle Large PDFs
- Increase `chunk_size` to 1500
- Increase `top_k` to 5
- May need more RAM

## 🔐 Security Checklist

- [ ] `.env` file not committed (in .gitignore)
- [ ] API keys not hardcoded
- [ ] CORS limited to localhost
- [ ] File uploads validated (PDF only)

## 📈 Monitoring

### Check System Health
```bash
# Backend status
curl http://localhost:8000/ | jq

# Memory usage
ps aux | grep python | grep backend

# Disk usage
du -sh output/*
```

### Logs Location
```
output/logs/backend.log    ← Backend errors/info
Browser console (F12)      ← Frontend errors
Terminal where ./start.sh  ← Startup messages
```

## 🎓 Learning Path

1. **Start here:** [README.md](README.md)
2. **Understand architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Learn RAG:** [RAG_COMPARISON.md](RAG_COMPARISON.md)
4. **Migration notes:** [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## 🆘 Get Help

### Check These First
1. Read error message in logs
2. Check this guide for common issues
3. Review [ARCHITECTURE.md](ARCHITECTURE.md) for how it works
4. Try `./stop.sh && ./start.sh` (restart fixes many issues)

### Still Stuck?
- GitHub Issues: https://github.com/vinayakmore4599/pdf_question_answer/issues
- Check logs: `cat output/logs/backend.log`
- Test MCP directly: `python src/mcp_server.py`

## 🎯 Success Metrics

Your system is working correctly if:
- ✅ Start takes ~10-15 seconds
- ✅ Upload takes 2-5 seconds
- ✅ First question takes 2-3 seconds
- ✅ Follow-up questions take 0.5-1.5 seconds
- ✅ Answers are formatted with markdown
- ✅ Can download chat as PDF
- ✅ No errors in logs

## 📝 Quick Reference: File Purposes

| File | Purpose | Edit? |
|------|---------|-------|
| `backend/mcp_proxy.py` | HTTP-to-MCP bridge | Rarely |
| `src/mcp_server.py` | MCP backend | Add tools |
| `src/rag_system.py` | Vector search | Tune params |
| `frontend/src/App.jsx` | UI logic | Often |
| `frontend/src/App.css` | Styling | Often |
| `.env` | API keys | When needed |
| `start.sh` | Startup | Rarely |
| `requirements.txt` | Python deps | When adding packages |

---

**Remember:** When in doubt, restart with `./stop.sh && ./start.sh` 🔄
