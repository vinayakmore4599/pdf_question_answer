# 🚀 MCP PDF Question-Answering System

An intelligent **Model Context Protocol (MCP)** based system for extracting information from PDF documents using **RAG (Retrieval-Augmented Generation)**. Features a modern React web interface with an MCP-powered backend architecture.

## 🎯 Key Features

### Core Capabilities
- **🔍 RAG-Based Architecture**: Vector search retrieves only relevant PDF sections
- **⚡ Efficient Processing**: 70-90% reduction in token consumption
- **🤖 MCP Protocol**: Pure MCP server with HTTP proxy bridge
- **💬 Interactive Chat**: Conversational interface with follow-up questions
- **📊 Smart Formatting**: Markdown-rendered answers with structured output
- **💾 Export Functionality**: Download chat history as PDF
- **🔄 Dual Access**: Web UI + AI assistant integration (Claude Desktop)

### Technical Excellence
- **Local Embeddings**: Sentence-Transformers (no API calls for embeddings)
- **Fast Vector Search**: FAISS-based similarity search
- **Automatic Caching**: Indexed PDFs for instant repeated queries
- **Document-Only Answers**: Extracts from PDF content (no web search)
- **Async Processing**: Non-blocking HTTP-to-MCP communication

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PDF Q&A System Architecture                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│                  │         │                  │         │                  │
│  React Frontend  │  HTTP   │   HTTP Proxy     │ JSON-RPC│   MCP Server     │
│  (Port 3000)     │◄───────►│  (Port 8000)     │◄───────►│  (stdin/stdout)  │
│                  │         │                  │         │                  │
│  • Upload PDFs   │         │  • Translate     │         │  • PDF Tools     │
│  • Chat UI       │         │    HTTP→MCP      │         │  • RAG Tools     │
│  • Markdown      │         │  • Subprocess    │         │  • Vector Store  │
│  • Export PDF    │         │    Management    │         │  • Perplexity    │
│                  │         │                  │         │                  │
└──────────────────┘         └──────────────────┘         └──────────────────┘
        │                             │                             │
        │                             │                             │
        └─────────────────────────────┴─────────────────────────────┘
                                      │
                        ┌─────────────▼─────────────┐
                        │    Shared Core Modules     │
                        ├────────────────────────────┤
                        │  • pdf_processor.py        │
                        │  • rag_system.py           │
                        │  • perplexity_client.py    │
                        │  • config.py               │
                        └────────────────────────────┘
```

### Architecture Explained

#### 1️⃣ **Frontend Layer** (React + Vite)
- Modern chat interface with message history
- File upload with drag-and-drop
- Real-time markdown rendering
- PDF export of conversations
- Responsive design

#### 2️⃣ **HTTP Proxy Layer** (FastAPI)
- Bridges web requests to MCP protocol
- Spawns MCP server as subprocess
- Translates HTTP → JSON-RPC messages
- Manages async stdin/stdout communication
- Maintains session state for web clients

#### 3️⃣ **MCP Server Layer** (Pure MCP)
- True backend processing engine
- Implements MCP tools and resources
- RAG pipeline execution
- Perplexity API integration
- Can be used independently by AI assistants

#### 4️⃣ **Shared Core** (Python Modules)
- `pdf_processor.py`: PDF text extraction & metadata
- `rag_system.py`: Vector embeddings & FAISS search
- `perplexity_client.py`: AI model communication
- `config.py`: Centralized configuration

## 📊 Data Flow Diagram

```
User Question Flow:
─────────────────

┌─────┐
│ 👤  │ User types question in browser
└──┬──┘
   │ HTTP POST /ask/{pdf_id}
   ▼
┌──────────────────────────────────────┐
│  HTTP Proxy (backend/mcp_proxy.py)   │
│  1. Receive HTTP request             │
│  2. Build JSON-RPC message           │
│  3. Send to MCP stdin                │
└──────────────────┬───────────────────┘
                   │ JSON-RPC via pipe
                   ▼
