"""PDF processing module for extracting text and metadata from PDF documents."""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF document processing and text extraction."""
    
    def __init__(self, pdf_path: str | Path):
        """Initialize the PDF processor.
        
        Args:
            pdf_path: Path to the PDF file to process
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self._text_content: Optional[str] = None
        self._metadata: Optional[Dict[str, Any]] = None
    
    def extract_text(self, use_layout: bool = True) -> str:
        """Extract all text from the PDF.
        
        Args:
            use_layout: If True, attempts to preserve layout information
            
        Returns:
            Extracted text content from all pages
        """
        if self._text_content is not None:
            return self._text_content
        
        logger.info(f"Extracting text from {self.pdf_path}")
        text_parts = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    logger.debug(f"Processing page {page_num}/{len(pdf.pages)}")
                    
                    if use_layout:
                        text = page.extract_text(layout=True)
                    else:
                        text = page.extract_text()
                    
                    if text:
                        text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            self._text_content = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(self._text_content)} characters")
            return self._text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the PDF.
        
        Returns:
            Dictionary containing PDF metadata
        """
        if self._metadata is not None:
            return self._metadata
        
        try:
            reader = PdfReader(self.pdf_path)
            metadata = reader.metadata or {}
            
            self._metadata = {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
                "creation_date": metadata.get("/CreationDate", ""),
                "modification_date": metadata.get("/ModDate", ""),
                "num_pages": len(reader.pages),
                "file_size": self.pdf_path.stat().st_size,
                "file_name": self.pdf_path.name,
            }
            
            logger.info(f"Extracted metadata: {self._metadata['num_pages']} pages")
            return self._metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def extract_tables(self, page_numbers: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Extract tables from specified pages.
        
        Args:
            page_numbers: List of page numbers to extract tables from (1-indexed).
                         If None, extracts from all pages.
        
        Returns:
            List of dictionaries containing table data and metadata
        """
        tables_data = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                pages_to_process = (
                    [pdf.pages[i - 1] for i in page_numbers if 0 < i <= len(pdf.pages)]
                    if page_numbers
                    else pdf.pages
                )
                
                for page in pages_to_process:
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            tables_data.append({
                                "page": page.page_number,
                                "table_index": table_idx,
                                "data": table,
                                "rows": len(table),
                                "cols": len(table[0]) if table else 0,
                            })
            
            logger.info(f"Extracted {len(tables_data)} tables from PDF")
            return tables_data
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            raise
    
    def search_text(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text within the PDF.
        
        Args:
            query: Text to search for
            case_sensitive: Whether the search should be case-sensitive
            
        Returns:
            List of dictionaries with page numbers and context
        """
        if not self._text_content:
            self.extract_text()
        
        results = []
        search_query = query if case_sensitive else query.lower()
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    search_text = text if case_sensitive else text.lower()
                    
                    if search_query in search_text:
                        # Find the position and get surrounding context
                        pos = search_text.find(search_query)
                        start = max(0, pos - 100)
                        end = min(len(text), pos + len(query) + 100)
                        context = text[start:end]
                        
                        results.append({
                            "page": page_num,
                            "context": context,
                            "position": pos,
                        })
            
            logger.info(f"Found {len(results)} occurrences of '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching text: {e}")
            raise
    
    def get_page_text(self, page_number: int) -> str:
        """Extract text from a specific page.
        
        Args:
            page_number: Page number to extract (1-indexed)
            
        Returns:
            Text content of the specified page
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise ValueError(f"Invalid page number: {page_number}")
                
                page = pdf.pages[page_number - 1]
                return page.extract_text() or ""
                
        except Exception as e:
            logger.error(f"Error extracting page {page_number}: {e}")
            raise
    
    def chunk_text(self, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
        """Split the PDF text into chunks for processing.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not self._text_content:
            self.extract_text()
        
        chunks = []
        text = self._text_content
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        logger.info(f"Split PDF into {len(chunks)} chunks")
        return chunks
