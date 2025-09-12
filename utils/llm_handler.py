import os
import openai
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class LLMHandler:
    def __init__(self, model: str = "gpt-4", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Detect the language of the following text and respond with only the ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'hi', 'de')."},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=10
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    def generate_answer(self, query: str, context_chunks: List[Dict], department: str, language: str = "en") -> Dict[str, Any]:
        """Generate a comprehensive answer with proper formatting and source attribution."""
        try:
            # Build context with source attribution
            context_text = self._build_context_with_sources(context_chunks)
            
            # Determine confidence based on context quality
            confidence = self._calculate_confidence(context_chunks, query)
            
            # Create the prompt
            prompt = self._create_prompt(query, context_text, department, language)
            
            # Generate response
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant for Ajit Industries Pvt. Ltd. Follow the exact format specified in the prompt."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1500
            )
            
            answer_text = response.choices[0].message.content.strip()
            
            # Extract sources for display
            sources = self._extract_sources(context_chunks)
            
            return {
                "answer": answer_text,
                "confidence": confidence,
                "sources": sources,
                "chunk_ids": [chunk["chunk_id"] for chunk in context_chunks],
                "model_used": self.model,
                "response_time": response.usage.total_tokens / 1000  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "answer": "I apologize, but I encountered an error while processing your request. Please try again or contact support.",
                "confidence": "low",
                "sources": [],
                "chunk_ids": [],
                "model_used": self.model,
                "response_time": 0
            }
    
    def _build_context_with_sources(self, context_chunks: List[Dict]) -> str:
        """Build context text without source references for cleaner answers."""
        context_parts = []
        
        for chunk in context_chunks:
            context_parts.append(chunk['text'])
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence(self, context_chunks: List[Dict], query: str) -> str:
        """Calculate confidence level based on context quality and relevance."""
        if not context_chunks:
            return "low"
        
        # Get rerank scores if available (more accurate than BM25 scores)
        scores = [c.get("rerank_score", c.get("score", 0)) for c in context_chunks]
        
        if not scores:
            return "low"
        
        # Calculate average score
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        
        # More sophisticated confidence calculation
        if max_score > 0.8 and avg_score > 0.6 and len(context_chunks) >= 3:
            return "high"
        elif max_score > 0.6 and avg_score > 0.4 and len(context_chunks) >= 2:
            return "medium"
        elif max_score > 0.4 and len(context_chunks) >= 1:
            return "medium"
        else:
            return "low"
    
    def _create_prompt(self, query: str, context: str, department: str, language: str) -> str:
        """Create a comprehensive prompt for the LLM."""
        language_names = {
            "en": "English",
            "hi": "Hindi", 
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese"
        }
        
        lang_name = language_names.get(language, "English")
        
        return f"""You are an expert AI assistant for Ajit Industries Pvt. Ltd. specializing in {department} department policies and procedures.

RESPOND IN {lang_name.upper()}

COMPANY DOCUMENTS CONTEXT:
{context}

USER QUESTION:
{query}

CRITICAL INSTRUCTIONS:
1. Answer ONLY based on the provided context - be precise and accurate
2. If context is insufficient, clearly state "I don't have enough information in our {department} documents to answer this question. Please contact the {department} department for assistance."
3. For sensitive information (personal data, financial details, legal matters), recommend contacting HR/admin
4. Provide detailed, actionable answers with specific steps when applicable
5. Use clear formatting with bullet points or numbered lists for procedures
6. Be conversational but professional
7. Focus on practical, implementable guidance

RESPONSE FORMAT:
**Answer (in {lang_name}) — Confidence: [High/Medium/Low]**

[Provide a comprehensive, detailed answer with specific information from the context. Use bullet points or numbered lists for procedures. Be thorough but concise.]

IMPORTANT:
- Do NOT include source references, document names, or chunk IDs
- Provide actionable, practical guidance
- If you cannot find relevant information, clearly state this
- For sensitive queries, recommend contacting the appropriate department
- Be specific about policies, procedures, and requirements"""

    def _extract_sources(self, context_chunks: List[Dict]) -> List[Dict]:
        """Extract source information for display."""
        sources = []
        for chunk in context_chunks:
            metadata = chunk["metadata"]
            sources.append({
                "title": metadata["filename"],
                "department": metadata["department"],
                "chunk_id": chunk["chunk_id"],
                "snippet": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })
        return sources
    
    def create_support_ticket(self, query: str, user_email: str, department: str) -> Dict[str, Any]:
        """Create a support ticket for sensitive queries."""
        try:
            # This would integrate with your support ticket system
            ticket_data = {
                "subject": f"Sensitive Query from {department} Department",
                "description": f"User: {user_email}\nDepartment: {department}\nQuery: {query}\n\nThis query requires human review due to sensitive content.",
                "priority": "medium",
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # In a real implementation, you would save this to your database
            logger.info(f"Support ticket created: {ticket_data}")
            
            return {
                "ticket_id": f"TICKET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "message": "Your query has been escalated to our support team. You will receive a response within 24 hours.",
                "ticket_data": ticket_data
            }
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return {
                "ticket_id": None,
                "message": "There was an error creating your support ticket. Please contact support directly.",
                "ticket_data": None
            }

# Global LLM handler instance
llm_handler = LLMHandler()

# Legacy compatibility functions
def generate_answer(context, question):
    """Legacy function for backward compatibility."""
    # This is a simplified version for the existing Streamlit app
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an HR Policy Assistant for Ajit Industries Pvt. Ltd. Always respond in the same language as the question. Use ONLY information from the provided context."},
                {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nProvide a detailed, pointwise answer with clear formatting."}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"

# Legacy embedding function for compatibility
class EmbeddingFunction:
    def embed_documents(self, texts):
        try:
            response = openai.Embedding.create(
                model="text-embedding-3-large",
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return []

    def embed_query(self, text):
        try:
            response = openai.Embedding.create(
                model="text-embedding-3-large",
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error creating query embedding: {e}")
            return []

embed_fn = EmbeddingFunction()