┌──────────────────────────────────────┐
│  MCP Server (src/mcp_server.py)      │
│  1. Parse JSON-RPC request           │
│  2. Call tool: answer_question_rag   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  RAG System (src/rag_system.py)      │
│  1. Embed question                   │
│  2. FAISS vector search (top-k=3)    │
│  3. Retrieve relevant chunks         │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Perplexity AI (src/perplexity_client)│
│  1. Send context + question          │
│  2. Get answer (PDF-only)            │
│  3. Summarize for formatting         │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Response flows back through layers: │
│  Perplexity → RAG → MCP → Proxy     │
└──────────────────┬───────────────────┘
                   │ JSON response
                   ▼
┌──────────────────────────────────────┐
│  React Frontend                       │
│  • Render markdown answer            │
│  • Add to chat history               │
│  • Enable follow-up questions        │
└──────────────────────────────────────┘
```

## 💡 RAG Pipeline Benefits

### Efficiency Comparison

**Without RAG** (Traditional approach):
```
100-page PDF → 250,000 characters → Sent to AI per question
Cost: High | Speed: Slow | Token limit: Often exceeded
```

**With RAG** (Our approach):
```
100-page PDF → Vector embeddings → Top 3 chunks → ~3,000 characters
Cost: 98% reduction | Speed: Fast | Token limit: Never exceeded
```

### Pipeline Steps

1. **📄 Extract**: PDF text → Chunked sections (1000 chars each)
2. **🧮 Embed**: Chunks → Vector embeddings (384 dimensions)
3. **💾 Index**: Store in FAISS vector database
4. **🔍 Retrieve**: Question → Find top-k relevant chunks
5. **🤖 Answer**: Context + Question → Perplexity AI → Answer


## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 18 or higher
- **Perplexity API Key**: [Get one here](https://www.perplexity.ai/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vinayakmore4599/pdf_question_answer.git
   cd pdf_question_answer
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   
   Create/edit `.env` file:
   ```env
   PERPLEXITY_API_KEY=your_api_key_here
   PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions
   ```

4. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

#### Option 1: Web Application (Recommended)

```bash
./start.sh
```

This starts:
- 🔧 MCP Proxy Server on `http://localhost:8000`
- 🌐 React Frontend on `http://localhost:3000`
- 🤖 MCP Server (subprocess, managed by proxy)

**Access**: Open browser to `http://localhost:3000`

**Stop**: `./stop.sh`

#### Option 2: MCP Server Only (for AI Assistants)

For direct integration with Claude Desktop or other MCP clients:

```bash
source venv/bin/activate
python src/mcp_server.py
```

### First Time Usage

1. **Upload PDF**: Click "Upload PDF" or drag & drop
2. **Ask Question**: Type question in chat box
3. **Get Answer**: View formatted markdown response
4. **Follow Up**: Continue conversation with context
5. **Export**: Download chat as PDF anytime

## 📁 Project Structure

```
mcp_pdf/
├── 🎨 frontend/                # React web interface
│   ├── src/
│   │   ├── App.jsx            # Main chat component
│   │   └── App.css            # Styling & markdown
│   ├── package.json
│   └── vite.config.js
│
├── 🔧 backend/                 # HTTP-to-MCP bridge
│   ├── mcp_proxy.py           # FastAPI proxy server ⭐
│   └── api.py                 # [OLD: Legacy REST API]
│
├── 🤖 src/                     # Core MCP server
│   ├── mcp_server.py          # MCP protocol implementation ⭐
│   ├── pdf_processor.py       # PDF extraction
│   ├── rag_system.py          # Vector embeddings & search
│   ├── perplexity_client.py   # AI integration
│   └── config.py              # Settings
│
├── 🛠️ tools/                   # MCP tools
│   ├── pdf_tools.py           # PDF extraction tools
│   └── rag_tools.py           # RAG-based analysis tools
│
├── 📝 output/                  # Generated files
│   ├── logs/                  # Application logs
│   ├── uploads/               # Uploaded PDFs
│   └── cache/                 # FAISS indices
│
├── 🚀 Scripts
│   ├── start.sh               # Start web app
│   ├── stop.sh                # Stop all services
│   └── start_all.sh           # Info about MCP usage
│
├── 📄 Configuration
│   ├── .env                   # API keys (DO NOT COMMIT)
│   ├── requirements.txt       # Python dependencies
│   └── .gitignore
│
└── 📚 Documentation
    ├── README.md              # This file
    ├── RAG_COMPARISON.md      # RAG performance analysis
    └── PROJECT_TECH_INFO.md   # Technical details
```

