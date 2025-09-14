#!/usr/bin/env python3
"""
Enhanced RAG Pipeline with robust error handling and automatic processing
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_rag_pipeline import SimpleRAGPipeline
from simple_config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Availability flags for optional dependencies
BM25_AVAILABLE = True
CROSS_ENCODER_AVAILABLE = True

class EnhancedRAGPipeline:
    """Enhanced RAG Pipeline with robust error handling"""
    
    def __init__(self):
        self.rag_pipeline = None
        self.last_rebuild = None
        self.error_count = 0
        self.max_errors = 5
        
    def initialize(self):
        """Initialize the RAG pipeline with error handling"""
        try:
            logger.info("🔧 Initializing Enhanced RAG Pipeline...")
            self.rag_pipeline = SimpleRAGPipeline()
            self.error_count = 0
            logger.info("✅ Enhanced RAG Pipeline initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG pipeline: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def search_with_fallback(self, query: str, department: str = "HR", top_k: int = 5) -> List[Dict]:
        """Search with fallback mechanisms"""
        try:
            if not self.rag_pipeline:
                logger.warning("⚠️ RAG pipeline not initialized, attempting to initialize...")
                if not self.initialize():
                    return []
            
            # Try search
            results = self.rag_pipeline.search(query, department=department, top_k=top_k)
            
            if results:
                logger.info(f"✅ Search successful: {len(results)} results found")
                return results
            else:
                logger.warning(f"⚠️ No results found for query: {query}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            self.error_count += 1
            
            if self.error_count >= self.max_errors:
                logger.error("❌ Too many errors, attempting to rebuild pipeline...")
                self.rebuild_pipeline()
                self.error_count = 0
            
            return []
    
    def rebuild_pipeline(self):
        """Rebuild the entire pipeline"""
        try:
            logger.info("🔄 Rebuilding RAG pipeline...")
            
            if self.rag_pipeline:
                self.rag_pipeline.rebuild_indices()
                self.last_rebuild = datetime.now()
                logger.info("✅ RAG pipeline rebuilt successfully")
                return True
            else:
                logger.error("❌ RAG pipeline not available for rebuild")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to rebuild pipeline: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        status = {
            "initialized": self.rag_pipeline is not None,
            "last_rebuild": self.last_rebuild,
            "error_count": self.error_count,
            "faiss_chunks": 0,
            "bm25_chunks": 0,
            "total_documents": 0
        }
        
        if self.rag_pipeline:
            try:
                status["faiss_chunks"] = self.rag_pipeline.faiss_index.ntotal if hasattr(self.rag_pipeline, 'faiss_index') and self.rag_pipeline.faiss_index else 0
                status["bm25_chunks"] = len(self.rag_pipeline.chunk_texts) if hasattr(self.rag_pipeline, 'chunk_texts') else 0
                
                # Get document count
                documents = config.get_documents()
                status["total_documents"] = len(documents)
                
            except Exception as e:
                logger.error(f"❌ Error getting pipeline status: {e}")
        
        return status
    
    def process_query_robust(self, query: str, department: str = "HR", language: str = "en") -> Dict[str, Any]:
        """Process query with robust error handling"""
        try:
            logger.info(f"🔍 Processing query: {query[:50]}...")
            
            # Search for relevant chunks
            search_results = self.search_with_fallback(query, department, top_k=5)
            
            if not search_results:
                return {
                    "answer": "I couldn't find relevant information in the uploaded documents. Please make sure documents are uploaded for this department or try rephrasing your question.",
                    "confidence": "low",
                    "sources": [],
                    "chunks_used": 0,
                    "error": "No relevant chunks found"
                }
            
            # Generate answer using LLM
            try:
                from utils.llm_handler import LLMHandler
                llm_handler = LLMHandler()
                
                response_data = llm_handler.generate_answer(
                    query=query,
                    context_chunks=search_results,
                    department=department,
                    language=language
                )
                
                # Add metadata
                response_data["chunks_used"] = len(search_results)
                response_data["search_successful"] = True
                
                logger.info(f"✅ Query processed successfully: {len(search_results)} chunks used")
                return response_data
                
            except Exception as e:
                logger.error(f"❌ LLM generation failed: {e}")
                return {
                    "answer": "I found relevant information but couldn't generate a proper response. Please try rephrasing your question.",
                    "confidence": "low",
                    "sources": [result["metadata"]["filename"] for result in search_results],
                    "chunks_used": len(search_results),
                    "error": f"LLM generation failed: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "answer": "I encountered an error while processing your request. Please try again or contact support.",
                "confidence": "low",
                "sources": [],
                "chunks_used": 0,
                "error": f"Query processing failed: {str(e)}"
            }
    
    def auto_rebuild_if_needed(self):
        """Automatically rebuild if needed"""
        try:
            # Check if rebuild is needed
            documents = config.get_documents()
            current_doc_count = len(documents)
            
            # Get current chunk count
            if self.rag_pipeline and hasattr(self.rag_pipeline, 'chunk_texts'):
                current_chunk_count = len(self.rag_pipeline.chunk_texts)
            else:
                current_chunk_count = 0
            
            # Simple heuristic: if document count changed significantly, rebuild
            if current_doc_count > 0 and current_chunk_count == 0:
                logger.info("🔄 No chunks found, rebuilding pipeline...")
                return self.rebuild_pipeline()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Auto-rebuild check failed: {e}")
            return False

# Global instance
enhanced_rag = EnhancedRAGPipeline()

def get_enhanced_rag_pipeline():
    """Get the global enhanced RAG pipeline instance"""
    if not enhanced_rag.rag_pipeline:
        enhanced_rag.initialize()
    return enhanced_rag

def process_query_enhanced(query: str, department: str = "HR", language: str = "en") -> Dict[str, Any]:
    """Process query using enhanced RAG pipeline"""
    rag = get_enhanced_rag_pipeline()
    
    # Auto-rebuild if needed
    rag.auto_rebuild_if_needed()
    
    # Process query
    return rag.process_query_robust(query, department, language)

if __name__ == "__main__":
    # Test the enhanced pipeline
    print("🧪 Testing Enhanced RAG Pipeline...")
    
    rag = get_enhanced_rag_pipeline()
    
    # Test status
    status = rag.get_pipeline_status()
    print(f"📊 Pipeline Status: {status}")
    
    # Test query
    test_query = "What is the travel allowance policy?"
    result = rag.process_query_robust(test_query, "HR", "en")
    
    print(f"🔍 Query: {test_query}")
    print(f"✅ Answer: {result['answer'][:200]}...")
    print(f"📊 Confidence: {result['confidence']}")
    print(f"📄 Sources: {len(result.get('sources', []))}")
    print(f"🔧 Chunks Used: {result.get('chunks_used', 0)}")
