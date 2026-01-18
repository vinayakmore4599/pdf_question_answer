# 🏗️ Architecture Documentation

## System Architecture Overview

This document provides a comprehensive understanding of the PDF Q&A system architecture for developers new to MCP (Model Context Protocol) and RAG (Retrieval-Augmented Generation).

## 📊 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         PDF Q&A System                                  │
│                    MCP-Powered Web Application                          │
└────────────────────────────────────────────────────────────────────────┘

        ┌──────────────┐
        │    User      │
        │  (Browser)   │
        └──────┬───────┘
               │
               │ HTTP (Port 3000)
               ▼
┌──────────────────────────────────────┐
│     FRONTEND LAYER                   │
│  ┌────────────────────────────────┐  │
│  │   React + Vite                 │  │
│  │  • App.jsx - Chat UI           │  │
│  │  • ReactMarkdown - Formatting  │  │
│  │  • jsPDF - Export              │  │
│  │  • Axios - HTTP Client         │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               │ HTTP REST API
               │ POST /upload
               │ POST /ask/{pdf_id}
               ▼
┌──────────────────────────────────────┐
│     PROXY LAYER                      │
│  ┌────────────────────────────────┐  │
│  │   FastAPI HTTP-to-MCP Proxy    │  │
│  │  • backend/mcp_proxy.py        │  │
│  │  • MCPClient class             │  │
│  │  • Subprocess management       │  │
│  │  • Protocol translation        │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               │ JSON-RPC 2.0 over stdio
               │ (pipes: stdin/stdout)
               ▼
┌──────────────────────────────────────┐
│     MCP SERVER LAYER                 │
│  ┌────────────────────────────────┐  │
│  │   Model Context Protocol       │  │
│  │  • src/mcp_server.py           │  │
│  │  • Tools registration          │  │
│  │  • Resource discovery          │  │
│  │  • JSON-RPC handling           │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│     PROCESSING LAYER                 │
│  ┌────────────────────────────────┐  │
│  │   RAG Pipeline                 │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │  1. PDF Processor        │  │  │
│  │  │     • pdfplumber         │  │  │
│  │  │     • Text extraction    │  │  │
│  │  │     • Metadata           │  │  │
│  │  └──────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │  2. RAG System           │  │  │
│  │  │     • Text chunking      │  │  │
│  │  │     • Embeddings         │  │  │
│  │  │     • FAISS indexing     │  │  │
│  │  │     • Similarity search  │  │  │
│  │  └──────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  │  │
│  │  │  3. Perplexity Client    │  │  │
│  │  │     • API calls          │  │  │
│  │  │     • Answer generation  │  │  │
│  │  │     • Summarization      │  │  │
│  │  └──────────────────────────┘  │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

## 🔄 Request Flow Diagram

### Complete Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    QUESTION ANSWERING FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

1. USER INPUT
   ┌──────────────────────────┐
   │ User types: "What is     │
   │ the main conclusion?"    │
   └────────────┬─────────────┘
                │
                ▼
2. FRONTEND (React)
   ┌──────────────────────────┐
   │ • Validate input         │
   │ • Add to chat UI         │
   │ • Show typing indicator  │
   │ • axios.post(/ask)       │
   └────────────┬─────────────┘
                │ HTTP POST
                │ {question: "What..."}
                ▼
3. HTTP PROXY (FastAPI)
   ┌──────────────────────────┐
   │ • Receive HTTP request   │
   │ • Get pdf_path from ID   │
   │ • Build JSON-RPC msg:    │
   │   {                      │
   │     method: "tools/call" │
   │     params: {            │
   │       name: "answer_q... │
   │       arguments: {...}   │
   │     }                    │
   │   }                      │
   │ • Write to MCP stdin     │
   └────────────┬─────────────┘
                │ stdio pipe
                │ JSON-RPC
                ▼