## 🔧 Configuration

### Python Environment (`requirements.txt`)
```
fastapi==0.109.0           # Web framework
uvicorn==0.27.0            # ASGI server
python-multipart==0.0.6    # File uploads
pydantic==2.5.3            # Data validation
mcp==0.9.0                 # MCP protocol
pdfplumber==0.11.4         # PDF extraction
sentence-transformers==3.3.1 # Embeddings
faiss-cpu==1.9.0           # Vector search
requests==2.31.0           # HTTP client
python-dotenv==1.0.0       # Environment vars
```

### Frontend Dependencies (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.5",        // HTTP client
    "react-markdown": "^10.1.0", // Markdown rendering
    "jspdf": "^4.0.0"         // PDF export
  }
}
```

### Environment Variables (`.env`)
```env
# Perplexity AI Configuration
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions

# RAG Settings (optional overrides)
CHUNK_SIZE=1000              # Text chunk size
CHUNK_OVERLAP=200            # Overlap between chunks
TOP_K=3                      # Number of chunks to retrieve
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Sentence transformer model

# MCP Settings
MCP_SERVER_NAME=pdf-qa-server
```

## 🎯 Usage Examples

### Web Interface

#### Upload & Ask
```
1. Upload "research_paper.pdf"
2. Ask: "What are the main findings?"
3. Get structured markdown answer
4. Follow up: "Can you elaborate on finding #2?"
```

#### Multi-Document Session
```
1. Upload multiple PDFs
2. Switch between them using PDF selector
3. Each maintains separate context
```

#### Export Conversation
```
1. Have conversation with PDF
2. Click "Download Chat as PDF"
3. Get formatted PDF with all Q&A
```

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pdf-qa": {
      "command": "/Users/vinu__more/Projects/mcp_pdf/venv/bin/python",
      "args": ["/Users/vinu__more/Projects/mcp_pdf/src/mcp_server.py"],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-your-key-here"
      }
    }
  }
}
```

Then in Claude Desktop:
```
You: Can you analyze the PDF at /path/to/document.pdf?
Claude: [Uses MCP tools to extract and analyze]
```

