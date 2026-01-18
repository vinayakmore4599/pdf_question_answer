"""FastAPI backend for PDF Q&A web application."""
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_processor import PDFProcessor
from src.perplexity_client import PerplexityClient
from src.rag_system import OptimizedRAGSystem
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Q&A API",
    description="Extract answers from PDF documents using RAG and AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for processed PDFs (in production, use Redis or database)
pdf_cache = {}

# Request/Response models
class Question(BaseModel):
    question: str

class QuestionList(BaseModel):
    questions: List[str]

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
    answers: List[Answer]
    processing_time: float


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PDF Q&A API",
        "version": "1.0.0"
    }


@app.post("/upload", response_model=ProcessResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    
    Args:
        file: PDF file to process
        
    Returns:
        ProcessResponse with PDF ID and metadata
    """
    start_time = datetime.now()
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Create temporary file to store uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        logger.info(f"Processing uploaded PDF: {file.filename}")
        
        # Extract PDF text
        processor = PDFProcessor(tmp_path)
        text = processor.extract_text()
        metadata = processor.extract_metadata()
        
        logger.info(f"Extracted {len(text)} characters from {metadata['num_pages']} pages")
        
        # Initialize RAG system
        rag_system = OptimizedRAGSystem()
        
        # Generate unique ID for this PDF
        pdf_id = f"{file.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Index the document (text first, then metadata)
        doc_metadata = {
            'pdf_id': pdf_id,
            'filename': file.filename,
            'num_pages': metadata['num_pages']
        }
        rag_system.index_document(text, doc_metadata)
        
        # Store in cache
        pdf_cache[pdf_id] = {
            'filename': file.filename,
            'text': text,
            'metadata': metadata,
            'rag_system': rag_system,
            'uploaded_at': datetime.now().isoformat()
        }
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"PDF processed in {processing_time:.2f} seconds")
        
        return ProcessResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            num_pages=metadata['num_pages'],
            num_chunks=len(rag_system.chunks),
            message=f"PDF processed successfully in {processing_time:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/ask/{pdf_id}", response_model=AnswerResponse)
async def ask_question(pdf_id: str, question: Question):
    """
    Ask a single question about a previously uploaded PDF.
    
    Args:
        pdf_id: ID of the processed PDF
        question: Question to answer
        
    Returns:
        AnswerResponse with the answer
    """
    start_time = datetime.now()
    
    # Check if PDF exists in cache
    if pdf_id not in pdf_cache:
        raise HTTPException(status_code=404, detail="PDF not found. Please upload it first.")
    
    try:
        pdf_data = pdf_cache[pdf_id]
        rag_system = pdf_data['rag_system']
        
        logger.info(f"Processing question for PDF {pdf_id}: {question.question[:50]}...")
        
        # Get relevant context using RAG
        context = rag_system.get_context_for_question(question.question)
        
        logger.info(f"Retrieved {len(context)} chars of relevant context")
        
        # Get answer from Perplexity
        client = PerplexityClient()
        result = client.analyze_document(
            document_text=context,
            question=question.question
        )
        
        logger.info("Summarizing answer for better readability...")
        
        # Summarize the raw answer
        summary_result = client.summarize_answer(
            answer_text=result['answer'],
            question=question.question
        )
        
        # Use summarized answer instead of raw answer
        final_answer = summary_result['summarized_answer']
        
        # Combine usage stats from both API calls
        total_usage = {
            'extraction': result.get('usage', {}),
            'summarization': summary_result.get('usage', {})
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnswerResponse(
            pdf_id=pdf_id,
            answers=[Answer(
                question=result['question'],
                answer=final_answer,
                model=result['model'],
                usage=total_usage
            )],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@app.post("/ask-multiple/{pdf_id}", response_model=AnswerResponse)
async def ask_multiple_questions(pdf_id: str, questions: QuestionList):
    """
    Ask multiple questions about a previously uploaded PDF.
    
    Args:
        pdf_id: ID of the processed PDF
        questions: List of questions to answer
        
    Returns:
        AnswerResponse with all answers
    """
    start_time = datetime.now()
    
    # Check if PDF exists in cache
    if pdf_id not in pdf_cache:
        raise HTTPException(status_code=404, detail="PDF not found. Please upload it first.")
    
    try:
        pdf_data = pdf_cache[pdf_id]
        rag_system = pdf_data['rag_system']
        client = PerplexityClient()
        
        logger.info(f"Processing {len(questions.questions)} questions for PDF {pdf_id}")
        
        answers = []
        for idx, q in enumerate(questions.questions, 1):
            logger.info(f"Processing question {idx}/{len(questions.questions)}")
            
            # Get relevant context using RAG
            context = rag_system.get_context_for_question(q)
            
            # Get answer from Perplexity
            result = client.analyze_document(
                document_text=context,
                question=q
            )
            
            logger.info(f"Summarizing answer {idx}...")
            
            # Summarize the raw answer
            summary_result = client.summarize_answer(
                answer_text=result['answer'],
                question=q
            )
            
            # Use summarized answer
            final_answer = summary_result['summarized_answer']
            
            # Combine usage stats
            total_usage = {
                'extraction': result.get('usage', {}),
                'summarization': summary_result.get('usage', {})
            }
            
            answers.append(Answer(
                question=result['question'],
                answer=final_answer,
                model=result['model'],
                usage=total_usage
            ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Processed {len(answers)} questions in {processing_time:.2f}s")
        
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
    """List all processed PDFs in cache."""
    return {
        "pdfs": [
            {
                "pdf_id": pdf_id,
                "filename": data['filename'],
                "num_pages": data['metadata']['num_pages'],
                "uploaded_at": data['uploaded_at']
            }
            for pdf_id, data in pdf_cache.items()
        ]
    }


@app.delete("/pdf/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete a PDF from cache."""
    if pdf_id not in pdf_cache:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    del pdf_cache[pdf_id]
    return {"message": f"PDF {pdf_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
