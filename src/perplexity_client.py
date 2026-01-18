"""Perplexity API client for document analysis and question answering."""
import logging
from typing import List, Dict, Any, Optional
import requests
from src.config import settings

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for interacting with the Perplexity API."""
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key (defaults to settings)
            api_url: Perplexity API URL (defaults to settings)
        """
        self.api_key = api_key or settings.perplexity_api_key
        self.api_url = api_url or settings.perplexity_api_url
        
        if not self.api_key:
            raise ValueError("Perplexity API key is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def analyze_document(
        self,
        document_text: str,
        question: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Analyze a document and answer a question.
        
        Args:
            document_text: The text content of the document
            question: The question to answer based on the document
            model: Model name to use (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens in response (defaults to settings)
            
        Returns:
            Dictionary containing the answer and metadata
        """
        model = model or settings.model_name
        temperature = temperature if temperature is not None else settings.temperature
        max_tokens = max_tokens or settings.max_tokens
        
        # Construct the prompt - IMPORTANT: Answer ONLY from PDF content
        system_message = (
            "You are a document analysis assistant. Your ONLY job is to extract information from the provided document. "
            "CRITICAL RULES:\n"
            "1. Answer ONLY using information explicitly stated in the document\n"
            "2. Do NOT use any external knowledge or information from the web\n"
            "3. If the answer is not in the document, respond with 'This information is not found in the document'\n"
            "4. Provide direct quotes from the document when possible\n"
            "5. Do not make inferences beyond what is explicitly stated"
        )
        
        user_message = f"""DOCUMENT CONTENT:
---
{document_text}
---

QUESTION: {question}

Extract the answer from the document above. Only use information from the document."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            logger.info(f"Sending request to Perplexity API for question: {question[:50]}...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=60,
            )
            
            # Log detailed error if request failed
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}")
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the answer from the response
            answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info("Successfully received response from Perplexity")
            
            return {
                "question": question,
                "answer": answer,
                "model": model,
                "usage": result.get("usage", {}),
                "finish_reason": result.get("choices", [{}])[0].get("finish_reason", ""),
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Perplexity API: {e}")
            raise
    
    def batch_analyze(
        self,
        document_text: str,
        questions: List[str],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Analyze a document with multiple questions.
        
        Args:
            document_text: The text content of the document
            questions: List of questions to answer
            model: Model name to use (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens in response (defaults to settings)
            
        Returns:
            List of dictionaries containing answers and metadata
        """
        results = []
        
        logger.info(f"Processing {len(questions)} questions")
        
        for idx, question in enumerate(questions, start=1):
            logger.info(f"Processing question {idx}/{len(questions)}")
            
            try:
                result = self.analyze_document(
                    document_text=document_text,
                    question=question,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing question {idx}: {e}")
                results.append({
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "model": model or settings.model_name,
                    "error": True,
                })
        
        logger.info(f"Completed processing {len(results)} questions")
        return results
    
    def summarize_document(
        self,
        document_text: str,
        max_length: Optional[int] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate a summary of the document.
        
        Args:
            document_text: The text content of the document
            max_length: Maximum length of summary in words
            model: Model name to use (defaults to settings)
            
        Returns:
            Summary text
        """
        length_instruction = f" in approximately {max_length} words" if max_length else ""
        
        question = f"Please provide a comprehensive summary of this document{length_instruction}."
        
        result = self.analyze_document(
            document_text=document_text,
            question=question,
            model=model,
        )
        
        return result["answer"]
    
    def extract_key_points(
        self,
        document_text: str,
        num_points: int = 5,
        model: Optional[str] = None,
    ) -> List[str]:
        """Extract key points from the document.
        
        Args:
            document_text: The text content of the document
            num_points: Number of key points to extract
            model: Model name to use (defaults to settings)
            
        Returns:
            List of key points
        """
        question = f"Please extract the {num_points} most important key points from this document. Format each point as a bullet point."
        
        result = self.analyze_document(
            document_text=document_text,
            question=question,
            model=model,
        )
        
        answer = result["answer"]
        
        # Parse bullet points from the response
        lines = answer.split("\n")
        key_points = [
            line.strip().lstrip("•-*").strip()
            for line in lines
            if line.strip() and any(line.strip().startswith(c) for c in ["•", "-", "*", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        ]
        
        return key_points[:num_points] if key_points else [answer]
    
    def summarize_answer(
        self,
        answer_text: str,
        question: str = "",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Summarize and format a raw answer to make it more user-friendly.
        
        Args:
            answer_text: The raw answer text to summarize
            question: The original question (optional, for context)
            model: Model name to use (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens in response (defaults to settings)
            
        Returns:
            Dictionary containing the summarized answer and metadata
        """
        model = model or settings.model_name
        temperature = temperature if temperature is not None else settings.temperature
        max_tokens = max_tokens or settings.max_tokens
        
        system_message = (
            "You are an expert at summarizing and formatting answers. "
            "Your job is to make answers clear, concise, and user-friendly. "
            "CRITICAL RULES:\n"
            "1. Whatever the question, you need to provide a summary then the answer to the questions\n"
            "2. Keep all factual information from the original answer\n"
            "3. Keep all PII's and show them clearly\n"
            "4. Make the answer more readable and well-structured\n"
            "5. Use bullet points, numbering, or paragraphs as appropriate\n"
            "6. Remove redundancy but preserve all key details\n"
            "7. If the answer says information is not found, keep that clear"
        )
        
        question_context = f"Original Question: {question}\n\n" if question else ""
        
        user_message = f"""{question_context}Raw Answer to Summarize:
---
{answer_text}
---

Please provide a clear, well-formatted summary of this answer. Make it easy to read and understand while preserving all important information."""
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            logger.info("Sending request to Perplexity for answer summarization...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=60,
            )
            
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}")
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the summarized answer from the response
            summarized = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info("Successfully summarized answer")
            
            return {
                "original_answer": answer_text,
                "summarized_answer": summarized,
                "model": model,
                "usage": result.get("usage", {}),
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error summarizing answer: {e}")
            # If summarization fails, return original answer
            return {
                "original_answer": answer_text,
                "summarized_answer": answer_text,
                "model": model,
                "usage": {},
                "summarization_error": str(e)
            }
