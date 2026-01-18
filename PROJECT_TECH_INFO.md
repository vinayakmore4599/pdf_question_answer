# Project Technical Documentation: Understanding MCP and RAG

A beginner-friendly guide to understanding how Model Context Protocol (MCP) and Retrieval-Augmented Generation (RAG) work in this PDF Question-Answering system.

---

## Table of Contents

1. [What is MCP (Model Context Protocol)?](#what-is-mcp)
2. [What is RAG (Retrieval-Augmented Generation)?](#what-is-rag)
3. [How This Project Uses Both Technologies](#how-this-project-uses-both)
4. [Complete Flow: From PDF to Answer](#complete-flow)
5. [Code Deep Dive](#code-deep-dive)
6. [Performance Comparison](#performance-comparison)

---

## What is MCP (Model Context Protocol)?

### Simple Explanation

Think of MCP as a **standardized communication protocol** between:
- **Clients** (applications that need AI help)
- **Servers** (tools that provide AI capabilities)

It's like a **universal translator** that lets different programs talk to AI tools in a standard way.

### Real-World Analogy

Imagine you're at a restaurant:
- **You (Client)**: Order food by speaking to the waiter
- **Kitchen (Server)**: Has tools (stove, oven, ingredients) to prepare food
- **Menu (Protocol)**: Standard way to communicate what you want

MCP is the "menu" - it defines how to request things and how to respond.

### MCP in This Project

Our MCP server provides "tools" (like menu items) that clients can use:

```
Client Request: "Extract text from this PDF"
     ↓
MCP Protocol: Standardized format
     ↓
Our Server: Executes the tool
     ↓
Response: Returns extracted text
```

### Key Components

#### 1. **MCP Server** (src/mcp_server.py)

The server offers "tools" to clients:

```python
# This is what the server exposes
Tools Available:
├── extract_pdf_text       # Tool to extract text from PDF
├── extract_pdf_metadata   # Tool to get PDF info
├── search_pdf            # Tool to search within PDF
├── answer_question_rag   # Tool to answer using RAG
└── ... more tools
```

#### 2. **Tool Definition**

Each tool is defined with:
- **Name**: What it's called
- **Description**: What it does
- **Input Schema**: What parameters it needs
- **Handler**: The actual code that runs

Example from our code:

```python
Tool(
    name="answer_question_rag",
    description="Answer a question using RAG (efficient - retrieves only relevant sections)",
    inputSchema={
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "Path to the PDF file",
            },
            "question": {
                "type": "string",
                "description": "The question to answer",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of relevant chunks to retrieve",
                "default": 3,
            },
        },
        "required": ["pdf_path", "question"],
    },
)
```

This says:
- Tool name: `answer_question_rag`
- Needs: PDF path (required), question (required), top_k (optional)
- Does: Answers questions efficiently using RAG

#### 3. **Tool Handler**

When a client calls a tool, this code runs:

```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """This function receives tool calls and routes them."""
    
    if name == "answer_question_rag":
        # Route to RAG tool
        result = rag_tool.answer_question_rag(
            pdf_path=arguments["pdf_path"],
            question=arguments["question"],
            top_k=arguments.get("top_k", 3),
        )
        return [TextContent(type="text", text=str(result))]
```

### MCP Communication Flow

```
┌─────────────┐                           ┌─────────────┐
│   Client    │                           │   Server    │
│ (Your App)  │                           │ (Our Code)  │
└──────┬──────┘                           └──────┬──────┘
       │                                          │
       │  1. "What tools do you have?"          │
       │ ─────────────────────────────────────> │
       │                                          │
       │  2. "I have: extract_pdf_text,         │
       │      answer_question_rag, etc."         │
       │ <───────────────────────────────────── │
       │                                          │
       │  3. "Call answer_question_rag with     │
       │      pdf_path='doc.pdf',                │
       │      question='What is this about?'"    │
       │ ─────────────────────────────────────> │
       │                                          │
       │         [Server processes request]      │
       │                                          │
       │  4. {"answer": "This document is       │
       │      about...", "success": true}        │
       │ <───────────────────────────────────── │
       │                                          │
```

### Why Use MCP?

**Without MCP** (Custom API):
```python
# Every project has different API
response1 = custom_api_1.extract_text(file="doc.pdf")
response2 = other_api.get_text(document="doc.pdf")
response3 = third_api.pdf_extract(path="doc.pdf")
```
Different APIs, different formats - confusing!

**With MCP** (Standardized):
```python
# Same protocol for all MCP servers
response = await session.call_tool("extract_pdf_text", {"pdf_path": "doc.pdf"})
```
Standard way to communicate!

---

## What is RAG (Retrieval-Augmented Generation)?

### Simple Explanation

RAG is like having a **smart research assistant** who:
1. Reads your entire document once
2. Organizes it into a searchable library
3. When you ask a question, quickly finds ONLY the relevant parts
4. Sends only those parts to an AI to answer

Instead of giving the AI 100 pages every time, RAG gives it only the 2-3 paragraphs that matter!

### Real-World Analogy

**Without RAG** (Inefficient):
```
You: "What's the author's name?"
Assistant: *Reads entire 500-page book every time*
          "The author is John Smith"
Time: 30 minutes
```

**With RAG** (Efficient):
```
You: "What's the author's name?"
Assistant: *Searches index, finds author section on page 2*
          *Reads only page 2*
          "The author is John Smith"
Time: 30 seconds
```

### RAG Pipeline: Step by Step

#### Step 1: **Chunking** - Breaking Down the Document

Your 100-page PDF has 250,000 characters. We can't send it all to the AI!

```python
# From src/rag_system.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # Each chunk is 1000 characters
    chunk_overlap=200,      # 200 chars overlap between chunks
)

# Example:
Full PDF: "This is page 1... This is page 2... This is page 3..."
          (250,000 characters)

After chunking:
Chunk 1: "This is page 1 content about introduction..."  (1000 chars)
Chunk 2: "...introduction and background information..." (1000 chars)
Chunk 3: "...background and methodology details..."      (1000 chars)
...
Chunk 250: "...conclusion and final remarks"             (1000 chars)

Total: 250 chunks instead of 1 giant document!
```

**Why overlap?** So sentences at chunk boundaries aren't cut off!

```
Chunk 1: "The study found that climate change..."
         └─ overlap ─┐
Chunk 2: "...climate change affects agriculture significantly."
```

#### Step 2: **Embeddings** - Converting Text to Numbers

Each chunk is converted to a "vector embedding" - a list of numbers that represents its meaning.

```python
# From src/rag_system.py
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",  # Fast, local model
)

# Example transformation:
Text: "The climate is changing rapidly"
      ↓ (Embedding model processes)
Vector: [0.23, -0.45, 0.67, ..., 0.12]  # 384 numbers!

Text: "Global warming accelerates"
      ↓
Vector: [0.21, -0.42, 0.69, ..., 0.15]  # Similar to above!

Text: "The cat sat on the mat"
      ↓
Vector: [-0.89, 0.34, -0.12, ..., 0.78]  # Very different!
```

**Key Point**: Similar meanings = Similar vectors!

#### Step 3: **Vector Store** - Creating a Searchable Database

We use FAISS (Facebook AI Similarity Search) to store and search vectors super fast.

```python
# From src/rag_system.py
vectorstore = FAISS.from_documents(
    documents=chunks,      # Our 250 chunks
    embedding=embeddings   # Embedding model
)

# What happens:
Input: 250 text chunks
       ↓
Process: Convert each to vector embedding
       ↓
Store: Create searchable FAISS index
       ↓
Result: Can find similar chunks in milliseconds!
```

**FAISS Index Visualization**:
```
Document Chunks (as vectors in high-dimensional space):

Chunk 45: "methodology"  →  Vector: [0.2, 0.5, ...]  ╮
Chunk 89: "methods used" →  Vector: [0.3, 0.4, ...]  ├─ Close together!
Chunk 12: "techniques"   →  Vector: [0.2, 0.6, ...]  ╯

Chunk 3:  "conclusion"   →  Vector: [-0.8, 0.1, ...] ╮
Chunk 99: "final results"→  Vector: [-0.7, 0.2, ...] ├─ Close together!
Chunk 150:"summary"      →  Vector: [-0.8, 0.0, ...] ╯
```

#### Step 4: **Retrieval** - Finding Relevant Chunks

When you ask a question, RAG finds the most relevant chunks:

```python
# From src/rag_system.py
def retrieve_relevant_chunks(self, query: str, top_k: int = 3):
    # 1. Convert question to vector
    question_vector = self.embeddings.embed_query(query)
    
    # 2. Find similar vectors in the index
    docs_with_scores = self.vectorstore.similarity_search_with_score(
        query=query,
        k=top_k  # Get top 3 most similar
    )
    
    return docs_with_scores
```

**Example**:

```
Your Question: "What methodology was used in the study?"
               ↓ (Convert to vector)
Question Vector: [0.25, 0.48, ...]

FAISS Search: Find chunks with similar vectors
               ↓
Top 3 Results:
1. Chunk 45: "The methodology section describes..." (similarity: 0.89)
2. Chunk 89: "We used quantitative methods..."     (similarity: 0.84)
3. Chunk 12: "The technique applied was..."        (similarity: 0.78)

Only these 3 chunks (~3000 chars) are sent to AI!
vs sending all 250,000 chars
```

#### Step 5: **Augmentation** - Combining Context with Question

```python
# From src/perplexity_client.py
# Construct prompt with ONLY relevant context
context = rag.get_context_for_question(question)

prompt = f"""
DOCUMENT CONTENT (Relevant Sections Only):
---
{context}  # Only 3000 chars instead of 250,000!
---

QUESTION: {question}

Extract the answer from the document above.
"""
```

#### Step 6: **Generation** - Getting the Answer

```python
# Send to Perplexity API
response = perplexity_api.chat(prompt)

# Response:
"The study used a mixed-methods approach combining quantitative 
surveys with qualitative interviews..."
```

### Complete RAG Example with Real Code

Let's trace a question through our system:

```python
# User asks a question
question = "Who is the author of this document?"
pdf_path = "research_paper.pdf"

# ===== Step 1: Load or Create RAG System =====
from src.rag_system import OptimizedRAGSystem

rag = OptimizedRAGSystem(
    embedding_model="all-MiniLM-L6-v2",
    chunk_size=1000,
    chunk_overlap=200,
    top_k=3
)

# ===== Step 2: Index the Document (First Time) =====
# Extract PDF text
pdf_text = """
Research Paper on Climate Change

Author: Dr. Jane Smith
Affiliation: University of Science

Abstract: This paper examines...
[... 250,000 more characters ...]
Conclusion: We found that...
"""

# Chunk the text
chunks = [
    "Research Paper on Climate Change\nAuthor: Dr. Jane Smith...",
    "...Affiliation: University of Science\nAbstract: This paper...",
    # ... 248 more chunks
]

# Create embeddings for each chunk
embeddings = [
    [0.23, -0.45, 0.67, ...],  # Chunk 1 vector (384 numbers)
    [0.12, -0.33, 0.54, ...],  # Chunk 2 vector
    # ... 248 more vectors
]

# Store in FAISS index
rag.index_document(pdf_text)
# ✓ Document indexed and cached!

# ===== Step 3: Answer Question =====
# Convert question to vector
question = "Who is the author of this document?"
question_vector = [0.19, -0.42, 0.61, ...]

# Find similar chunks
similar_chunks = rag.retrieve_relevant_chunks(question, top_k=3)

# Results:
# Chunk 1: "Research Paper on Climate Change\nAuthor: Dr. Jane Smith..." (score: 0.92)
# Chunk 2: "...Affiliation: University of Science..." (score: 0.78)
# Chunk 18: "...Dr. Jane Smith's previous work..." (score: 0.71)

# Combine relevant chunks
context = """
[Relevant Section 1]
Research Paper on Climate Change
Author: Dr. Jane Smith
Affiliation: University of Science

[Relevant Section 2]
...Affiliation: University of Science
Abstract: This paper examines...

[Relevant Section 3]
...Dr. Jane Smith's previous work in this field...
"""
# Only ~3000 characters instead of 250,000!

# ===== Step 4: Send to AI =====
prompt = f"""
DOCUMENT CONTENT:
{context}

QUESTION: {question}
"""

response = perplexity_api.chat(prompt)

# ===== Step 5: Return Answer =====
answer = "The author of this document is Dr. Jane Smith from the University of Science."
```

### RAG Benefits in Numbers

**Scenario**: 100-page PDF, 1 question

**Without RAG**:
```
PDF Size: 250,000 characters
Tokens sent to API: ~62,500 tokens
Cost: ~$3.13
Time: ~30 seconds
```

**With RAG**:
```
PDF Size: 250,000 characters
Chunks created: 250 chunks
Chunks retrieved: 3 chunks
Characters sent to API: ~3,000 characters
Tokens sent to API: ~750 tokens
Cost: ~$0.04
Time: ~3 seconds

Savings: 98.8% cost reduction, 90% time reduction!
```

---

## How This Project Uses Both Technologies

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP CLIENT                              │
│  (Your application, CLI, or other MCP-compatible tool)      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ MCP Protocol (standardized communication)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   MCP SERVER                                │
│              (src/mcp_server.py)                            │
│                                                             │
│  Available Tools:                                           │
│  ├─ extract_pdf_text                                        │
│  ├─ answer_question (standard)                              │
│  └─ answer_question_rag (efficient!) ◄─── Uses RAG         │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
         ┌──────▼──────┐   ┌─────▼──────┐
         │  PDF Tools  │   │ RAG Tools  │
         │             │   │            │
         │ - Extract   │   │ - Index    │
         │ - Metadata  │   │ - Retrieve │
         │ - Search    │   │ - Cache    │
         └─────────────┘   └──────┬─────┘
                                  │
                         ┌────────▼────────┐
                         │  RAG System     │
                         │                 │
                         │ 1. Chunking     │
                         │ 2. Embeddings   │
                         │ 3. FAISS Index  │
                         │ 4. Retrieval    │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │ Perplexity API  │
                         │ (Answer Gen)    │
                         └─────────────────┘
```

### Integration Points

#### 1. **MCP Exposes RAG as a Tool**

```python
# In src/mcp_server.py
Tool(
    name="answer_question_rag",
    description="Answer using RAG (retrieves only relevant sections)",
    # ... schema ...
)
```

Clients can now call this tool just like any other MCP tool!

#### 2. **RAG Tool Implementation**

```python
# In tools/rag_tools.py
class RAGDocumentAnalysisTool:
    def answer_question_rag(self, pdf_path, question, top_k=3):
        # 1. Get or create RAG system
        rag = self._get_or_create_rag(pdf_path, top_k)
        
        # 2. Retrieve relevant chunks
        context = rag.get_context_for_question(question, top_k)
        
        # 3. Send to Perplexity
        answer = self.client.analyze_document(context, question)
        
        return answer
```

#### 3. **Automatic Caching**

```python
# In src/rag_system.py
def index_document_with_cache(self, text, document_id):
    cache_path = self.cache_dir / document_id
    
    if cache_path.exists():
        # Load from cache (instant!)
        self.load_index(cache_path)
        return False
    
    # Create new index
    self.index_document(text)
    self.save_index(cache_path)
    return True
```

First time: Creates embeddings (10 seconds)  
Next time: Loads from cache (0.1 seconds)

---

## Complete Flow: From PDF to Answer

Let's trace a complete request through the system:

### Scenario
- **Client**: Python script using MCP
- **PDF**: `research_paper.pdf` (100 pages)
- **Question**: "What were the key findings?"

### Step-by-Step Flow

```
TIME: 0s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. CLIENT SENDS REQUEST via MCP Protocol
   
   Client code:
   ```python
   result = await session.call_tool(
       "answer_question_rag",
       arguments={
           "pdf_path": "research_paper.pdf",
           "question": "What were the key findings?",
           "top_k": 3
       }
   )
   ```
   
   ↓ MCP Protocol packages this as standardized message

TIME: 0.01s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. MCP SERVER RECEIVES REQUEST
   
   Server code (src/mcp_server.py):
   ```python
   @app.call_tool()
   async def call_tool(name: str, arguments: Any):
       if name == "answer_question_rag":
           result = rag_tool.answer_question_rag(
               pdf_path=arguments["pdf_path"],
               question=arguments["question"],
               top_k=arguments.get("top_k", 3),
           )
   ```
   
   ↓ Routes to RAG tool

TIME: 0.02s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. RAG TOOL CHECKS CACHE
   
   RAG tool code (tools/rag_tools.py):
   ```python
   def answer_question_rag(self, pdf_path, question, top_k):
       # Check if we have a RAG system for this PDF
       rag = self._get_or_create_rag(pdf_path, top_k)
   ```
   
   Cache check (src/rag_system.py):
   ```python
   cache_path = "output/cache/research_paper"
   
   if cache_path.exists():
       print("✓ Loading from cache!")
       # Already indexed - instant load!
   else:
       print("✗ First time - need to index")
       # Need to process...
   ```

TIME: 0.1s (cached) or 15s (first time)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. IF FIRST TIME: INDEX THE DOCUMENT
   
   Only runs on first access:
   
   ```python
   # A. Extract PDF text
   processor = PDFProcessor("research_paper.pdf")
   text = processor.extract_text()
   # Result: 250,000 characters
   
   # B. Chunk the text
   chunks = text_splitter.split_text(text)
   # Result: 250 chunks of ~1000 chars each
   
   # C. Create embeddings (locally, no API calls!)
   for chunk in chunks:
       embedding = embedding_model.encode(chunk)
       # Each chunk → 384-dimensional vector
   
   # D. Build FAISS index
   vectorstore = FAISS.from_documents(chunks, embeddings)
   
   # E. Save to cache
   vectorstore.save_local("output/cache/research_paper")
   ```
   
   ↓ Now ready for questions!

TIME: +0.5s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. CONVERT QUESTION TO VECTOR
   
   ```python
   question = "What were the key findings?"
   
   # Use same embedding model
   question_vector = embeddings.embed_query(question)
   # Result: [0.34, -0.12, 0.67, ..., 0.23] (384 numbers)
   ```

TIME: +0.1s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. SEARCH VECTOR INDEX (FAISS)
   
   ```python
   # FAISS searches through 250 chunk vectors instantly
   similar_chunks = vectorstore.similarity_search_with_score(
       query=question,
       k=3  # Get top 3 most similar
   )
   
   # Results:
   # Chunk 187: "Key findings section: We found that..." (score: 0.91)
   # Chunk 188: "...findings indicate climate impact..." (score: 0.87)
   # Chunk 12:  "...results show significant changes..." (score: 0.79)
   ```
   
   Magic: Searched 250 chunks in milliseconds!

TIME: +0.2s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. COMBINE RELEVANT CHUNKS
   
   ```python
   context = ""
   for i, chunk in enumerate(similar_chunks, 1):
       context += f"[Relevant Section {i}]\n{chunk.page_content}\n\n"
   
   # Result:
   context = """
   [Relevant Section 1]
   Key findings section: We found that climate change has
   accelerated significantly in the past decade...
   
   [Relevant Section 2]
   ...findings indicate climate impact on agriculture with
   a 15% reduction in crop yields...
   
   [Relevant Section 3]
   ...results show significant changes in temperature
   patterns across all regions studied...
   """
   
   # Only 3,000 characters instead of 250,000!
   ```

TIME: +2s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. SEND TO PERPLEXITY API
   
   ```python
   prompt = f"""
   DOCUMENT CONTENT (Relevant Sections Only):
   ---
   {context}  # 3,000 chars
   ---
   
   QUESTION: What were the key findings?
   
   Extract the answer from the document above. Only use
   information from the document.
   """
   
   response = requests.post(
       "https://api.perplexity.ai/chat/completions",
       json={
           "model": "llama-3.1-sonar-large-128k-chat",
           "messages": [
               {"role": "system", "content": system_message},
               {"role": "user", "content": prompt}
           ],
           "temperature": 0.2,
       },
       headers={"Authorization": f"Bearer {api_key}"}
   )
   ```
   
   Perplexity processes: ~750 tokens instead of ~62,500!

TIME: +0.5s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. PERPLEXITY RETURNS ANSWER
   
   ```python
   api_response = {
       "choices": [{
           "message": {
               "content": "The key findings of the study were:\n\n1. Climate change has accelerated significantly in the past decade\n2. Agricultural impacts show a 15% reduction in crop yields\n3. Temperature patterns have changed significantly across all regions studied\n\nThese findings are based on comprehensive analysis of the data presented in the document."
           }
       }],
       "usage": {
           "prompt_tokens": 750,      # Small!
           "completion_tokens": 120,
           "total_tokens": 870        # vs 62,500 without RAG!
       }
   }
   ```

TIME: +0.1s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. RAG TOOL FORMATS RESPONSE
    
    ```python
    result = {
        "success": True,
        "question": "What were the key findings?",
        "answer": "The key findings of the study were...",
        "model": "llama-3.1-sonar-large-128k-chat",
        "rag_enabled": True,
        "context_length": 3000,
        "chunks_retrieved": 3,
        "usage": {
            "prompt_tokens": 750,
            "completion_tokens": 120,
            "total_tokens": 870
        }
    }
    ```

TIME: +0.01s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. MCP SERVER RETURNS RESULT
    
    ```python
    return [TextContent(type="text", text=str(result))]
    ```
    
    ↓ MCP Protocol packages response

TIME: +0.01s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

12. CLIENT RECEIVES ANSWER
    
    Client code:
    ```python
    result = await session.call_tool(...)
    # Got the answer!
    
    print(result.content[0].text)
    # Displays: {"success": True, "answer": "The key findings..."}
    ```

TOTAL TIME:
- First time: ~18 seconds (includes indexing)
- Subsequent queries: ~3 seconds (uses cache)

vs Without RAG: ~30 seconds EVERY time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### What Happened Behind the Scenes

1. **MCP**: Provided standardized way to call the tool
2. **RAG**: Found only relevant parts of 100-page PDF
3. **Caching**: Made second query 180x faster
4. **Efficiency**: Used 98.6% fewer tokens

---

## Code Deep Dive

### 1. RAG System Implementation

Let's understand the core RAG code:

#### Creating Embeddings

```python
# File: src/rag_system.py

class PDFRAGSystem:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        # Initialize the embedding model
        # This runs LOCALLY on your machine (no API calls!)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},  # Use CPU (or 'cuda' for GPU)
            encode_kwargs={'normalize_embeddings': True}  # Normalize vectors
        )
```

**What does this do?**
- Downloads a pre-trained model (first time only)
- The model knows how to convert text → numbers
- Runs on your computer (free, private, fast)

**Model Size**: ~90MB  
**Speed**: ~1000 chunks per second on CPU

#### Chunking Text

```python
def index_document(self, text: str):
    # Split text into chunks
    self.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # 1000 characters per chunk
        chunk_overlap=200,    # 200 chars overlap
        separators=["\n\n", "\n", ". ", " ", ""]  # Split priority
    )
    
    self.chunks = self.text_splitter.create_documents(
        texts=[text]
    )
```

**How does splitting work?**

```python
# Example input:
text = """
Paragraph 1: Introduction to the study...

Paragraph 2: Methodology section explains...

Paragraph 3: Results show that...
"""

# RecursiveCharacterTextSplitter tries to split by:
# 1. Double newlines (\n\n) - between paragraphs (preferred!)
# 2. Single newlines (\n) - if chunk too big
# 3. Periods (.) - if still too big
# 4. Spaces - last resort

# Result: Clean chunks that preserve paragraph structure
```

#### Creating Vector Index

```python
def index_document(self, text: str):
    # After chunking...
    
    # Create FAISS vector store
    self.vectorstore = FAISS.from_documents(
        documents=self.chunks,    # Our text chunks
        embedding=self.embeddings  # Embedding model
    )
```

**What happens internally:**

```python
# For each chunk:
for chunk in self.chunks:
    # 1. Convert chunk to vector
    vector = embedding_model.encode(chunk.page_content)
    # vector = [0.23, -0.45, ..., 0.12]  (384 numbers)
    
    # 2. Add to FAISS index
    faiss_index.add(vector)

# FAISS builds efficient search structure
# Think of it like a sorted database for vectors
```

#### Retrieving Relevant Chunks

```python
def retrieve_relevant_chunks(self, query: str, top_k: int = 3):
    # Search for similar vectors
    docs_with_scores = self.vectorstore.similarity_search_with_score(
        query=query,
        k=top_k
    )
    
    return docs_with_scores
```

**How similarity search works:**

```python
# 1. Convert query to vector
query = "What were the findings?"
query_vector = [0.34, -0.12, 0.67, ...]  # 384 numbers

# 2. FAISS compares this to all chunk vectors
# Using cosine similarity:
similarity(v1, v2) = dot_product(v1, v2) / (||v1|| * ||v2||)

# Example:
chunk_1_vector = [0.32, -0.10, 0.65, ...]
similarity(query_vector, chunk_1_vector) = 0.91  # Very similar!

chunk_2_vector = [0.35, -0.14, 0.68, ...]
similarity(query_vector, chunk_2_vector) = 0.87  # Also similar!

chunk_3_vector = [-0.80, 0.90, -0.20, ...]
similarity(query_vector, chunk_3_vector) = 0.23  # Not similar

# 3. Return top K most similar
return [chunk_1, chunk_2]  # top_k=2
```

### 2. MCP Server Implementation

#### Defining Tools

```python
# File: src/mcp_server.py

@app.list_tools()
async def list_tools() -> List[Tool]:
    """Tell clients what tools are available."""
    return [
        Tool(
            name="answer_question_rag",
            description="Answer a question using RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "question": {"type": "string"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["pdf_path", "question"],
            },
        ),
        # ... more tools
    ]
```

**What is inputSchema?**

It's like a contract that says:
- "This tool needs these parameters"
- "Some are required, some are optional"
- "Here are the data types"

JSON Schema format - standard for API definitions.

#### Handling Tool Calls

```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute the requested tool."""
    
    if name == "answer_question_rag":
        # 1. Extract arguments
        pdf_path = arguments["pdf_path"]
        question = arguments["question"]
        top_k = arguments.get("top_k", 3)  # Default to 3
        
        # 2. Call RAG tool
        result = rag_tool.answer_question_rag(
            pdf_path=pdf_path,
            question=question,
            top_k=top_k,
        )
        
        # 3. Return as TextContent
        return [TextContent(type="text", text=str(result))]
```

**Flow:**
```
MCP Request → Decode arguments → Route to handler → Execute → Format response → MCP Response
```

### 3. Integration: RAG Tool for MCP

```python
# File: tools/rag_tools.py

class RAGDocumentAnalysisTool:
    def __init__(self):
        self.client = PerplexityClient()
        self.rag_systems = {}  # Cache RAG systems per PDF
    
    def answer_question_rag(self, pdf_path, question, top_k=3):
        # 1. Get or create RAG system for this PDF
        rag = self._get_or_create_rag(pdf_path, top_k)
        
        # 2. Retrieve relevant context
        context = rag.get_context_for_question(question, top_k)
        
        # 3. Get answer from Perplexity
        result = self.client.analyze_document(
            document_text=context,  # Only relevant chunks!
            question=question,
        )
        
        # 4. Add RAG metadata
        result["rag_enabled"] = True
        result["context_length"] = len(context)
        
        return result
```

**Key insight**: This bridges RAG and MCP!
- Input: MCP tool call
- Process: RAG retrieval
- Output: MCP tool response

---

## Performance Comparison

### Memory Usage

**Without RAG:**
```
Load entire PDF into memory: 250 MB
Send to API: 250 MB every query
```

**With RAG:**
```
PDF in memory: 250 MB (initial)
Create embeddings: 96 MB (250 chunks × 384 floats × 4 bytes)
FAISS index: ~100 MB
Cached to disk: Yes
Subsequent queries: Only 3 MB in memory (3 chunks)
```

### API Costs (100 queries)

**Without RAG:**
```
Per query: 62,500 tokens × $0.001/1K = $0.0625
100 queries: $6.25
```

**With RAG:**
```
Per query: 750 tokens × $0.001/1K = $0.00075
100 queries: $0.075

Savings: $6.175 (98.8%)
```

### Time Performance

**First Query:**
```
Without RAG: 30 seconds
With RAG: 18 seconds (includes 15s indexing)
```

**Subsequent Queries:**
```
Without RAG: 30 seconds (same every time!)
With RAG: 3 seconds (uses cached index)

10x faster!
```

### Quality Comparison

**Without RAG:**
- ✅ Has full context
- ❌ May get confused by irrelevant info
- ❌ Slower processing
- ❌ May hit context limits on large PDFs

**With RAG:**
- ✅ Focused on relevant sections
- ✅ Less noise, clearer answers
- ✅ Can handle PDFs of any size
- ⚠️ Might miss info if not in top-k chunks
  - Solution: Increase top_k from 3 to 5 or 7

---

## Summary

### MCP Benefits
- ✅ Standardized protocol for AI tools
- ✅ Easy for clients to discover and use tools
- ✅ Works with any MCP-compatible client
- ✅ Clear tool definitions and schemas

### RAG Benefits
- ✅ 98% reduction in token usage
- ✅ 90% faster query processing
- ✅ Handles PDFs of any size
- ✅ Automatic caching for speed
- ✅ Local embeddings (free, private)

### Combined Power
```
MCP provides the interface
  ↓
RAG provides the efficiency
  ↓
Together: Fast, cheap, standardized PDF Q&A system!
```

### Key Takeaways

1. **MCP** = How clients talk to our tools
2. **RAG** = How we efficiently find answers
3. **Embeddings** = Convert text to searchable vectors
4. **FAISS** = Ultra-fast vector similarity search
5. **Caching** = First query slow, rest fast
6. **Chunking** = Break large documents into searchable pieces

---

## Next Steps for Learning

1. **Try it yourself**: Run the code with a small PDF
2. **Experiment**: Change `top_k` and see how it affects answers
3. **Monitor**: Check the logs to see RAG in action
4. **Optimize**: Try different embedding models
5. **Extend**: Add new MCP tools using the same pattern

---

## Glossary

- **MCP**: Protocol for standardized AI tool communication
- **RAG**: Technique to retrieve relevant info before generating answers
- **Embeddings**: Numerical representations of text meaning
- **Vector**: List of numbers representing text
- **FAISS**: Facebook's fast similarity search library
- **Chunking**: Breaking text into smaller pieces
- **Top-k**: Retrieve k most similar items
- **Cosine Similarity**: Measure of how similar two vectors are
- **Token**: Unit of text for API pricing (~4 characters)
- **Context Window**: Maximum text an AI can process at once

---

**Questions?** Check the code comments or README for more details!
