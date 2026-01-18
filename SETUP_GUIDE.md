# Setup and Installation Guide

This document outlines the steps taken to set up the MCP PDF Question-Answering system on your local machine.

---

## System Requirements

- **Operating System**: macOS
- **Python Version**: Python 3.10 or higher (we installed Python 3.12.1)
- **Perplexity API Key**: Required for document analysis

---

## Installation Steps

### Step 1: Check Existing Python Version

First, we checked what Python version was available on the system:

```bash
python3 --version
```

**Result**: Python 3.9.6 (macOS system default)

**Issue**: The MCP package requires Python 3.10+, so we needed to upgrade.

---

### Step 2: Install Python 3.12

Since Homebrew was not available, we installed Python 3.12 from the official Python website:

1. Downloaded Python 3.12.1 installer from: https://www.python.org/downloads/
2. Ran the `.pkg` installer
3. Verified installation:

```bash
python3.12 --version
```

**Result**: Python 3.12.1

**Note**: macOS keeps both versions:
- `python3` → Points to system Python 3.9.6 (don't modify)
- `python3.12` → Points to your installed Python 3.12.1 (use this)

---

### Step 3: Create Virtual Environment

Created a virtual environment using Python 3.12:

```bash
cd /Users/vinu__more/Projects/mcp_pdf
python3.12 -m venv venv
```

This creates a `venv/` folder containing an isolated Python environment.

---

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

**What this does**:
- Your terminal prompt changes to show `(venv)`
- `python` and `pip` now point to Python 3.12 inside the virtual environment
- Packages install only in this project, not system-wide

**To deactivate later**:
```bash
deactivate
```

---

### Step 5: Upgrade pip

Inside the activated virtual environment:

```bash
pip install --upgrade pip
```

This ensures you have the latest package installer.

---

### Step 6: Install Project Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

**What gets installed**:
- `mcp` - Model Context Protocol server
- `pdfplumber` - PDF text extraction
- `sentence-transformers` - Local embeddings for RAG
- `faiss-cpu` - Vector database for similarity search
- `langchain` - LLM framework
- `requests` - HTTP client for Perplexity API
- `python-dotenv` - Environment variable management
- And more... (see requirements.txt)

---

### Step 7: Verify Installation

Check that everything is installed:

```bash
pip list
```

You should see all packages from requirements.txt listed.

---

## Configuration

### Step 8: Set Up Environment Variables

Your `.env` file should already contain:

```env
PERPLEXITY_API_KEY=your_api_key_here
PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions
```

**Important**: The `.env` file contains your API key, so it's listed in `.gitignore` to prevent accidental commits.

---

## Ready to Run!

Now you can run the application. See below for usage examples.

---

## Running the Application

### Option 1: CLI with RAG (Recommended)

Process a PDF with questions using the efficient RAG approach:

```bash
python main.py 1768627127211.pdf examples/questions.json
```

**With custom output file**:
```bash
python main.py 1768627127211.pdf examples/questions.json -o my_results.json
```

**Retrieve more context (increase accuracy)**:
```bash
python main.py 1768627127211.pdf examples/questions.json --top-k 5
```

**Verbose logging**:
```bash
python main.py 1768627127211.pdf examples/questions.json -v
```

### Option 2: MCP Server

Start the MCP server for programmatic access:

```bash
python -m src.mcp_server
```

Then connect with an MCP client (see examples/mcp_client_example.py).

---

## Troubleshooting

### Virtual Environment Not Activated

**Symptom**: Commands fail or use wrong Python version

**Solution**: 
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**: 
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### API Key Errors

**Symptom**: `ValueError: Perplexity API key is required`

**Solution**: Check your `.env` file contains:
```env
PERPLEXITY_API_KEY=your_actual_api_key_here
```

### Python Version Issues

**Symptom**: MCP server won't start

**Solution**: Verify you're using Python 3.12:
```bash
python --version  # Should show 3.12.x when venv is activated
```

If not, recreate the virtual environment:
```bash
deactivate
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## File Structure After Setup

```
mcp_pdf/
├── venv/                        # ← Virtual environment (created)
├── .env                         # ← API keys (already existed)
├── 1768627127211.pdf           # ← Your PDF file
├── requirements.txt             # ← Dependencies list
├── main.py                      # ← Main CLI script
├── src/                         # ← Source code
│   ├── config.py
│   ├── pdf_processor.py
│   ├── rag_system.py
│   ├── perplexity_client.py
│   └── mcp_server.py
├── tools/                       # ← MCP tools
├── examples/                    # ← Example files
│   ├── questions.json
│   └── mcp_client_example.py
├── output/                      # ← Generated results (created on first run)
│   └── cache/                  # ← RAG indexes cache
└── README.md                    # ← Documentation
```

---

## Quick Reference Commands

**Activate environment**:
```bash
source venv/bin/activate
```

**Run with your PDF**:
```bash
python main.py 1768627127211.pdf examples/questions.json
```

**Check what's installed**:
```bash
pip list
```

**Deactivate environment**:
```bash
deactivate
```

---

## Next Steps

1. ✅ Python 3.12 installed
2. ✅ Virtual environment created
3. ✅ Dependencies installed
4. ✅ Environment configured
5. ⏭️ **Run the application** (see commands above)
6. ⏭️ Check output in `output/` directory
7. ⏭️ Modify questions in `examples/questions.json` for your needs

---

## Why Virtual Environments?

**Benefits**:
- ✅ Isolates project dependencies
- ✅ Prevents conflicts between projects
- ✅ Easy to recreate exact environment
- ✅ Doesn't pollute system Python
- ✅ Can have different package versions per project

**When to use**:
- Always for Python projects!
- Especially when working on multiple projects

---

## Summary

You now have:
- Python 3.12.1 installed
- Virtual environment set up
- All dependencies installed
- Project ready to run

**To start working**:
1. Open terminal
2. Navigate to project: `cd /Users/vinu__more/Projects/mcp_pdf`
3. Activate environment: `source venv/bin/activate`
4. Run commands!