4. MCP SERVER
   ┌──────────────────────────┐
   │ • Read from stdin        │
   │ • Parse JSON-RPC         │
   │ • Route to tool handler  │
   │ • call_tool("answer_... │
   └────────────┬─────────────┘
                │
                ▼
5. PDF PROCESSOR
   ┌──────────────────────────┐
   │ • Load PDF from path     │
   │ • Extract text           │
   │ • Split into chunks:     │
   │   ["Chunk 1...",         │
   │    "Chunk 2...",         │
   │    ... 100+ chunks]      │
   └────────────┬─────────────┘
                │
                ▼
6. RAG SYSTEM - Embedding
   ┌──────────────────────────┐
   │ • Load model:            │
   │   all-MiniLM-L6-v2       │
   │ • Encode chunks:         │
   │   chunk → [0.23, -0.45,  │
   │            ..., 0.12]    │
   │   (384 dimensions)       │
   │ • Store in FAISS         │
   └────────────┬─────────────┘
                │
                ▼
7. RAG SYSTEM - Retrieval
   ┌──────────────────────────┐
   │ • Embed question         │
   │ • FAISS similarity:      │
   │   question_vec.search()  │
   │ • Get top-k=3:           │
   │   indices: [45, 12, 89]  │
   │ • Retrieve chunks:       │
   │   context = chunks[45] + │
   │             chunks[12] + │
   │             chunks[89]   │
   └────────────┬─────────────┘
                │
                ▼
8. PERPLEXITY CLIENT
   ┌──────────────────────────┐
   │ • Build prompt:          │
   │   "Context: {context}    │
   │    Question: {question}  │
   │    Answer from PDF only" │
   │ • API call to sonar      │
   │ • Get raw answer         │
   │ • Summarize (2nd call):  │
   │   Format as markdown     │
   └────────────┬─────────────┘
                │
                ▼
9. RESPONSE PATH
   ┌──────────────────────────┐
   │ MCP Server:              │
   │ • Wrap in JSON-RPC       │
   │ • Write to stdout        │
   └────────────┬─────────────┘
                │ stdio pipe
                ▼
   ┌──────────────────────────┐
   │ HTTP Proxy:              │
   │ • Read from stdout       │
   │ • Parse JSON-RPC         │
   │ • Extract answer text    │
   │ • Return HTTP response   │
   └────────────┬─────────────┘
                │ HTTP 200
                │ JSON response
                ▼
   ┌──────────────────────────┐
   │ Frontend:                │
   │ • Receive response       │
   │ • ReactMarkdown render   │
   │ • Add to chat history    │
   │ • Hide typing indicator  │
   └──────────────────────────┘
                │
                ▼
   ┌──────────────────────────┐
   │ User sees formatted      │
   │ markdown answer in UI    │
   └──────────────────────────┘

Total Time: ~1-3 seconds
Token Savings: 98% (compared to sending full PDF)
```

## 🧩 Component Details

### 1. Frontend Layer (React)

**Technology Stack:**
- React 18 (UI framework)
- Vite (Build tool & dev server)
- Axios (HTTP client)
- ReactMarkdown (Rendering formatted answers)
- jsPDF (PDF export)

**Key Files:**
```
frontend/
├── src/
│   ├── App.jsx          # Main component
│   │   ├── State: chatMessages, currentPdf, loading
│   │   ├── Functions: handleUpload, handleAskQuestion
│   │   └── UI: Chat interface, file upload, export
│   └── App.css          # Styling
│       ├── .chat-message styles
│       ├── .markdown-content formatting
│       └── Responsive design
└── package.json
```

**State Management:**
```javascript
// Chat message structure
chatMessages = [
  {
    type: 'user',
    content: 'What is the conclusion?',
    timestamp: '2026-01-18T14:30:22'
  },
  {
    type: 'assistant',
    content: '## Conclusion\n\nThe main finding...',
    timestamp: '2026-01-18T14:30:25'
  }
]
```

**API Integration:**
```javascript
// Upload PDF
POST http://localhost:8000/upload
FormData: { file: pdfFile }
Response: { pdf_id, filename, num_pages }

// Ask question
POST http://localhost:8000/ask/{pdf_id}
Body: { question: "..." }
Response: { answers: [{ question, answer, model }] }
```

### 2. Proxy Layer (FastAPI)

**Purpose:** Bridge between web HTTP and MCP stdio protocols

**Key Components:**

```python
class MCPClient:
    """Manages MCP server subprocess communication"""
    
    process: asyncio.subprocess.Process
    request_id: int
    lock: asyncio.Lock  # Prevent concurrent stdin writes
    
    async def start():
        # Spawn: python src/mcp_server.py
        # Capture stdin/stdout/stderr
        
    async def call_tool(name, arguments):
        # 1. Build JSON-RPC request
        # 2. Write to process.stdin
        # 3. Read from process.stdout
        # 4. Parse JSON-RPC response
        # 5. Return result
```

**Lifecycle:**
```
App Startup:
  └─> startup_event()
      └─> mcp_client.start()
          └─> Spawn MCP server process
              └─> Wait 2s for initialization

Request Handling:
  └─> /ask endpoint
      └─> mcp_client.call_tool()
          └─> JSON-RPC request → stdin
          └─> JSON-RPC response ← stdout
          └─> Return HTTP response

App Shutdown:
  └─> shutdown_event()
      └─> mcp_client.stop()
          └─> process.terminate()
```

**Why This Layer Exists:**
- **Protocol Mismatch:** Browsers speak HTTP, MCP speaks stdio
- **Process Management:** MCP server needs to be started/stopped
- **State Translation:** HTTP sessions → MCP tool calls
- **Error Handling:** Convert MCP errors to HTTP status codes

### 3. MCP Server Layer

**MCP Concepts for Beginners:**

**What is MCP?**
Model Context Protocol is a standardized way for AI assistants (like Claude) to interact with external tools and data sources.

**Key MCP Elements:**

1. **Tools** - Functions AI can call
```python
Tool(
    name="answer_question_rag",
    description="Answer questions using RAG",
    inputSchema={
        "pdf_path": "string",
        "question": "string",
        "top_k": "integer (optional)"
    }
)
```

2. **Resources** - Data AI can access
```python
Resource(
    uri="pdf://document.pdf",
    name="document.pdf",
    mimeType="application/pdf"
)
```

3. **JSON-RPC 2.0** - Communication protocol
```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "answer_question_rag",
    "arguments": {
      "pdf_path": "doc.pdf",
      "question": "What...?"
    }
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "The answer is..."
      }
    ]
  }
}
```

**Server Implementation:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("pdf-qa-server")

@app.list_tools()
async def list_tools():
    """AI asks: What tools are available?"""
    return [tool1, tool2, ...]

@app.call_tool()
async def call_tool(name, arguments):
    """AI says: Call this tool with these args"""
    if name == "answer_question_rag":
        return await handle_rag_query(arguments)

# Start server (stdio communication)
async def main():
    async with stdio_server() as streams:
        await app.run(*streams)
```

