# MCP PDF Question-Answering System

A Python-based Model Context Protocol (MCP) server for extracting information from PDF documents using RAG (Retrieval-Augmented Generation). The system efficiently answers questions by retrieving only relevant sections from PDFs, significantly reducing token usage and processing time.

## Features

- **RAG-Based Architecture**: Uses embeddings and vector search to retrieve only relevant content
- **Efficient Processing**: Reduces token consumption by 70-90% compared to sending full documents
- **Local Embeddings**: Uses Sentence-Transformers (runs locally, no API calls for embeddings)
- **Fast Vector Search**: FAISS-based similarity search for instant retrieval
- **Automatic Caching**: Indexes are cached to speed up repeated queries
- **Document-Based Q&A**: Answers extracted ONLY from PDF content (no web search)
- **MCP Architecture**: Built on Model Context Protocol for standardized AI interactions
- **Batch Processing**: Process multiple questions efficiently
- **Flexible Input**: Support for various JSON question formats
- **Rich Output**: Structured JSON with answers, metadata, and token usage statistics

## How It Works

### RAG Pipeline:
1. **Extract**: PDF text is extracted and split into chunks
2. **Embed**: Each chunk is converted to a vector embedding (locally, using Sentence-Transformers)
3. **Index**: Embeddings are stored in a FAISS vector database
4. **Retrieve**: For each question, find the top-k most relevant chunks
5. **Answer**: Send only relevant chunks to Perplexity AI (saves 70-90% tokens!)

**Example**: For a 100-page PDF (~250,000 characters):
- Without RAG: Sends all 250,000 chars per question
- With RAG: Sends only ~3,000 chars per question (top 3 chunks)
- **Result**: 98% reduction in tokens!

## Installation

### Prerequisites

- Python 3.9 or higher
- Perplexity API key

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/vinu__more/Projects/mcp_pdf
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   
   The `.env` file should already exist with your Perplexity API credentials:
   ```
   PERPLEXITY_API_KEY=your_api_key_here
   PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions
   ```

## Usage

### Basic Usage

Process a PDF document with questions using RAG (efficient, default):

```bash
python main.py path/to/document.pdf path/to/questions.json
```

### Advanced Usage

```bash
# Specify output file
python main.py document.pdf questions.json -o results.json

# Retrieve more chunks per question (default is 3)
python main.py document.pdf questions.json --top-k 5

# Disable RAG (sends full document - not recommended for large PDFs)
python main.py document.pdf questions.json --no-rag

# Use a specific model
python main.py document.pdf questions.json --model llama-3.1-sonar-large-128k-online

# Enable verbose logging
python main.py document.pdf questions.json -v
```

### Question JSON Format

The system supports multiple JSON formats for questions:

**Option 1: Simple list**
```json
[
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
