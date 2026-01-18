"""Main script for PDF question-answering system.

This script reads a JSON file containing questions, processes a PDF document,
and extracts answers from the PDF content using RAG (Retrieval-Augmented Generation).

RAG APPROACH:
1. Chunks the PDF into smaller segments
2. Creates embeddings and stores in vector database
3. For each question, retrieves only the most relevant chunks
4. Sends only relevant context to Perplexity (saves tokens and time)

IMPORTANT: Answers are extracted ONLY from the PDF content. The system does not
use web search or external knowledge - it analyzes the document text you provide.
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from src.pdf_processor import PDFProcessor
from src.perplexity_client import PerplexityClient
from src.rag_system import OptimizedRAGSystem
from src.config import settings

# Configure logging with file and console handlers
def setup_logging():
    """Setup logging with both file and console output."""
    # Create output/logs directory if it doesn't exist
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"pdf_qa_{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler (for terminal output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler (for log file)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # More detailed logs in file
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return log_file

# Setup logging
log_file_path = setup_logging()
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file_path}")


def load_questions(questions_file: str | Path) -> List[Dict[str, Any]]:
    """Load questions from a JSON file.
    
    Args:
        questions_file: Path to JSON file containing questions
        
    Returns:
        List of question dictionaries
        
    Expected JSON format:
        {
            "questions": [
                {"id": 1, "question": "What is...?"},
                {"id": 2, "question": "How does...?"}
            ]
        }
        
        OR simply:
        
        [
            "What is...?",
            "How does...?"
        ]
    """
    questions_path = Path(questions_file)
    
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_file}")
    
    logger.info(f"Loading questions from {questions_path}")
    
    with open(questions_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, list):
        # Simple list of question strings
        questions = [
            {"id": idx, "question": q}
            for idx, q in enumerate(data, start=1)
        ]
    elif isinstance(data, dict) and "questions" in data:
        # Structured format with questions array
        questions = []
        for idx, item in enumerate(data["questions"], start=1):
            if isinstance(item, str):
                questions.append({"id": idx, "question": item})
            elif isinstance(item, dict):
                questions.append({
                    "id": item.get("id", idx),
                    "question": item.get("question", item.get("query", "")),
                })
    else:
        raise ValueError("Invalid JSON format. Expected list of questions or {'questions': [...]}")
    
    logger.info(f"Loaded {len(questions)} questions")
    return questions


def process_pdf_questions(
    pdf_path: str | Path,
    questions: List[Dict[str, Any]],
    output_file: str | Path | None = None,
    use_rag: bool = True,
) -> Dict[str, Any]:
    """Process a PDF and answer questions about it.
    
    Args:
        pdf_path: Path to the PDF file
        questions: List of question dictionaries
        output_file: Path to save output JSON (optional)
        use_rag: Whether to use RAG for efficient retrieval (recommended)
        
    Returns:
        Dictionary containing results
    """
    # Initialize components
    logger.info(f"Processing PDF: {pdf_path}")
    processor = PDFProcessor(pdf_path)
    client = PerplexityClient()
    
    # Extract PDF content
    logger.info("Extracting PDF text...")
    document_text = processor.extract_text()
    metadata = processor.extract_metadata()
    
    logger.info(f"Extracted {len(document_text)} characters from {metadata['num_pages']} pages")
    
    # Prepare questions list
    question_strings = [q["question"] for q in questions]
    
    results = []
    
    if use_rag:
        logger.info("Using RAG for efficient question answering")
        
        # Initialize RAG system
        rag = OptimizedRAGSystem(
            embedding_model=settings.embedding_model,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            top_k=settings.rag_top_k,
        )
        
        # Index the document (with caching)
        document_id = Path(pdf_path).stem
        indexed = rag.index_document_with_cache(
            text=document_text,
            document_id=document_id,
            metadata=metadata,
        )
        
        if indexed:
            logger.info("Document indexed successfully")
        else:
            logger.info("Using cached index")
        
        # Get RAG statistics
        rag_stats = rag.get_stats()
        logger.info(f"RAG stats: {rag_stats['num_chunks']} chunks, "
                   f"avg size: {rag_stats['avg_chunk_size']} chars")
        
        # Answer each question using RAG
        logger.info(f"Processing {len(question_strings)} questions with RAG...")
        for idx, (original_q, question) in enumerate(zip(questions, question_strings), 1):
            logger.info(f"Question {idx}/{len(question_strings)}: {question[:80]}...")
            
            try:
                # Retrieve relevant context
                context = rag.get_context_for_question(question)
                
                logger.info(f"Retrieved {len(context)} chars of relevant context "
                           f"(vs {len(document_text)} full document)")
                
                # Get answer using only relevant context
                result = client.analyze_document(
                    document_text=context,  # Only send relevant chunks!
                    question=question,
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing question {idx}: {e}")
                results.append({
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "model": settings.model_name,
                    "error": True,
                })
    else:
        # Original approach: send full document (not recommended for large PDFs)
        logger.info("Using full document approach (RAG disabled)")
        logger.warning("This may consume many tokens for large documents!")
        
        results = client.batch_analyze(
            document_text=document_text,
            questions=question_strings,
        )
    
    # Build output structure
    output = {
        "metadata": {
            "pdf_file": str(Path(pdf_path).name),
            "pdf_path": str(pdf_path),
            "num_pages": metadata["num_pages"],
            "processed_at": datetime.now().isoformat(),
            "model": settings.model_name,
            "total_questions": len(questions),
            "rag_enabled": use_rag,
        },
        "document_info": {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "num_pages": metadata["num_pages"],
            "file_size": metadata["file_size"],
        },
        "qa_results": []
    }
    
    # Add RAG stats if used
    if use_rag:
        output["rag_stats"] = rag.get_stats()
    
    # Combine questions with answers
    for original_q, result in zip(questions, results):
        qa_item = {
            "id": original_q["id"],
            "question": result["question"],
            "answer": result["answer"],
            "model": result.get("model", ""),
        }
        
        # Include error information if present
        if result.get("error"):
            qa_item["error"] = True
            
        # Include token usage if available
        if "usage" in result:
            qa_item["usage"] = result["usage"]
        
        output["qa_results"].append(qa_item)
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving results to {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if settings.pretty_print_json:
                json.dump(output, f, indent=2, ensure_ascii=False)
            else:
                json.dump(output, f, ensure_ascii=False)
        
        logger.info(f"Results saved successfully")
    
    return output


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract answers from PDF documents using AI (answers based on PDF content only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a PDF with questions using RAG (efficient, recommended)
  python main.py document.pdf questions.json
  
  # Specify output file
  python main.py document.pdf questions.json -o results.json
  
  # Retrieve more context chunks per question
  python main.py document.pdf questions.json --top-k 5
  
  # Disable RAG (sends full document - uses more tokens)
  python main.py document.pdf questions.json --no-rag
  
  # Use specific model
  python main.py document.pdf questions.json --model llama-3.1-sonar-large-128k-chat

Note: RAG is enabled by default - it retrieves only relevant sections,
saving tokens and processing time while maintaining accuracy.
        """
    )
    
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file to process"
    )
    
    parser.add_argument(
        "questions_file",
        type=str,
        help="Path to JSON file containing questions"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to save output JSON file (default: output/results_TIMESTAMP.json)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help=f"Model to use for analysis (default: {settings.model_name})"
    )
    
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG and send full document (uses more tokens)"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        help=f"Number of relevant chunks to retrieve with RAG (default: {settings.rag_top_k})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Override model if specified
    if args.model:
        settings.model_name = args.model
    
    # Override RAG settings if specified
    if args.top_k:
        settings.rag_top_k = args.top_k
    
    # Generate output filename if not specified
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = settings.output_dir / f"results_{timestamp}.json"
    
    try:
        # Load questions
        questions = load_questions(args.questions_file)
        
        # Process PDF and get answers
        results = process_pdf_questions(
            pdf_path=args.pdf_file,
            questions=questions,
            output_file=args.output,
            use_rag=not args.no_rag,  # RAG enabled by default
        )
        
        # Print summary
        print("\n" + "="*60)
        print("Processing Complete!")
        print("="*60)
        print(f"PDF: {results['metadata']['pdf_file']}")
        print(f"Pages: {results['metadata']['num_pages']}")
        print(f"Questions answered: {results['metadata']['total_questions']}")
        print(f"RAG enabled: {results['metadata']['rag_enabled']}")
        if results['metadata']['rag_enabled'] and 'rag_stats' in results:
            rag = results['rag_stats']
            print(f"Document chunks: {rag['num_chunks']}")
            print(f"Chunks per query: {rag['top_k']}")
        print(f"Results saved to: {args.output}")
        print(f"Log file: {log_file_path}")
        print("="*60 + "\n")
        
        logger.info(f"Processing completed successfully. Results saved to {args.output}")
        
        # Print a sample of results
        if results['qa_results']:
            print("Sample Results:")
            print("-" * 60)
            for qa in results['qa_results'][:3]:  # Show first 3
                print(f"\nQ{qa['id']}: {qa['question']}")
                print(f"A: {qa['answer'][:200]}{'...' if len(qa['answer']) > 200 else ''}")
            
            if len(results['qa_results']) > 3:
                print(f"\n... and {len(results['qa_results']) - 3} more results")
            print("-" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
