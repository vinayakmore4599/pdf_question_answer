# Plan: Build MCP-based PDF Question-Answering System

This plan outlines creating a Python project that uses Model Context Protocol architecture to extract answers from PDFs based on user-defined questions in JSON format, leveraging the Perplexity API for intelligent analysis.

## Steps

1. **Set up Python project structure** with directories: `src/` (core logic), `tools/` (MCP tools), `tests/` (testing), and root-level files (requirements.txt, README.md, main.py).

2. **Create requirements.txt** with dependencies: mcp, pdfplumber, langchain, requests, python-dotenv, pytest for the project foundation.

3. **Implement MCP server** in `src/mcp_server.py` with resource definitions (PDF documents) and tool handlers for PDF extraction and document analysis.

4. **Build PDF processor module** in `src/pdf_processor.py` using pdfplumber to extract text/metadata from PDFs and support text searching.

5. **Create Perplexity integration** in `src/perplexity_client.py` to send extracted PDF content + questions to Perplexity API and parse responses.

6. **Build main orchestration script** in `main.py` that: reads JSON with user questions, triggers PDF processing via MCP, calls Perplexity for analysis, and outputs JSON with questions and extracted answers.

## Further Considerations

1. **JSON Input Schema**: Should the user's question JSON file have a specific structure (e.g., `{"questions": [{"id": 1, "query": "..."}]}`), or is a simpler flat format preferred? This affects validation and processing logic.

2. **PDF Handling Strategy**: Should the system support multiple PDFs in one request, or single PDF per execution? Should there be a configurable chunk size for large PDFs sent to Perplexity?

3. **Caching and Persistence**: Should extracted PDF content be cached locally to reduce API calls, or should each run re-extract? Should output JSON maintain any metadata (extraction timestamps, model versions)?

4. **Error Handling**: How should the system handle PDFs with poor text extraction (scanned images), malformed questions, or API failures—skip with warnings or halt processing?