### Programmatic Usage (MCP Client)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def analyze_pdf():
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp_server.py"],
        env={"PERPLEXITY_API_KEY": "your-key"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call RAG tool
            result = await session.call_tool(
                "answer_question_rag",
                {
                    "pdf_path": "document.pdf",
                    "question": "What is this about?",
                    "top_k": 3
                }
            )
            print(result.content[0].text)

asyncio.run(analyze_pdf())
```

## 🔍 API Reference

### HTTP Proxy Endpoints

#### `POST /upload`
Upload and process a PDF file.

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "pdf_id": "document.pdf_20260118_143022",
  "filename": "document.pdf",
  "num_pages": 45,
  "num_chunks": 120,
  "message": "PDF processed successfully via MCP in 2.34s"
}
```

#### `POST /ask/{pdf_id}`
Ask a question about an uploaded PDF.

**Request:**
```bash
curl -X POST http://localhost:8000/ask/document.pdf_20260118_143022 \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main conclusions?"}'
```

**Response:**
```json
{
  "pdf_id": "document.pdf_20260118_143022",
  "answers": [{
    "question": "What are the main conclusions?",
    "answer": "## Main Conclusions\n\n1. First finding...",
    "model": "sonar (via MCP)",
    "usage": null
  }],
  "processing_time": 1.23
}
```

#### `POST /ask-multiple/{pdf_id}`
Ask multiple questions at once.

**Request:**
```json
{
  "questions": [
    "What is the methodology?",
    "What are the results?",
    "What are the limitations?"
  ]
}
```

#### `GET /pdfs`
List all uploaded PDFs.

#### `DELETE /pdf/{pdf_id}`
Delete a specific PDF.

### MCP Tools

#### `answer_question_rag`
RAG-based question answering (primary tool).

**Arguments:**
```json
{
  "pdf_path": "path/to/document.pdf",
  "question": "Your question here",
  "top_k": 3
}
```

#### `extract_pdf_text`
Extract raw text from PDF.

#### `analyze_document`
Get document metadata and summary.

#### `get_document_sections`
Extract specific sections/pages.

Full tool list: Use `tools/list` MCP method.

## 🧪 How RAG Works (Technical Deep Dive)

### 1. Document Indexing

```python
# When PDF is uploaded
text = pdf_processor.extract_text()  # "Full document..."

# Split into chunks
chunks = [
  "Introduction: This paper presents...",
  "Methodology: We employed a novel...",
  "Results: The experiment showed...",
  # ... 100+ chunks
]

# Generate embeddings (local, no API)
embeddings = model.encode(chunks)  # [[0.23, -0.45, ...], ...]

# Store in FAISS
faiss_index.add(embeddings)  # Fast similarity search
```

### 2. Question Processing

```python
# When user asks question
question = "What methodology was used?"

# Embed question
q_embedding = model.encode([question])  # [0.12, -0.34, ...]

# Search FAISS (milliseconds!)
distances, indices = faiss_index.search(q_embedding, k=3)

# Retrieved chunks:
# - "Methodology: We employed a novel..."
# - "The experimental setup consisted of..."  
# - "Data collection followed these steps..."
```

### 3. Answer Generation

```python
# Send only relevant context to AI
context = "\n\n".join(retrieved_chunks)  # ~3000 chars

prompt = f"""
Context from PDF: {context}

Question: {question}

Provide answer based ONLY on the context above.
"""

answer = perplexity_api.complete(prompt)
```

**Token Savings:**
- Full document: 250,000 chars ≈ 62,500 tokens
- RAG context: 3,000 chars ≈ 750 tokens
- **Savings: 98.8%** 💰

## 🐛 Troubleshooting

### Backend Issues

**MCP Proxy won't start:**
```bash
# Check logs
cat output/logs/backend.log

# Verify Python environment
source venv/bin/activate
python -c "import mcp; print('MCP OK')"

# Kill existing processes
./stop.sh
```

**"PDF not found" error:**
```bash
# PDFs are in memory cache
# Re-upload PDF after restart
# Or check: ls output/uploads/
```

### Frontend Issues

**Frontend won't connect:**
```bash
# Check if backend is running
curl http://localhost:8000/

# Check CORS settings in mcp_proxy.py
# Ensure port 3000 is in allow_origins
```

**Markdown not rendering:**
```bash
# Ensure react-markdown is installed
cd frontend && npm install react-markdown
```

### MCP Server Issues

**Claude Desktop can't find server:**
```bash
# Verify python path
which python
# Update config with absolute path to venv python

# Test server directly
source venv/bin/activate
python src/mcp_server.py
# Type: {"jsonrpc":"2.0","id":1,"method":"tools/list"}
```

**FAISS errors:**
```bash
# macOS ARM architecture issue
pip uninstall faiss-cpu
pip install faiss-cpu --no-cache-dir

# Or use conda
conda install -c conda-forge faiss-cpu
```

## 🔐 Security Notes

- ✅ `.env` is in `.gitignore` (API keys never committed)
- ✅ File uploads validated (PDF only)
- ✅ CORS restricted to localhost
- ⚠️ In production:
  - Add authentication
  - Use HTTPS
  - Implement rate limiting
  - Store PDFs in S3/cloud storage
  - Use Redis for session management

## 📊 Performance Metrics

**Average Response Times:**
- PDF Upload: 2-5 seconds (depends on size)
- First Question: 1-3 seconds (includes indexing)
- Follow-up Questions: 0.5-1.5 seconds (index cached)

**Resource Usage:**
- RAM: ~500MB (with cached embeddings)
- CPU: Spikes during embedding, idle otherwise
- Storage: ~10MB per 100-page PDF (FAISS index)

**Scalability:**
- Handles PDFs up to 1000 pages
- Concurrent requests: 10-20 (single process)
- For production: Deploy with Gunicorn/multiple workers

## 🛠️ Development

### Running in Development Mode

```bash
# Backend with auto-reload
source venv/bin/activate
uvicorn backend.mcp_proxy:app --reload --port 8000

# Frontend with hot reload
cd frontend && npm run dev
```

### Adding New MCP Tools

1. Create tool in `tools/` directory
2. Register in `src/mcp_server.py`:
   ```python
   @app.list_tools()
   async def list_tools():
       return [
           # ... existing tools
           Tool(
               name="your_new_tool",
               description="What it does",
               inputSchema={...}
           )
       ]
   ```

3. Implement handler:
   ```python
   @app.call_tool()
   async def call_tool(name: str, arguments: Any):
       if name == "your_new_tool":
           return await handle_new_tool(arguments)
   ```

### Running Tests

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python tests/test_integration.py

# MCP protocol tests
python examples/mcp_client_example.py
```

## 📚 Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Perplexity API](https://docs.perplexity.ai/)
- [RAG Explanation](./RAG_COMPARISON.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **MCP Protocol**: Anthropic for Model Context Protocol
- **RAG Architecture**: LangChain community for inspiration
- **Embeddings**: Sentence Transformers team
- **Vector Search**: Meta AI for FAISS

## 📧 Contact

For questions or support:
- GitHub Issues: [Create an issue](https://github.com/vinayakmore4599/pdf_question_answer/issues)
- Repository: [vinayakmore4599/pdf_question_answer](https://github.com/vinayakmore4599/pdf_question_answer)

---

**Made with ❤️ using MCP, RAG, and React**
  "What is the main topic of this document?",
  "Who are the authors?",
  "What are the key findings?"
]
```

**Option 2: Structured format**
```json
{
  "questions": [
    {
      "id": 1,
      "question": "What is the main topic of this document?"
    },
    {
      "id": 2,
      "question": "Who are the authors?"
    }
  ]
}
```

### Output Format

The system generates a JSON file with the following structure:

```json
{
  "metadata": {
    "pdf_file": "document.pdf",
    "num_pages": 10,
    "processed_at": "2026-01-18T10:30:00",
    "model": "llama-3.1-sonar-large-128k-chat",
    "total_questions": 3,
    "rag_enabled": true
  },
  "rag_stats": {
    "indexed": true,
    "num_chunks": 87,
    "total_characters": 87000,
    "avg_chunk_size": 1000,
    "top_k": 3
  },
  "document_info": {
    "title": "Document Title",
    "author": "Author Name",
    "num_pages": 10,
    "file_size": 1024000
  },
  "qa_results": [
    {
      "id": 1,
      "question": "What is the main topic?",
      "answer": "The document discusses...",
      "model": "llama-3.1-sonar-large-128k-chat",
      "usage": {
        "prompt_tokens": 450,
        "completion_tokens": 120,
        "total_tokens": 570
      }
    }
  ]
}
```

## MCP Server

The project includes a full MCP server implementation with RAG support for efficient question answering.

### Running the MCP Server

```bash
python -m src.mcp_server
```

### Available MCP Tools

#### PDF Extraction Tools
1. **extract_pdf_text**: Extract all text from a PDF
2. **extract_pdf_metadata**: Get PDF metadata (title, author, pages, etc.)
3. **search_pdf**: Search for specific text within a PDF

#### Document Analysis Tools (Standard)
4. **answer_question**: Answer a single question about a document
5. **answer_multiple_questions**: Process multiple questions at once
6. **summarize_document**: Generate a document summary
7. **extract_key_points**: Extract key points from a document

#### RAG-Enabled Tools (Efficient - Recommended)
8. **answer_question_rag**: Answer a question using RAG (retrieves only relevant sections)
9. **answer_multiple_questions_rag**: Answer multiple questions efficiently with RAG

**Note**: RAG tools are recommended for PDFs larger than 10 pages as they reduce token usage by ~98%.

### Using MCP Server with RAG

Example MCP client code:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def answer_with_rag(pdf_path: str, question: str):
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use RAG tool for efficient answering
            result = await session.call_tool(
                "answer_question_rag",
                arguments={
                    "pdf_path": pdf_path,
                    "question": question,
                    "top_k": 3,  # Retrieve top 3 relevant chunks
                }
            )
            
            return result
```

See [examples/mcp_client_example.py](examples/mcp_client_example.py) for complete examples.

## Project Structure

```
mcp_pdf/
├── .env                          # Environment variables (API keys)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── RAG_COMPARISON.md            # Detailed RAG performance analysis
├── main.py                       # Main CLI script
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── mcp_server.py            # MCP server implementation (with RAG support)
│   ├── pdf_processor.py         # PDF extraction logic
│   ├── perplexity_client.py    # Perplexity API client
│   └── rag_system.py            # RAG implementation (embeddings + vector store)
├── tools/                        # MCP tools
│   ├── __init__.py
│   ├── pdf_tools.py             # PDF processing and analysis tools
│   └── rag_tools.py             # RAG-enabled MCP tools
├── examples/                     # Example files
│   ├── questions.json           # Sample structured questions
│   ├── questions_simple.json    # Sample simple questions
│   └── mcp_client_example.py   # MCP client usage examples
├── tests/                        # Test files
└── output/                       # Generated output files
    └── cache/                   # Cached vector indexes (for RAG)
```

## Configuration

Configuration is managed through environment variables and `src/config.py`. Key settings:

### API Configuration
- `PERPLEXITY_API_KEY`: Your Perplexity API key (required)
- `PERPLEXITY_API_URL`: Perplexity API endpoint

### RAG Settings
- `use_rag`: Enable/disable RAG (default: True)
- `rag_chunk_size`: Chunk size for indexing (default: 1000 characters)
- `rag_chunk_overlap`: Overlap between chunks (default: 200 characters)
- `rag_top_k`: Number of chunks to retrieve per question (default: 3)
- `embedding_model`: Embedding model to use (default: "all-MiniLM-L6-v2")

### Embedding Model Options
- **all-MiniLM-L6-v2** (default): Fast, lightweight, 384 dimensions
- **all-mpnet-base-v2**: Higher quality, slower, 768 dimensions
- **multi-qa-MiniLM-L6-cos-v1**: Optimized for Q&A tasks

### Other Settings
- `model_name`: AI model for answering (default: llama-3.1-sonar-large-128k-chat)
- `temperature`: Model temperature (default: 0.2)
- `max_tokens`: Maximum response tokens (default: 4000)

**Note**: The system uses RAG by default to minimize token usage and maximize efficiency.

## Examples

See the `examples/` directory for sample question files and usage examples.

## Error Handling

The system provides comprehensive error handling:

- File not found errors for missing PDFs or question files
- API errors with detailed logging
- Invalid JSON format detection
- PDF extraction failures

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
# Format code with black
black src/ tools/ main.py

# Lint with ruff
ruff check src/ tools/ main.py
```

## License

This project is provided as-is for demonstration purposes.

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.
