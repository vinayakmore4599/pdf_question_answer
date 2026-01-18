"""RAG-enabled MCP tool for efficient document analysis."""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.pdf_processor import PDFProcessor
from src.perplexity_client import PerplexityClient
from src.rag_system import OptimizedRAGSystem
from src.config import settings

logger = logging.getLogger(__name__)


class RAGDocumentAnalysisTool:
    """MCP tool for analyzing documents using RAG for efficiency."""
    
    def __init__(self):
        """Initialize the RAG document analysis tool."""
        self.client = PerplexityClient()
        self.rag_systems: Dict[str, OptimizedRAGSystem] = {}
    
    def _get_or_create_rag(self, pdf_path: str, top_k: int = 3) -> OptimizedRAGSystem:
        """Get existing RAG system or create a new one.
        
        Args:
            pdf_path: Path to the PDF file
            top_k: Number of chunks to retrieve
            
        Returns:
            OptimizedRAGSystem instance
        """
        pdf_path = str(Path(pdf_path).resolve())
        
        if pdf_path not in self.rag_systems:
            logger.info(f"Creating RAG system for {pdf_path}")
            
            # Create RAG system
            rag = OptimizedRAGSystem(
                embedding_model=settings.embedding_model,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
                top_k=top_k,
            )
            
            # Extract and index PDF
            processor = PDFProcessor(pdf_path)
            text = processor.extract_text()
            metadata = processor.extract_metadata()
            
            # Use PDF stem as document ID
            document_id = Path(pdf_path).stem
            
            # Index with caching
            rag.index_document_with_cache(
                text=text,
                document_id=document_id,
                metadata=metadata,
            )
            
            self.rag_systems[pdf_path] = rag
            logger.info(f"RAG system created and cached for {pdf_path}")
        
        return self.rag_systems[pdf_path]
    
    def answer_question_rag(
        self,
        pdf_path: str,
        question: str,
        top_k: int = 3,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer a question using RAG.
        
        Args:
            pdf_path: Path to the PDF file
            question: Question to answer
            top_k: Number of chunks to retrieve
            model: Model to use (optional)
            
        Returns:
            Dictionary with the answer and metadata
        """
        try:
            # Get or create RAG system
            rag = self._get_or_create_rag(pdf_path, top_k)
            
            # Retrieve relevant context
            context = rag.get_context_for_question(question, top_k)
            
            logger.info(f"Retrieved {len(context)} chars of context for question")
            
            # Get answer using only relevant context
            result = self.client.analyze_document(
                document_text=context,
                question=question,
                model=model,
            )
            
            # Add RAG metadata
            result["rag_enabled"] = True
            result["context_length"] = len(context)
            result["chunks_retrieved"] = top_k
            
            return {
                "success": True,
                **result,
            }
            
        except Exception as e:
            logger.error(f"Error answering question with RAG: {e}")
            return {
                "success": False,
                "question": question,
                "error": str(e),
            }
    
    def answer_multiple_questions_rag(
        self,
        pdf_path: str,
        questions: List[str],
        top_k: int = 3,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer multiple questions using RAG.
        
        Args:
            pdf_path: Path to the PDF file
            questions: List of questions to answer
            top_k: Number of chunks to retrieve per question
            model: Model to use (optional)
            
        Returns:
            Dictionary with all answers and metadata
        """
        try:
            # Get or create RAG system
            rag = self._get_or_create_rag(pdf_path, top_k)
            
            results = []
            total_context_length = 0
            
            for idx, question in enumerate(questions, 1):
                logger.info(f"Processing question {idx}/{len(questions)} with RAG")
                
                try:
                    # Retrieve relevant context for this question
                    context = rag.get_context_for_question(question, top_k)
                    total_context_length += len(context)
                    
                    # Get answer
                    result = self.client.analyze_document(
                        document_text=context,
                        question=question,
                        model=model,
                    )
                    
                    result["rag_enabled"] = True
                    result["context_length"] = len(context)
                    result["chunks_retrieved"] = top_k
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error on question {idx}: {e}")
                    results.append({
                        "question": question,
                        "answer": f"Error: {str(e)}",
                        "error": True,
                    })
            
            # Get RAG stats
            rag_stats = rag.get_stats()
            
            return {
                "success": True,
                "results": results,
                "total_questions": len(questions),
                "rag_enabled": True,
                "rag_stats": rag_stats,
                "total_context_length": total_context_length,
                "avg_context_per_question": total_context_length // len(questions) if questions else 0,
            }
            
        except Exception as e:
            logger.error(f"Error answering multiple questions with RAG: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_rag_stats(self, pdf_path: str) -> Dict[str, Any]:
        """Get RAG system statistics for a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with RAG statistics
        """
        pdf_path = str(Path(pdf_path).resolve())
        
        if pdf_path in self.rag_systems:
            return self.rag_systems[pdf_path].get_stats()
        else:
            return {
                "indexed": False,
                "message": "Document not yet indexed"
            }
