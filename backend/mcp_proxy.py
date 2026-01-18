"""HTTP-to-MCP Proxy Server
Bridges HTTP requests from web frontend to MCP server backend.
"""
import logging
import asyncio
import json
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Q&A Proxy",
    description="HTTP-to-MCP bridge for PDF Q&A system",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPClient:
    """Client for communicating with MCP server via stdin/stdout."""
    
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.lock = asyncio.Lock()
        self.initialized = False
        
    async def start(self):
        """Start the MCP server process."""
        mcp_server_path = Path(__file__).parent.parent / "src" / "mcp_server.py"
        venv_python = Path(__file__).parent.parent / "venv" / "bin" / "python"
        project_root = Path(__file__).parent.parent
        
        logger.info(f"Starting MCP server: {mcp_server_path}")
        logger.info(f"Project root: {project_root}")
        
        # Pass environment variables to subprocess
        env = os.environ.copy()
        # Add project root to PYTHONPATH so imports work
        env['PYTHONPATH'] = str(project_root)
        
        self.process = await asyncio.create_subprocess_exec(
            str(venv_python),
            str(mcp_server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,  # Pass environment variables with PYTHONPATH
            cwd=str(project_root)  # Set working directory to project root
        )
        
        logger.info("MCP server process started")
        
        # Wait a bit and check if process is alive
        await asyncio.sleep(0.5)
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"MCP server failed to start: {error_msg}")
            raise RuntimeError(f"MCP server crashed on startup: {error_msg}")
        
        # Initialize MCP session
        await self._initialize_session()
        
        logger.info("MCP server ready")
    
    async def _initialize_session(self):
        """Send initialization request to MCP server."""
        async with self.lock:
            self.request_id += 1
            init_request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-proxy",
                        "version": "2.0.0"
                    }
                }
            }
            
            init_json = json.dumps(init_request) + "\n"
            logger.info("Sending MCP initialization...")
            self.process.stdin.write(init_json.encode())
            await self.process.stdin.drain()
            
            # Read initialization response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=10.0
            )
            
            if response_line:
                response = json.loads(response_line.decode())
                logger.info(f"MCP initialization response: {json.dumps(response)[:200]}")
                
                if "error" in response:
                    raise RuntimeError(f"MCP initialization failed: {response['error']}")
                
                self.initialized = True
                logger.info("MCP session initialized successfully")
            else:
                raise RuntimeError("No response from MCP server during initialization")
        
    async def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP server stopped")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return the result."""
        async with self.lock:
            # Check if process is still alive
            if self.process.returncode is not None:
                stderr = await self.process.stderr.read()
                error_msg = stderr.decode() if stderr else "Process terminated"
                logger.error(f"MCP server died: {error_msg}")
                raise RuntimeError(f"MCP server not running: {error_msg}")
            
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments  # Arguments should be at this level
                }
            }
            
            # Send request
            request_json = json.dumps(request) + "\n"
            logger.info(f"Sending to MCP: {tool_name}")
            logger.info(f"Full MCP request: {request_json.strip()}")
            
            try:
                self.process.stdin.write(request_json.encode())
                await self.process.stdin.drain()
            except (ConnectionResetError, BrokenPipeError) as e:
                stderr = await self.process.stderr.read()
                error_msg = stderr.decode() if stderr else str(e)
                logger.error(f"Failed to send to MCP: {error_msg}")
                raise RuntimeError(f"Connection to MCP server lost: {error_msg}")
            
            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=30.0
                )
                if not response_line:
                    stderr = await self.process.stderr.read()
                    error_msg = stderr.decode() if stderr else "No response"
                    raise RuntimeError(f"MCP server returned empty response: {error_msg}")
                    
                response = json.loads(response_line.decode())
            except asyncio.TimeoutError:
                logger.error("MCP server response timeout")
                raise RuntimeError("MCP server took too long to respond")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from MCP: {response_line}")
                raise RuntimeError(f"Invalid response from MCP server: {e}")
            
            logger.info(f"Full MCP response: {json.dumps(response)[:500]}")
            logger.info(f"Received from MCP: {response.get('result', {}).get('content', [{}])[0].get('text', '')[:100]}")
            
            if "error" in response:
                raise HTTPException(status_code=500, detail=response["error"]["message"])
            
            return response["result"]


# Global MCP client
mcp_client = MCPClient()

# In-memory PDF tracking
pdf_uploads: Dict[str, str] = {}  # Maps pdf_id to file path


# Request/Response models
class Question(BaseModel):
    question: str

class QuestionList(BaseModel):
    questions: list[str]

class Answer(BaseModel):
    question: str
    answer: str
    model: str
    usage: Optional[dict] = None

class ProcessResponse(BaseModel):
    pdf_id: str
    filename: str
    num_pages: int
    num_chunks: int
    message: str

class AnswerResponse(BaseModel):
    pdf_id: str
    answers: list[Answer]
    processing_time: float


