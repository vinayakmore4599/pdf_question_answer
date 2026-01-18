"""MCP Server implementation for PDF question-answering system with RAG support."""
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from tools.pdf_tools import PDFExtractionTool, DocumentAnalysisTool
from tools.rag_tools import RAGDocumentAnalysisTool
from src.pdf_processor import PDFProcessor
from src.rag_system import OptimizedRAGSystem
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server(settings.mcp_server_name)

# Initialize tools
pdf_tool = PDFExtractionTool()
analysis_tool = DocumentAnalysisTool()
rag_tool = RAGDocumentAnalysisTool()

# Store loaded PDFs and RAG systems
loaded_pdfs: Dict[str, PDFProcessor] = {}
rag_systems: Dict[str, OptimizedRAGSystem] = {}


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available PDF resources.
    
    Returns:
        List of PDF resources available for querying
    """
    resources = []
    
    # Scan for PDF files in the current directory and common locations
    search_paths = [
        Path.cwd(),
        Path.cwd() / "examples",
        Path.cwd() / "data",
        Path.cwd() / "pdfs",
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            for pdf_file in search_path.glob("**/*.pdf"):
                uri = f"pdf://{pdf_file.relative_to(Path.cwd())}"
                resources.append(
                    Resource(
                        uri=uri,
                        name=pdf_file.name,
                        mimeType="application/pdf",
                        description=f"PDF document: {pdf_file.name}",
                    )
                )
    
    logger.info(f"Found {len(resources)} PDF resources")
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read the content of a PDF resource.
    
    Args:
        uri: URI of the resource (format: pdf://path/to/file.pdf)
        
    Returns:
        Text content of the PDF
    """
    logger.info(f"Reading resource: {uri}")
    
    if not uri.startswith("pdf://"):
        raise ValueError(f"Invalid URI format: {uri}")
    
    # Extract path from URI
    pdf_path = Path.cwd() / uri.replace("pdf://", "")
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Load or retrieve PDF processor
    if str(pdf_path) not in loaded_pdfs:
        loaded_pdfs[str(pdf_path)] = PDFProcessor(pdf_path)
    
    processor = loaded_pdfs[str(pdf_path)]
    text = processor.extract_text()
    
    return text


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools.
    
    Returns:
        List of tools for PDF processing and analysis
    """
    return [
        Tool(
            name="extract_pdf_text",
            description="Extract all text content from a PDF file",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file to extract text from",
                    },
                    "use_layout": {
                        "type": "boolean",
                        "description": "Whether to preserve layout information",
                        "default": True,
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="extract_pdf_metadata",
            description="Extract metadata from a PDF file (title, author, pages, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="search_pdf",
            description="Search for specific text within a PDF file",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search for",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search should be case-sensitive",
                        "default": False,
                    },
                },
                "required": ["pdf_path", "query"],
            },
        ),
        Tool(
            name="answer_question",
            description="Answer a question about a document using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_text": {
                        "type": "string",
                        "description": "The text content of the document",
                    },
                    "question": {
                        "type": "string",
                        "description": "The question to answer",
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["document_text", "question"],
            },
        ),
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
                        "description": "Number of relevant chunks to retrieve (default: 3)",
                        "default": 3,
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["pdf_path", "question"],
            },
        ),
        Tool(
            name="answer_multiple_questions",
            description="Answer multiple questions about a document using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_text": {
                        "type": "string",
                        "description": "The text content of the document",
                    },
                    "questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of questions to answer",
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["document_text", "questions"],
            },
        ),
        Tool(
            name="answer_multiple_questions_rag",
            description="Answer multiple questions using RAG (efficient - retrieves only relevant sections for each question)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                    "questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of questions to answer",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant chunks to retrieve per question (default: 3)",
                        "default": 3,
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["pdf_path", "questions"],
            },
        ),
        Tool(
            name="summarize_document",
            description="Generate a summary of a document using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_text": {
                        "type": "string",
                        "description": "The text content of the document",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of summary in words (optional)",
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["document_text"],
            },
        ),
        Tool(
            name="extract_key_points",
            description="Extract key points from a document using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_text": {
                        "type": "string",
                        "description": "The text content of the document",
                    },
                    "num_points": {
                        "type": "integer",
                        "description": "Number of key points to extract",
                        "default": 5,
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use (optional)",
                    },
                },
                "required": ["document_text"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls from MCP clients.
    
    Args:
        name: Name of the tool to call
        arguments: Arguments for the tool
        
    Returns:
        List of text content results
    """
    logger.info(f"Calling tool: {name}")
    
    try:
        if name == "extract_pdf_text":
            result = pdf_tool.extract_pdf_text(
                pdf_path=arguments["pdf_path"],
                use_layout=arguments.get("use_layout", True),
            )
        elif name == "extract_pdf_metadata":
            result = pdf_tool.extract_pdf_metadata(
                pdf_path=arguments["pdf_path"],
            )
        elif name == "search_pdf":
            result = pdf_tool.search_pdf(
                pdf_path=arguments["pdf_path"],
                query=arguments["query"],
                case_sensitive=arguments.get("case_sensitive", False),
            )
        elif name == "answer_question":
            result = analysis_tool.answer_question(
                document_text=arguments["document_text"],
                question=arguments["question"],
                model=arguments.get("model"),
            )
        elif name == "answer_question_rag":
            result = rag_tool.answer_question_rag(
                pdf_path=arguments["pdf_path"],
                question=arguments["question"],
                top_k=arguments.get("top_k", 3),
                model=arguments.get("model"),
            )
        elif name == "answer_multiple_questions":
            result = analysis_tool.answer_multiple_questions(
                document_text=arguments["document_text"],
                questions=arguments["questions"],
                model=arguments.get("model"),
            )
        elif name == "answer_multiple_questions_rag":
            result = rag_tool.answer_multiple_questions_rag(
                pdf_path=arguments["pdf_path"],
                questions=arguments["questions"],
                top_k=arguments.get("top_k", 3),
                model=arguments.get("model"),
            )
        elif name == "summarize_document":
            result = analysis_tool.summarize_document(
                document_text=arguments["document_text"],
                max_length=arguments.get("max_length"),
                model=arguments.get("model"),
            )
        elif name == "extract_key_points":
            result = analysis_tool.extract_key_points(
                document_text=arguments["document_text"],
                num_points=arguments.get("num_points", 5),
                model=arguments.get("model"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(type="text", text=str(result))]
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    logger.info(f"Starting {settings.mcp_server_name} v{settings.mcp_server_version}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
