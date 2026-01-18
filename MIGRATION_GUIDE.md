# Architecture Migration Guide

## Old vs New Architecture

### Previous Architecture (REST API)
```
Browser → FastAPI (api.py) → Direct RAG/Perplexity → Response
```
- **File:** `backend/api.py`
- **Protocol:** Pure HTTP REST
- **Use case:** Web browsers only
- **MCP:** Not used

### Current Architecture (MCP-Powered)
```
Browser → HTTP Proxy (mcp_proxy.py) → MCP Server → RAG/Perplexity → Response
                                         ↓
                              Can also be used by:
                              Claude Desktop, AI assistants
```
- **File:** `backend/mcp_proxy.py`
- **Protocol:** HTTP → JSON-RPC → MCP
- **Use case:** Web browsers AND AI assistants
- **MCP:** Core backend protocol

## File Status

### Active Files (Current Architecture)
✅ `backend/mcp_proxy.py` - HTTP-to-MCP proxy server (ACTIVE)
✅ `src/mcp_server.py` - Pure MCP server backend (ACTIVE)
✅ `start.sh` - Updated to use mcp_proxy.py

### Legacy Files (Kept for Reference)
⚠️ `backend/api.py` - Old REST-only backend (INACTIVE)
   - Keep for reference or fallback
   - Not used by start.sh anymore
   - Can be deleted if not needed

### Shared Files (Used by Both)
🔄 `src/pdf_processor.py` - PDF extraction
🔄 `src/rag_system.py` - Vector embeddings & search
🔄 `src/perplexity_client.py` - AI integration
🔄 `src/config.py` - Configuration

## Which File Does What?

### Backend Files Comparison

| Feature | api.py (OLD) | mcp_proxy.py (NEW) |
|---------|--------------|---------------------|
| **Protocol** | HTTP REST only | HTTP + MCP |
| **Backend** | Direct Python code | MCP subprocess |
| **AI Integration** | Can't be used by Claude | Can be used by Claude Desktop |
| **Architecture** | Monolithic | Layered (Proxy + MCP) |
| **Started by** | Not used anymore | `./start.sh` |
| **Purpose** | Web app only | Web app + AI assistants |

### When to Use Which?

**Use `mcp_proxy.py` (NEW) when:**
- ✅ You want MCP protocol benefits
- ✅ You want AI assistant integration
- ✅ You want modern, layered architecture
- ✅ You're following the project's current direction

**Use `api.py` (OLD) when:**
- ⚠️ You only need web interface (no AI integration)
- ⚠️ You want simpler architecture (no subprocess)
- ⚠️ You're debugging issues with proxy approach
- ⚠️ You need a fallback during migration

## How to Switch Back to Old Architecture (If Needed)

1. Edit `start.sh`:
   ```bash
   # Change this line:
   nohup python backend/mcp_proxy.py > output/logs/backend.log 2>&1 &
   
   # To this:
   nohup python backend/api.py > output/logs/backend.log 2>&1 &
   ```

2. Restart:
   ```bash
   ./stop.sh
   ./start.sh
   ```

## Benefits of New Architecture

### 1. **Dual Use Case Support**
- Web browsers via HTTP
- AI assistants via MCP
- Same backend, two interfaces

### 2. **True MCP Implementation**
- Follows MCP protocol standards
- Can be discovered by MCP clients
- Tool registration and resource discovery

### 3. **Better Separation of Concerns**
- Proxy: Protocol translation
- MCP Server: Business logic
- Core modules: Shared processing

### 4. **Future-Proof**
- Easy to add more MCP tools
- Can scale to multiple MCP servers
- Standard protocol reduces lock-in

## Migration Checklist

✅ Created `backend/mcp_proxy.py`
✅ Updated `start.sh` to use proxy
✅ Updated `stop.sh` to kill both processes
✅ Updated `README.md` with new architecture
✅ Created `ARCHITECTURE.md` for detailed docs
✅ Kept `api.py` for reference/fallback

## Cleanup Options

### Option 1: Keep Both (Recommended for Now)
- Allows easy rollback if issues arise
- Useful for comparison and learning
- Minimal disk space cost

### Option 2: Archive Old File
```bash
mkdir -p archive
mv backend/api.py archive/api.py.backup
```

### Option 3: Delete Old File
```bash
rm backend/api.py
```
⚠️ Only do this after thoroughly testing new architecture

## Testing Checklist

Before removing old architecture, verify:

- [ ] Web interface loads at http://localhost:3000
- [ ] PDF upload works
- [ ] Question answering works
- [ ] Markdown rendering works
- [ ] PDF export works
- [ ] Multiple follow-up questions work
- [ ] MCP server can be used by Claude Desktop (optional)

## Troubleshooting

### Issue: Proxy won't start
**Solution:** Check if MCP server path is correct in mcp_proxy.py:
```python
mcp_server_path = Path(__file__).parent.parent / "src" / "mcp_server.py"
```

### Issue: Want to use old REST API
**Solution:** 
1. Edit start.sh to use `backend/api.py`
2. Restart with `./stop.sh && ./start.sh`

### Issue: Need to compare implementations
**Solution:** Both files are similar. Key difference:
- `api.py`: Calls RAG/Perplexity directly
- `mcp_proxy.py`: Calls via MCP subprocess

## Questions?

- Architecture details: See [ARCHITECTURE.md](ARCHITECTURE.md)
- Getting started: See [README.md](README.md)
- RAG details: See [RAG_COMPARISON.md](RAG_COMPARISON.md)
