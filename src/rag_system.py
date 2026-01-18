"""RAG (Retrieval-Augmented Generation) module for efficient PDF question answering.

This module implements a RAG pipeline that:
1. Chunks PDF text into smaller segments
2. Creates embeddings for each chunk
3. Stores embeddings in a FAISS vector store
4. Retrieves only relevant chunks for each question
5. Sends only relevant context to Perplexity (saves tokens and time)
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.config import settings

logger = logging.getLogger(__name__)


class PDFRAGSystem:
    """RAG system for efficient PDF question answering."""
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 3,
    ):
        """Initialize the RAG system.
        
        Args:
            embedding_model: HuggingFace embedding model name
                - "all-MiniLM-L6-v2": Fast, lightweight (default)
                - "all-mpnet-base-v2": Higher quality but slower
                - "multi-qa-MiniLM-L6-cos-v1": Optimized for Q&A
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks for context preservation
            top_k: Number of relevant chunks to retrieve per question
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        logger.info(f"Initializing RAG system with {embedding_model}")
        
        # Initialize embeddings model (runs locally, no API calls)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vectorstore: Optional[FAISS] = None
        self.chunks: List[Document] = []
        
        logger.info("RAG system initialized successfully")
    
    def index_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Index a document by creating chunks and embeddings.
        
        Args:
            text: Full text of the document
            metadata: Optional metadata to attach to chunks
        """
        logger.info(f"Indexing document ({len(text)} characters)")
        
        # Split text into chunks
        self.chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata or {}]
        )
        
        logger.info(f"Created {len(self.chunks)} chunks")
        
        # Create vector store from chunks
        logger.info("Creating embeddings and vector store...")
        self.vectorstore = FAISS.from_documents(
            documents=self.chunks,
            embedding=self.embeddings
        )
        
        logger.info("Document indexed successfully")
    
    def retrieve_relevant_chunks(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve the most relevant chunks for a query.
        
        Args:
            query: The question or query
            top_k: Number of chunks to retrieve (uses default if not specified)
            
        Returns:
            List of relevant chunks with content and metadata
        """
        if not self.vectorstore:
            raise ValueError("No document indexed. Call index_document() first.")
        
        k = top_k or self.top_k
        
        logger.info(f"Retrieving top {k} chunks for query: {query[:100]}...")
        
        # Retrieve similar documents
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k
        )
        
        results = []
        for doc, score in docs_with_scores:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score),
            })
        
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
    
    def get_context_for_question(self, question: str, top_k: Optional[int] = None) -> str:
        """Get relevant context for a question.
        
        Args:
            question: The question to answer
            top_k: Number of chunks to retrieve
            
        Returns:
            Combined context from relevant chunks
        """
        chunks = self.retrieve_relevant_chunks(question, top_k)
        
        # Combine chunks into context
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Relevant Section {idx}]\n{chunk['content']}")
        
        context = "\n\n".join(context_parts)
        
        logger.info(f"Generated context of {len(context)} characters from {len(chunks)} chunks")
        return context
    
    def save_index(self, path: str | Path) -> None:
        """Save the vector store index to disk.
        
        Args:
            path: Directory path to save the index
        """
        if not self.vectorstore:
            raise ValueError("No vector store to save")
        
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        self.vectorstore.save_local(str(path))
        
        # Save chunks separately
        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        
        logger.info(f"Index saved to {path}")
    
    def load_index(self, path: str | Path) -> None:
        """Load a previously saved vector store index.
        
        Args:
            path: Directory path where index is saved
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Index not found at {path}")
        
        # Load FAISS index
        self.vectorstore = FAISS.load_local(
            str(path),
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Load chunks
        with open(path / "chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)
        
        logger.info(f"Index loaded from {path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed document.
        
        Returns:
            Dictionary with indexing statistics
        """
        if not self.chunks:
            return {"indexed": False}
        
        total_chars = sum(len(chunk.page_content) for chunk in self.chunks)
        avg_chunk_size = total_chars / len(self.chunks) if self.chunks else 0
        
        return {
            "indexed": True,
            "num_chunks": len(self.chunks),
            "total_characters": total_chars,
            "avg_chunk_size": int(avg_chunk_size),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
        }


class OptimizedRAGSystem(PDFRAGSystem):
    """Optimized RAG system with caching and performance improvements."""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        **kwargs
    ):
        """Initialize optimized RAG system.
        
        Args:
            cache_dir: Directory for caching indexes
            **kwargs: Arguments passed to PDFRAGSystem
        """
        super().__init__(**kwargs)
        self.cache_dir = cache_dir or (settings.output_dir / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def index_document_with_cache(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        force_reindex: bool = False,
    ) -> bool:
        """Index a document with automatic caching.
        
        Args:
            text: Full text of the document
            document_id: Unique identifier for the document
            metadata: Optional metadata
            force_reindex: If True, reindex even if cache exists
            
        Returns:
            True if document was indexed, False if loaded from cache
        """
        cache_path = self.cache_dir / document_id
        
        if not force_reindex and cache_path.exists():
            logger.info(f"Loading cached index for {document_id}")
            self.load_index(cache_path)
            return False
        
        logger.info(f"Indexing document {document_id}")
        self.index_document(text, metadata)
        self.save_index(cache_path)
        return True
