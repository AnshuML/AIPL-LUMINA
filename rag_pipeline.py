import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import faiss

# Import logger first
import logging
logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BM25 not available: {e}")
    BM25Okapi = None
    BM25_AVAILABLE = False

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrossEncoder not available: {e}")
    CrossEncoder = None
    CROSS_ENCODER_AVAILABLE = False

# Also check if sentence_transformers is available at all
try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"sentence_transformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from models import Document, DocumentChunk, get_db
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridRAGPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. RAG pipeline will be limited to text search only.")
            self.embedding_model = None
        else:
            self.embedding_model = OpenAIEmbeddings(
                model=config.get("embedding_model", "text-embedding-3-large"),
                openai_api_key=api_key
            )
        
        # Initialize cross-encoder for re-ranking with device handling
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("CrossEncoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")
                self.reranker = None
        else:
            logger.warning("CrossEncoder not available, disabling re-ranking")
            self.reranker = None
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.get("chunk_size", 400),
            chunk_overlap=config.get("chunk_overlap", 80),
            separators=["\n\n", "\n", "•", "●", "- ", "* ", ".", "!", "?"]
        )
        
        # Initialize FAISS index
        self.faiss_index = None
        self.chunk_metadata = []
        self.bm25_index = None
        self.chunk_texts = []
        
        # Load or create indices
        self._load_or_create_indices()
    
    def _load_or_create_indices(self):
        """Load existing indices or create new ones - optimized for cloud deployment."""
        # Check if we're on Streamlit Cloud
        if os.path.exists('/mount/src'):
            # On Streamlit Cloud - always create new indices (no persistent storage)
            logger.info("Streamlit Cloud detected - creating new indices...")
            self._create_new_indices()
            return
        
        # Local development - try to load existing indices
        faiss_path = self.config.get("faiss_path", "index/faiss_index")
        bm25_path = self.config.get("bm25_path", "index/bm25.pkl")
        
        # Create directories if they don't exist
        try:
            os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
            os.makedirs(os.path.dirname(bm25_path), exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
        
        if os.path.exists(faiss_path) and os.path.exists(bm25_path):
            try:
                self._load_indices(faiss_path, bm25_path)
                logger.info(f"Loaded existing indices with {len(self.chunk_texts)} chunks")
            except Exception as e:
                logger.error(f"Error loading indices: {e}")
                logger.info("Creating new indices...")
                self._create_new_indices()
        else:
            logger.info("No existing indices found, creating new ones...")
            self._create_new_indices()
    
    def _load_indices(self, faiss_path: str, bm25_path: str):
        """Load existing FAISS and BM25 indices."""
        # Load FAISS index
        self.faiss_index = faiss.read_index(faiss_path)
        
        # Load BM25 index
        with open(bm25_path, "rb") as f:
            bm25_data = pickle.load(f)
            self.bm25_index = bm25_data["bm25"]
            self.chunk_texts = bm25_data["texts"]
            self.chunk_metadata = bm25_data["metadata"]
    
    def _create_new_indices(self):
        """Create new FAISS and BM25 indices."""
        try:
            # Get all documents from database
            db = next(get_db())
            all_docs = db.query(Document).all()
            documents = db.query(Document).filter(Document.is_processed == True).all()
            
            logger.info(f"Total documents in database: {len(all_docs)}")
            logger.info(f"Processed documents: {len(documents)}")
            logger.info(f"Unprocessed documents: {len(all_docs) - len(documents)}")
            
            # Debug: List all documents
            for doc in all_docs:
                logger.info(f"Document: {doc.filename} - Department: {doc.department} - Processed: {doc.is_processed}")
            
            # Debug: List processed documents
            for doc in documents:
                logger.info(f"Processed Document: {doc.filename} - Department: {doc.department}")
            
            # EMERGENCY FIX: If we have unprocessed documents, process them now
            if len(all_docs) > len(documents):
                logger.warning("Found unprocessed documents, processing them now...")
                unprocessed_docs = [doc for doc in all_docs if not doc.is_processed]
                for doc in unprocessed_docs:
                    try:
                        # Process the document
                        from utils.pdf_processor import process_pdfs
                        processed_docs = process_pdfs([doc.filename], doc.department)
                        
                        # Create chunks in database
                        for i, chunk_data in enumerate(processed_docs):
                            chunk = DocumentChunk(
                                document_id=doc.id,
                                content=chunk_data["content"],
                                chunk_index=i,
                                chunk_metadata=chunk_data.get("metadata", {})
                            )
                            db.add(chunk)
                        
                        # Mark document as processed
                        doc.is_processed = True
                        db.commit()
                        logger.info(f"Processed document: {doc.filename}")
                    except Exception as e:
                        logger.error(f"Error processing document {doc.filename}: {e}")
                
                # Reload documents after processing
                documents = db.query(Document).filter(Document.is_processed == True).all()
                logger.info(f"After processing: {len(documents)} processed documents")
            
            if not documents:
                logger.warning("No processed documents found. Creating empty indices.")
                self._create_empty_indices()
                return
        except Exception as e:
            logger.error(f"Error accessing database: {e}")
            logger.warning("Creating empty indices due to database error.")
            self._create_empty_indices()
            return
        
        # Process all chunks
        all_chunks = []
        all_texts = []
        all_metadata = []
        
        for doc in documents:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            logger.info(f"Loading document: {doc.filename} (Department: {doc.department}) - {len(chunks)} chunks")
            
            # Debug: Show chunk details
            if len(chunks) == 0:
                logger.warning(f"  ⚠️ No chunks found for {doc.filename}!")
            else:
                logger.info(f"  ✅ Chunks loaded successfully for {doc.filename}")
            
            for chunk in chunks:
                all_chunks.append(chunk)
                all_texts.append(chunk.content)
                all_metadata.append({
                    "doc_id": doc.id,
                    "filename": doc.filename,
                    "department": doc.department,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "upload_date": doc.upload_date.isoformat(),
                    "language": doc.language
                })
        
        if not all_chunks:
            self._create_empty_indices()
            return
        
        # Create embeddings
        if self.embedding_model:
            try:
                logger.info(f"Creating embeddings for {len(all_texts)} chunks...")
                embeddings = self.embedding_model.embed_documents(all_texts)
                embeddings = np.array(embeddings).astype('float32')
                
                # Create FAISS index
                if len(embeddings) > 0:
                    dimension = embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                    faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
                    self.faiss_index.add(embeddings)
                    logger.info(f"Created FAISS index with {len(embeddings)} embeddings")
                else:
                    # Create empty index
                    dimension = 1536  # OpenAI embedding dimension
                    self.faiss_index = faiss.IndexFlatIP(dimension)
                    logger.warning("No embeddings created, using empty FAISS index")
            except Exception as e:
                logger.error(f"Error creating embeddings: {e}")
                # Create empty index as fallback
                dimension = 1536  # OpenAI embedding dimension
                self.faiss_index = faiss.IndexFlatIP(dimension)
        else:
            # No embedding model available, create empty index
            logger.warning("No embedding model available, using empty FAISS index")
            dimension = 1536  # OpenAI embedding dimension
            self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Create BM25 index
        try:
            if BM25_AVAILABLE and all_texts:
                tokenized_texts = [text.lower().split() for text in all_texts]
                self.bm25_index = BM25Okapi(tokenized_texts)
                logger.info(f"Created BM25 index with {len(all_texts)} documents")
            else:
                if not BM25_AVAILABLE:
                    logger.warning("BM25 not available, using dummy index")
                else:
                    logger.warning("No texts available, using dummy BM25 index")
                self.bm25_index = BM25Okapi([["dummy"]])  # BM25 can't handle empty corpus
        except Exception as e:
            logger.error(f"Error creating BM25 index: {e}")
            self.bm25_index = BM25Okapi([["dummy"]])
        
        # Store data
        self.chunk_texts = all_texts
        self.chunk_metadata = all_metadata
        
        logger.info(f"RAG Pipeline loaded: {len(all_texts)} chunks from {len(documents)} documents")
        
        # Save indices
        self._save_indices()
        logger.info("Created and saved new indices")
    
    def _create_empty_indices(self):
        """Create empty indices when no documents are available."""
        dimension = 1536  # OpenAI embedding dimension
        self.faiss_index = faiss.IndexFlatIP(dimension)
        # BM25Okapi can't handle empty corpus, so we'll create it with a dummy document
        self.bm25_index = BM25Okapi([["dummy"]])
        self.chunk_texts = []
        self.chunk_metadata = []
    
    def _save_indices(self):
        """Save FAISS and BM25 indices to disk - skip on cloud deployment."""
        # Skip saving on Streamlit Cloud (no persistent storage)
        if os.path.exists('/mount/src'):
            logger.info("Streamlit Cloud detected - skipping index persistence")
            return
        
        faiss_path = self.config.get("faiss_path", "index/faiss_index")
        bm25_path = self.config.get("bm25_path", "index/bm25.pkl")
        
        try:
            # Save FAISS index
            faiss.write_index(self.faiss_index, faiss_path)
            
            # Save BM25 index
            bm25_data = {
                "bm25": self.bm25_index,
                "texts": self.chunk_texts,
                "metadata": self.chunk_metadata
            }
            with open(bm25_path, "wb") as f:
                pickle.dump(bm25_data, f)
        except Exception as e:
            logger.error(f"Error saving indices: {e}")
    
    def add_documents(self, texts: List[str], metadata: List[Dict[str, Any]]):
        """Add multiple documents directly from texts and metadata."""
        if not texts:
            return
        
        # Add chunk_id to metadata if not present
        for i, meta in enumerate(metadata):
            if "chunk_id" not in meta:
                meta["chunk_id"] = f"chunk_{len(self.chunk_texts) + i}"
            if "chunk_index" not in meta:
                meta["chunk_index"] = i
        
        # Create embeddings
        if self.embedding_model:
            embeddings = self.embedding_model.embed_documents(texts)
            embeddings = np.array(embeddings).astype('float32')
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            if self.faiss_index is None or self.faiss_index.ntotal == 0:
                # First document - create new index
                dimension = embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(embeddings)
        else:
            # No embedding model available, create empty index if needed
            if self.faiss_index is None:
                dimension = 1536  # OpenAI embedding dimension
                self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Add to BM25 index
        self.chunk_texts.extend(texts)
        self.chunk_metadata.extend(metadata)
        
        if len(self.chunk_texts) > 0:
            self.bm25_index = BM25Okapi(self.chunk_texts)
        
        # Save indices
        self._save_indices()
        
        logger.info(f"Added {len(texts)} chunks to RAG pipeline")

    def add_document(self, document: Document, chunks: List[DocumentChunk]):
        """Add a new document and its chunks to the indices."""
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk.content for chunk in chunks]
        metadata = [{
            "doc_id": document.id,
            "filename": document.filename,
            "department": document.department,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "upload_date": document.upload_date.isoformat(),
            "language": document.language
        } for chunk in chunks]
        
        # Create embeddings
        if self.embedding_model:
            embeddings = self.embedding_model.embed_documents(texts)
            embeddings = np.array(embeddings).astype('float32')
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            if self.faiss_index.ntotal == 0:
                # First document - create new index
                dimension = embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(embeddings)
        else:
            # No embedding model available, create empty index if needed
            if self.faiss_index.ntotal == 0:
                dimension = 1536  # OpenAI embedding dimension
                self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Add to BM25 index
        tokenized_texts = [text.split() for text in texts]
        if not self.chunk_texts:
            self.bm25_index = BM25Okapi(tokenized_texts)
        else:
            # Rebuild BM25 index with new texts
            all_tokenized = [text.split() for text in self.chunk_texts] + tokenized_texts
            self.bm25_index = BM25Okapi(all_tokenized)
        
        # Update stored data
        self.chunk_texts.extend(texts)
        self.chunk_metadata.extend(metadata)
        
        # Save updated indices
        self._save_indices()
        logger.info(f"Added document {document.filename} with {len(chunks)} chunks")
    
    def search(self, query: str, department: str = None, top_k: int = 50) -> List[Dict[str, Any]]:
        """Perform hybrid search with improved dense and sparse retrieval."""
        if not self.chunk_texts or len(self.chunk_texts) == 0:
            logger.warning("No chunks available for search")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        # Expand search for better coverage
        search_top_k = min(top_k * 2, 200)  # Search more chunks for better results
        
        # Dense search (FAISS) - improved
        dense_results = []
        if self.embedding_model and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            query_embedding = self.embedding_model.embed_query(query)
            query_embedding = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            dense_scores, dense_indices = self.faiss_index.search(query_embedding, search_top_k)
            for score, idx in zip(dense_scores[0], dense_indices[0]):
                if idx < len(self.chunk_metadata) and score > 0.1:  # Filter low scores
                    dense_results.append({
                        "chunk_id": self.chunk_metadata[idx]["chunk_id"],
                        "text": self.chunk_texts[idx],
                        "metadata": self.chunk_metadata[idx],
                        "score": float(score),
                        "type": "dense"
                    })
        
        # Sparse search (BM25) - improved
        tokenized_query = query.lower().split()
        # Add query expansion for better matching
        expanded_query = tokenized_query + [word for word in tokenized_query if len(word) > 3]
        
        sparse_results = []
        if BM25_AVAILABLE and len(self.chunk_texts) > 0 and self.bm25_index is not None:
            try:
                bm25_scores = self.bm25_index.get_scores(expanded_query)
                sparse_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:search_top_k]
            except Exception as e:
                logger.error(f"Error in BM25 search: {e}")
                sparse_indices = []
        else:
            if not BM25_AVAILABLE:
                logger.warning("BM25 not available, skipping keyword search")
            sparse_indices = []
            
        for idx in sparse_indices:
            if BM25_AVAILABLE and 'bm25_scores' in locals() and bm25_scores[idx] > 0.1:  # Filter low scores
                sparse_results.append({
                    "chunk_id": self.chunk_metadata[idx]["chunk_id"],
                    "text": self.chunk_texts[idx],
                    "metadata": self.chunk_metadata[idx],
                    "score": float(bm25_scores[idx]),
                    "type": "sparse"
                    })
        
        # Combine and deduplicate results with better scoring
        combined_results = self._merge_results(dense_results, sparse_results)
        
        # Filter by department if specified (with fallback to all departments if no results)
        if department:
            dept_filtered = [r for r in combined_results if r["metadata"]["department"] == department]
            if dept_filtered:
                combined_results = dept_filtered
            else:
                logger.warning(f"No results found for department '{department}', searching all departments")
                # Don't filter by department if no results found
        
        # Sort by combined score for better ranking
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        return combined_results[:top_k]
    
    def _merge_results(self, dense_results: List[Dict], sparse_results: List[Dict]) -> List[Dict]:
        """Merge dense and sparse results, removing duplicates."""
        # Create a dictionary to store unique results by chunk_id
        unique_results = {}
        
        # Add dense results
        for result in dense_results:
            chunk_id = result["chunk_id"]
            if chunk_id not in unique_results:
                unique_results[chunk_id] = result
            else:
                # Keep the higher score
                if result["score"] > unique_results[chunk_id]["score"]:
                    unique_results[chunk_id] = result
        
        # Add sparse results
        for result in sparse_results:
            chunk_id = result["chunk_id"]
            if chunk_id not in unique_results:
                unique_results[chunk_id] = result
            else:
                # Combine scores or keep higher
                if result["score"] > unique_results[chunk_id]["score"]:
                    unique_results[chunk_id] = result
        
        return list(unique_results.values())
    
    def rerank_results(self, query: str, results: List[Dict], top_n: int = 10) -> List[Dict]:
        """Re-rank results using cross-encoder."""
        if not results:
            return []
        
        # If reranker is not available, return results sorted by original score
        if self.reranker is None:
            logger.warning("Reranker not available, using original scores")
            for result in results:
                result["rerank_score"] = result.get("score", 0.0)
            return sorted(results, key=lambda x: x["rerank_score"], reverse=True)[:top_n]
        
        try:
            # Prepare query-document pairs for re-ranking
            pairs = [(query, result["text"]) for result in results]
            
            # Get re-ranking scores
            rerank_scores = self.reranker.predict(pairs)
            
            # Add re-ranking scores to results
            for i, result in enumerate(results):
                result["rerank_score"] = float(rerank_scores[i])
            
            # Sort by re-ranking score
            reranked_results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
            
            return reranked_results[:top_n]
        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            # Fallback to original scores
            for result in results:
                result["rerank_score"] = result.get("score", 0.0)
            return sorted(results, key=lambda x: x["rerank_score"], reverse=True)[:top_n]
    
    def apply_mmr(self, results: List[Dict], lambda_param: float = 0.7, top_k: int = 10) -> List[Dict]:
        """Apply Maximal Marginal Relevance for diversity."""
        if len(results) <= top_k or not results:
            return results
        
        # Convert texts to embeddings for MMR
        texts = [result["text"] for result in results]
        if not texts or not self.embedding_model:
            logger.warning("Embedding model not available for MMR, returning original results")
            return results[:top_k]
            
        try:
            embeddings = self.embedding_model.embed_documents(texts)
            embeddings = np.array(embeddings)
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            # Avoid division by zero
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms
        except Exception as e:
            logger.error(f"Error creating embeddings for MMR: {e}")
            return results[:top_k]
        
        # MMR algorithm
        selected = []
        remaining = list(range(len(results)))
        
        # Select first result (highest score)
        selected.append(remaining.pop(0))
        
        while len(selected) < top_k and remaining:
            max_mmr_score = -1
            best_idx = 0
            
            for i, idx in enumerate(remaining):
                # Relevance score (original score)
                relevance = results[idx]["rerank_score"] if "rerank_score" in results[idx] else results[idx]["score"]
                
                # Max similarity to already selected
                max_sim = 0
                for sel_idx in selected:
                    sim = np.dot(embeddings[idx], embeddings[sel_idx])
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                
                if mmr_score > max_mmr_score:
                    max_mmr_score = mmr_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return [results[i] for i in selected]
    
    def get_context_for_llm(self, query: str, department: str = None, max_tokens: int = 4000) -> Tuple[List[Dict], str]:
        """Get context for LLM with improved accuracy and better chunk selection."""
        # Search for relevant chunks with higher top_k for better coverage
        search_results = self.search(query, department, top_k=100)
        
        if not search_results:
            return [], "No relevant documents found."
        
        # Re-rank results with more chunks for better accuracy
        reranked_results = self.rerank_results(query, search_results, top_n=30)
        
        # Apply MMR for diversity but keep more chunks for better context
        mmr_results = self.apply_mmr(reranked_results, lambda_param=0.6, top_k=15)
        
        # Build context with better chunk selection
        context_chunks = []
        context_text = ""
        current_tokens = 0
        
        # Sort by rerank score to get the most relevant chunks first
        sorted_results = sorted(mmr_results, key=lambda x: x.get("rerank_score", x["score"]), reverse=True)
        
        for result in sorted_results:
            chunk_text = result["text"]
            metadata = result["metadata"]
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk_text) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            # Clean and format chunk text for better LLM understanding
            cleaned_text = chunk_text.strip()
            if not cleaned_text:
                continue
                
            # Add chunk with better formatting
            formatted_chunk = f"{cleaned_text}\n\n"
            
            context_chunks.append({
                "chunk_id": result["chunk_id"],
                "text": cleaned_text,
                "metadata": metadata,
                "score": result.get("rerank_score", result["score"])
            })
            
            context_text += formatted_chunk
            current_tokens += chunk_tokens
        
        return context_chunks, context_text

# Global pipeline instance
pipeline = None

def get_rag_pipeline() -> HybridRAGPipeline:
    """Get or create the global RAG pipeline instance."""
    global pipeline
    if pipeline is None:
        from shared_config import config
        rag_config = config.get_rag_config()
        pipeline = HybridRAGPipeline(rag_config)
    return pipeline
