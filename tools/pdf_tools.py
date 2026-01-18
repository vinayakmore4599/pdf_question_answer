"""MCP tools for PDF extraction and document analysis."""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.pdf_processor import PDFProcessor
from src.perplexity_client import PerplexityClient
from src.rag_system import OptimizedRAGSystem
from src.config import settings

logger = logging.getLogger(__name__)


class PDFExtractionTool:
    """MCP tool for extracting content from PDF documents."""
    
    @staticmethod
    def extract_pdf_text(pdf_path: str, use_layout: bool = True) -> Dict[str, Any]:
        """Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            use_layout: Whether to preserve layout information
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            processor = PDFProcessor(pdf_path)
            text = processor.extract_text(use_layout=use_layout)
            metadata = processor.extract_metadata()
            
            return {
                "success": True,
                "text": text,
                "metadata": metadata,
                "char_count": len(text),
            }
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def extract_pdf_metadata(pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            processor = PDFProcessor(pdf_path)
            metadata = processor.extract_metadata()
            
            return {
                "success": True,
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def search_pdf(pdf_path: str, query: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for text within a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            query: Text to search for
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            Dictionary with search results
        """
        try:
            processor = PDFProcessor(pdf_path)
            results = processor.search_text(query, case_sensitive)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            logger.error(f"Error searching PDF: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class DocumentAnalysisTool:
    """MCP tool for analyzing documents using Perplexity AI."""
    
    def __init__(self):
        """Initialize the document analysis tool."""
        self.client = PerplexityClient()
    
    def answer_question(
        self,
        document_text: str,
        question: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer a question about a document.
        
        Args:
            document_text: The document text
            question: Question to answer
            model: Model to use (optional)
            
        Returns:
            Dictionary with the answer
        """
        try:
            result = self.client.analyze_document(
                document_text=document_text,
                question=question,
                model=model,
            )
            
            return {
                "success": True,
                **result,
            }
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "success": False,
                "question": question,
                "error": str(e),
            }
    
    def answer_multiple_questions(
        self,
        document_text: str,
        questions: List[str],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answer multiple questions about a document.
        
        Args:
            document_text: The document text
            questions: List of questions to answer
            model: Model to use (optional)
            
        Returns:
            Dictionary with all answers
        """
        try:
            results = self.client.batch_analyze(
                document_text=document_text,
                questions=questions,
                model=model,
            )
            
            return {
                "success": True,
                "results": results,
                "total_questions": len(questions),
            }
        except Exception as e:
            logger.error(f"Error answering multiple questions: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def summarize_document(
        self,
        document_text: str,
        max_length: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Summarize a document.
        
        Args:
            document_text: The document text
            max_length: Maximum summary length in words
            model: Model to use (optional)
            
        Returns:
            Dictionary with the summary
        """
        try:
            summary = self.client.summarize_document(
                document_text=document_text,
                max_length=max_length,
                model=model,
            )
            
            return {
                "success": True,
                "summary": summary,
            }
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def extract_key_points(
        self,
        document_text: str,
        num_points: int = 5,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract key points from a document.
        
        Args:
            document_text: The document text
            num_points: Number of key points to extract
            model: Model to use (optional)
            
        Returns:
            Dictionary with key points
        """
        try:
            key_points = self.client.extract_key_points(
                document_text=document_text,
                num_points=num_points,
                model=model,
            )
            
            return {
                "success": True,
                "key_points": key_points,
                "count": len(key_points),
            }
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return {
                "success": False,
                "error": str(e),
            }