### 4. Processing Layer (RAG Pipeline)

**A. PDF Processor**

```python
class PDFProcessor:
    def extract_text(self, pdf_path):
        # pdfplumber opens PDF
        # Extract text page by page
        # Return: "Full document text..."
        
    def extract_metadata(self, pdf_path):
        # Get: title, author, pages, size
        # Return: dict with metadata
```

**B. RAG System**

**What is RAG?**
Retrieval-Augmented Generation improves AI answers by:
1. Finding relevant information (Retrieval)
2. Using it to generate better answers (Augmented Generation)

**Why RAG?**
- **Problem:** AI models have token limits (can't send 1000-page PDF)
- **Solution:** Send only relevant excerpts (3-5 chunks)
- **Benefit:** 98% reduction in tokens + faster responses

**How it Works:**

```python
class OptimizedRAGSystem:
    
    # STEP 1: Index document
    def index_document(self, text, metadata):
        # Split text into chunks
        chunks = split_text(
            text,
            chunk_size=1000,      # chars per chunk
            overlap=200           # overlap for context
        )
        # Example:
        # chunks = [
        #   "Introduction: This paper...",  # 1000 chars
        #   "...novel approach. Methods...", # 1000 chars (200 overlap)
        #   "...experiment. Results show..." # 1000 chars
        # ]
        
        # Generate embeddings (convert text → numbers)
        embeddings = sentence_transformer.encode(chunks)
        # [[0.23, -0.45, ..., 0.12],  # 384 numbers
        #  [0.15, -0.32, ..., 0.08],
        #  ...]
        
        # Store in FAISS (vector database)
        faiss_index.add(embeddings)
        
        # Cache for future queries
        save_to_disk(faiss_index)
    
    # STEP 2: Retrieve relevant chunks
    def get_context_for_question(self, question, top_k=3):
        # Embed question
        q_embedding = model.encode([question])
        # [0.18, -0.39, ..., 0.11]
        
        # Find similar chunks
        distances, indices = faiss_index.search(q_embedding, k=top_k)
        # distances: [0.12, 0.18, 0.25]  # Lower = more similar
        # indices: [45, 12, 89]           # Which chunks
        
        # Get chunk texts
        relevant_chunks = [chunks[i] for i in indices]
        
        # Combine into context
        context = "\n\n".join(relevant_chunks)
        
        return context, metadata_about_chunks
```

**Embeddings Explained:**

```
Text: "The quick brown fox"
       ↓ Sentence Transformer (all-MiniLM-L6-v2)
Vector: [0.23, -0.45, 0.12, ..., 0.89]  (384 numbers)

Why? Similar text → similar vectors
"The quick brown fox" ≈ "A fast brown animal"
[0.23, -0.45, ...]    ≈ [0.25, -0.43, ...]

Different text → different vectors  
"The quick brown fox" ≠ "Python programming"
[0.23, -0.45, ...]    ≠ [-0.78, 0.91, ...]
```

**FAISS Explained:**

```
FAISS = Facebook AI Similarity Search
Purpose: Find nearest vectors super fast

Example:
Index contains 1000 document chunks (1000 vectors)
Question: "What is the methodology?"
Query vector: [0.18, -0.39, ..., 0.11]

FAISS searches all 1000 vectors in milliseconds!
Returns top-3 most similar:
  #45: distance 0.12 (very similar)
  #12: distance 0.18 (similar)
  #89: distance 0.25 (somewhat similar)
```

**C. Perplexity Client**

```python
class PerplexityClient:
    
    def analyze_document(self, question, context):
        """First call: Get answer from PDF content"""
        
        messages = [
            {
                "role": "system",
                "content": "Answer ONLY from provided PDF context"
            },
            {
                "role": "user",
                "content": f"""
                PDF Context:
                {context}
                
                Question: {question}
                """
            }
        ]
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json={
                "model": "sonar",
                "messages": messages
            }
        )
        
        raw_answer = response.json()["choices"][0]["message"]["content"]
        return raw_answer
    
    def summarize_answer(self, answer):
        """Second call: Format answer as markdown"""
        
        messages = [
            {
                "role": "user",
                "content": f"""
                Format this answer as structured markdown:
                {answer}
                
                Use headers, bullet points, code blocks.
                """
            }
        ]
        
        formatted = requests.post(...)
        return formatted_answer
```

**Two-Stage Processing:**
1. **Extraction:** Focus on accuracy (answer from PDF)
2. **Summarization:** Focus on formatting (make it pretty)

## 🔌 Protocol Translation

### HTTP ↔ JSON-RPC Mapping

```
┌─────────────────────────────────────────────────────┐
│              Protocol Translation                    │
└─────────────────────────────────────────────────────┘

HTTP Request:
  POST /ask/doc.pdf_123
  {
    "question": "What is the conclusion?"
  }

        ↓ Proxy translates ↓

JSON-RPC Request (to MCP stdin):
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "answer_question_rag",
      "arguments": {
        "pdf_path": "/path/to/doc.pdf",
        "question": "What is the conclusion?",
        "top_k": 3
      }
    }
  }

        ↓ MCP processes ↓

JSON-RPC Response (from MCP stdout):
  {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "content": [
        {
          "type": "text",
          "text": "## Conclusion\n\nThe main finding..."
        }
      ]
    }
  }

        ↓ Proxy translates ↓

HTTP Response:
  {
    "pdf_id": "doc.pdf_123",
    "answers": [
      {
        "question": "What is the conclusion?",
        "answer": "## Conclusion\n\nThe main finding...",
        "model": "sonar (via MCP)"
      }
    ],
    "processing_time": 1.23
  }
```

## 📦 Data Storage

### In-Memory Storage (Current)

```python
# HTTP Proxy maintains:
pdf_uploads = {
    "doc.pdf_20260118_143000": "/path/to/uploads/doc.pdf",
    "report.pdf_20260118_143100": "/path/to/uploads/report.pdf"
}

# MCP Server maintains:
rag_systems = {
    "/path/to/doc.pdf": RAGSystem(faiss_index, chunks),
    "/path/to/report.pdf": RAGSystem(faiss_index, chunks)
}
```

### Persistent Storage

```
output/
├── uploads/              # Uploaded PDF files
│   ├── 20260118_143000_document.pdf
│   └── 20260118_143100_report.pdf
├── cache/                # FAISS indices (for faster re-indexing)
│   ├── document_pdf.faiss
│   └── report_pdf.faiss
└── logs/                 # Application logs
    ├── backend.log
    └── mcp_server.log
```

## 🔄 Process Lifecycle

```
┌─────────────────────────────────────────────────────┐
│                System Startup                        │
└─────────────────────────────────────────────────────┘

1. ./start.sh executed
   │
   ├─> Start MCP Proxy (backend/mcp_proxy.py)
   │   │
   │   ├─> FastAPI app initializes
   │   ├─> startup_event() triggered
   │   ├─> MCPClient.start()
   │   │   └─> Spawn subprocess: python src/mcp_server.py
   │   │       ├─> MCP server loads models
   │   │       ├─> Registers tools
   │   │       └─> Listens on stdin
   │   │
   │   └─> Uvicorn starts on port 8000
   │
   └─> Start Frontend (cd frontend && npm run dev)
       └─> Vite dev server on port 3000

2. System ready
   ├─> Web UI: http://localhost:3000
   ├─> HTTP API: http://localhost:8000
   └─> MCP: Running as subprocess

┌─────────────────────────────────────────────────────┐
│                System Shutdown                       │
└─────────────────────────────────────────────────────┘

1. ./stop.sh executed
   │
   ├─> Kill processes on ports 8000, 3000
   │
   ├─> shutdown_event() in proxy
   │   └─> MCPClient.stop()
   │       └─> MCP process terminated
   │
   └─> Cleanup PIDs and temp files
```

## 🎓 Key Takeaways for Beginners

### What Makes This Architecture Unique?

1. **Pure MCP Backend:**
   - True MCP server (not REST API pretending to be MCP)
   - Can be used by AI assistants directly
   - Standard protocol, not custom

2. **HTTP Bridge Pattern:**
   - Web browsers can't use stdio (MCP's communication method)
   - Proxy solves this by translating protocols
   - Best of both worlds: Web UI + AI integration

3. **RAG Efficiency:**
   - Sending full PDFs to AI is wasteful
   - Vector search finds relevant sections
   - 98% reduction in tokens = faster + cheaper

4. **Two-Stage AI Processing:**
   - First: Accurate extraction from PDF
   - Second: Beautiful formatting
   - Better results than single-pass

### Common Questions

**Q: Why not just use REST API?**
A: REST API works for web only. MCP allows AI assistants (Claude Desktop) to use our tools directly.

**Q: Why subprocess instead of HTTP between proxy and MCP?**
A: MCP protocol uses stdin/stdout. Subprocess is the standard way to communicate with MCP servers.

**Q: Can I skip the proxy and use MCP directly from browser?**
A: No, browsers don't support stdio communication. You need HTTP.

**Q: Why FAISS instead of database?**
A: FAISS is optimized for vector similarity search. Databases are slower for finding "similar" vectors.

**Q: Why local embeddings instead of API?**
A: Sentence Transformers runs locally (no API calls, no costs, no rate limits, privacy preserved).

---

**For more information:**
- [README.md](README.md) - Getting started
- [RAG_COMPARISON.md](RAG_COMPARISON.md) - RAG performance details
- [MCP Documentation](https://modelcontextprotocol.io/) - Official MCP docs
