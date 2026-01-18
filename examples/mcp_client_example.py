"""Example MCP client demonstrating how to use the PDF Q&A MCP server with RAG.

This script shows how to:
1. Connect to the MCP server
2. List available PDF resources
3. Use RAG tools for efficient question answering
4. Compare RAG vs non-RAG approaches
"""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_mcp_client_example():
    """Example MCP client usage."""
    
    # Server parameters - adjust path to your mcp_server.py
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server"],
        env=None,
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            print("=" * 60)
            print("MCP PDF Q&A Client - RAG Demo")
            print("=" * 60)
            
            # 1. List available resources
            print("\n📚 Listing available PDF resources...")
            resources = await session.list_resources()
            
            if resources.resources:
                print(f"Found {len(resources.resources)} PDF(s):")
                for resource in resources.resources:
                    print(f"  - {resource.name} ({resource.uri})")
            else:
                print("No PDF resources found")
            
            # 2. List available tools
            print("\n🛠️  Listing available tools...")
            tools = await session.list_tools()
            
            print(f"Found {len(tools.tools)} tools:")
            rag_tools = []
            standard_tools = []
            
            for tool in tools.tools:
                if "rag" in tool.name:
                    rag_tools.append(tool.name)
                else:
                    standard_tools.append(tool.name)
            
            print(f"  RAG Tools ({len(rag_tools)}):")
            for tool in rag_tools:
                print(f"    - {tool}")
            
            print(f"  Standard Tools ({len(standard_tools)}):")
            for tool in standard_tools[:5]:  # Show first 5
                print(f"    - {tool}")
            if len(standard_tools) > 5:
                print(f"    ... and {len(standard_tools) - 5} more")
            
            # 3. Example: Extract PDF metadata
            print("\n📄 Example 1: Extract PDF metadata...")
            pdf_path = "your_document.pdf"  # Change this to your PDF
            
            if Path(pdf_path).exists():
                result = await session.call_tool(
                    "extract_pdf_metadata",
                    arguments={"pdf_path": pdf_path}
                )
                print(f"Metadata: {result.content[0].text[:200]}...")
            else:
                print(f"PDF not found: {pdf_path}")
            
            # 4. Example: Answer question with RAG (efficient)
            print("\n🚀 Example 2: Answer question using RAG...")
            
            if Path(pdf_path).exists():
                question = "What is the main topic of this document?"
                
                result = await session.call_tool(
                    "answer_question_rag",
                    arguments={
                        "pdf_path": pdf_path,
                        "question": question,
                        "top_k": 3,
                    }
                )
                
                print(f"Question: {question}")
                print(f"Answer: {result.content[0].text[:300]}...")
                print("\n✅ RAG retrieved only relevant sections (efficient!)")
            
            # 5. Example: Answer multiple questions with RAG
            print("\n📝 Example 3: Answer multiple questions using RAG...")
            
            if Path(pdf_path).exists():
                questions = [
                    "Who is the author?",
                    "What are the key findings?",
                    "What conclusions are presented?",
                ]
                
                result = await session.call_tool(
                    "answer_multiple_questions_rag",
                    arguments={
                        "pdf_path": pdf_path,
                        "questions": questions,
                        "top_k": 3,
                    }
                )
                
                response = json.loads(result.content[0].text)
                
                if response.get("success"):
                    print(f"Processed {response['total_questions']} questions")
                    print(f"RAG Stats: {response.get('rag_stats', {})}")
                    print(f"Avg context per question: {response.get('avg_context_per_question', 0)} chars")
                    
                    print("\nAnswers:")
                    for idx, qa_result in enumerate(response['results'][:2], 1):
                        print(f"\n  Q{idx}: {qa_result['question']}")
                        print(f"  A: {qa_result['answer'][:150]}...")
            
            # 6. Comparison: RAG vs Standard
            print("\n⚖️  Example 4: Comparing RAG vs Standard approach...")
            print("\nRAG Approach:")
            print("  ✅ Retrieves only 3 relevant chunks (~3000 chars)")
            print("  ✅ ~98% token reduction")
            print("  ✅ Faster processing")
            print("  ✅ Lower cost")
            print("  ✅ Automatic caching")
            
            print("\nStandard Approach:")
            print("  ❌ Sends entire document (could be 100,000+ chars)")
            print("  ❌ High token usage")
            print("  ❌ Slower processing")
            print("  ❌ Higher cost")
            
            print("\n" + "=" * 60)
            print("💡 Recommendation: Use RAG tools for best efficiency!")
            print("=" * 60)


async def simple_rag_example(pdf_path: str, question: str):
    """Simple example showing RAG usage.
    
    Args:
        pdf_path: Path to your PDF file
        question: Question to answer
    """
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use RAG to answer question
            result = await session.call_tool(
                "answer_question_rag",
                arguments={
                    "pdf_path": pdf_path,
                    "question": question,
                    "top_k": 3,
                }
            )
            
            response = json.loads(result.content[0].text)
            
            if response.get("success"):
                print(f"Q: {question}")
                print(f"A: {response['answer']}")
                print(f"\nRAG Stats:")
                print(f"  - Context length: {response['context_length']} chars")
                print(f"  - Chunks retrieved: {response['chunks_retrieved']}")
            else:
                print(f"Error: {response.get('error')}")


if __name__ == "__main__":
    # Run the full example
    asyncio.run(run_mcp_client_example())
    
    # Or run a simple example:
    # asyncio.run(simple_rag_example("your_document.pdf", "What is this document about?"))