@app.on_event("startup")
async def startup_event():
    """Start MCP server on app startup."""
    await mcp_client.start()
    # Wait a bit for MCP server to initialize
    await asyncio.sleep(2)


@app.on_event("shutdown")
async def shutdown_event():
    """Stop MCP server on app shutdown."""
    await mcp_client.stop()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PDF Q&A Proxy (MCP Bridge)",
        "version": "2.0.0"
    }


@app.post("/upload", response_model=ProcessResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file via MCP."""
    start_time = datetime.now()
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file to temp location
        temp_dir = Path(__file__).parent.parent / "output" / "uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = temp_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"Processing PDF via MCP: {file.filename}")
        
        # Call MCP tool to process PDF
        result = await mcp_client.call_tool(
            "answer_question_rag",  # We'll use this to test if PDF loads
            {
                "pdf_path": str(pdf_path),
                "question": "What is this document about?"  # Initial test question
            }
        )
        
        # Generate PDF ID
        pdf_id = f"{file.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pdf_uploads[pdf_id] = str(pdf_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Extract basic info from result
        return ProcessResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            num_pages=1,  # MCP doesn't return this easily, could enhance
            num_chunks=1,  # Same here
            message=f"PDF processed successfully via MCP in {processing_time:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        if 'pdf_path' in locals() and Path(pdf_path).exists():
            Path(pdf_path).unlink()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/ask/{pdf_id}", response_model=AnswerResponse)
async def ask_question(pdf_id: str, question: Question):
    """Ask a question about a PDF via MCP."""
    start_time = datetime.now()
    
    if pdf_id not in pdf_uploads:
        raise HTTPException(status_code=404, detail="PDF not found. Please upload it first.")
    
    try:
        pdf_path = pdf_uploads[pdf_id]
        
        logger.info(f"Asking question via MCP: {question.question[:50]}...")
        
        # Call MCP tool
        result = await mcp_client.call_tool(
            "answer_question_rag",
            {
                "pdf_path": pdf_path,
                "question": question.question,
                "top_k": 3
            }
        )
        
        # Extract answer from MCP response
        answer_text = result.get("content", [{}])[0].get("text", "No answer received")
        
        # Parse the answer if it's a JSON string
        try:
            import ast
            # The MCP server returns str(dict), so we need to parse it
            answer_data = ast.literal_eval(answer_text)
            
            # Extract the actual answer
            if isinstance(answer_data, dict) and 'answer' in answer_data:
                formatted_answer = answer_data['answer']
            else:
                formatted_answer = answer_text
        except (ValueError, SyntaxError):
            # If parsing fails, use raw text
            formatted_answer = answer_text
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnswerResponse(
            pdf_id=pdf_id,
            answers=[Answer(
                question=question.question,
                answer=formatted_answer,
                model="perplexity-sonar",  # Add model field
                usage=None
            )],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@app.post("/ask-multiple/{pdf_id}", response_model=AnswerResponse)
async def ask_multiple_questions(pdf_id: str, questions: QuestionList):
    """Ask multiple questions about a PDF via MCP."""
    start_time = datetime.now()
    
    if pdf_id not in pdf_uploads:
        raise HTTPException(status_code=404, detail="PDF not found. Please upload it first.")
    
    try:
        pdf_path = pdf_uploads[pdf_id]
        
        logger.info(f"Processing {len(questions.questions)} questions via MCP")
        
        answers = []
        for q in questions.questions:
            # Call MCP tool for each question
            result = await mcp_client.call_tool(
                "answer_question_rag",
                {
                    "pdf_path": pdf_path,
                    "question": q,
                    "top_k": 3
                }
            )
            
            answer_text = result.get("content", [{}])[0].get("text", "No answer received")
            
            # Parse the answer if it's a JSON string
            try:
                import ast
                answer_data = ast.literal_eval(answer_text)
                
                if isinstance(answer_data, dict) and 'answer' in answer_data:
                    formatted_answer = answer_data['answer']
                else:
                    formatted_answer = answer_text
            except (ValueError, SyntaxError):
                formatted_answer = answer_text
            
            answers.append(Answer(
                question=q,
                answer=formatted_answer,
                model="perplexity-sonar",  # Add model field
                usage=None
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnswerResponse(
            pdf_id=pdf_id,
            answers=answers,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error answering questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error answering questions: {str(e)}")


@app.get("/pdfs")
async def list_pdfs():
    """List all uploaded PDFs."""
    return {
        "pdfs": [
            {
                "pdf_id": pdf_id,
                "filename": Path(path).name,
                "path": path
            }
            for pdf_id, path in pdf_uploads.items()
        ]
    }


@app.delete("/pdf/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete a PDF."""
    if pdf_id not in pdf_uploads:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    pdf_path = Path(pdf_uploads[pdf_id])
    if pdf_path.exists():
        pdf_path.unlink()
    
    del pdf_uploads[pdf_id]
    return {"message": f"PDF {pdf_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
