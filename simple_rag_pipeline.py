"""
Simplified RAG Pipeline without database dependency
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import faiss
import logging

# Import logger first
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
    logger.info("CrossEncoder imported successfully")
except ImportError as e:
    logger.warning(f"CrossEncoder not available (ImportError): {e}")
    CrossEncoder = None
    CROSS_ENCODER_AVAILABLE = False
except Exception as e:
    logger.warning(f"CrossEncoder not available (Exception): {e}")
    CrossEncoder = None
    CROSS_ENCODER_AVAILABLE = False

import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from simple_config import config

class SimpleRAGPipeline:
    def __init__(self):
        self.config = config.RAG_CONFIG
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. RAG pipeline will be limited to text search only.")
            self.embedding_model = None
        else:
            self.embedding_model = OpenAIEmbeddings(
                model=self.config.get("embedding_model", "text-embedding-3-large"),
                openai_api_key=api_key
            )
        
        # Initialize cross-encoder for re-ranking
        self.reranker = None
        if CROSS_ENCODER_AVAILABLE and CrossEncoder is not None:
            try:
                # Try to load a lightweight cross-encoder
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("CrossEncoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder: {e}")
                self.reranker = None
        else:
            logger.info("CrossEncoder not available, using basic search only")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get("chunk_size", 400),
            chunk_overlap=self.config.get("chunk_overlap", 80),
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize indices
        self.faiss_index = None
        self.bm25_index = None
        self.chunk_texts = []
        self.chunk_metadata = []
        
        # Load or create indices
        self._load_or_create_indices()
    
    def _load_or_create_indices(self):
        """Load existing indices or create new ones"""
        # Always create new indices to ensure latest documents are processed
        logger.info("Creating new indices to ensure latest documents are processed...")
        self._create_new_indices()
    
    def _load_indices(self, faiss_path: str, bm25_path: str):
        """Load existing FAISS and BM25 indices"""
        # Load FAISS index
        self.faiss_index = faiss.read_index(faiss_path)
        
        # Load BM25 index
        with open(bm25_path, 'rb') as f:
            bm25_data = pickle.load(f)
            self.bm25_index = bm25_data["bm25"]
            self.chunk_texts = bm25_data["texts"]
            self.chunk_metadata = bm25_data["metadata"]
    
    def _create_new_indices(self):
        """Create new FAISS and BM25 indices from documents"""
        try:
            # Get all documents
            documents = config.get_documents()
            logger.info(f"Found {len(documents)} documents")
            
            if not documents:
                logger.warning("No documents found!")
                self._create_empty_indices()
                return
            
            # Process all documents
            all_texts = []
            all_metadata = []
            
            for doc in documents:
                logger.info(f"Processing document: {doc['filename']} (Department: {doc['department']})")
                
                try:
                    # Process document and get chunks
                    chunks = []
                    
                    if doc['filename'].lower().endswith('.pdf'):
                        try:
                            from utils.pdf_processor import process_pdfs
                            chunks = process_pdfs([doc['filepath']], doc['department'])
                        except Exception as e:
                            logger.error(f"Error processing PDF {doc['filename']}: {e}")
                            continue
                    elif doc['filename'].lower().endswith('.txt'):
                        # Process text file directly
                        try:
                            with open(doc['filepath'], 'r', encoding='utf-8') as f:
                                text = f.read()
                            
                            if text.strip():
                                # Split text into chunks
                                text_chunks = self.text_splitter.split_text(text)
                                for chunk_text in text_chunks:
                                    if chunk_text.strip():
                                        chunks.append({
                                            "content": chunk_text,
                                            "metadata": {
                                                "source": doc['filepath'],
                                                "policy_type": "text",
                                                "department": doc['department']
                                            }
                                        })
                        except Exception as e:
                            logger.error(f"Error reading text file {doc['filename']}: {e}")
                            continue
                    
                    logger.info(f"  Created {len(chunks)} chunks")
                    
                    for i, chunk_data in enumerate(chunks):
                        all_texts.append(chunk_data["content"])
                        all_metadata.append({
                            "filename": doc['filename'],
                            "department": doc['department'],
                            "chunk_index": i,
                            "filepath": doc['filepath']
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing {doc['filename']}: {e}")
                    continue
            
            if not all_texts:
                logger.warning("No chunks created from documents!")
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
                        self.faiss_index = faiss.IndexFlatIP(dimension)
                        faiss.normalize_L2(embeddings)
                        self.faiss_index.add(embeddings)
                        logger.info(f"Created FAISS index with {len(embeddings)} embeddings")
                    else:
                        self._create_empty_indices()
                        return
                except Exception as e:
                    logger.error(f"Error creating embeddings: {e}")
                    self._create_empty_indices()
                    return
            else:
                logger.warning("No embedding model available, using empty FAISS index")
                self._create_empty_indices()
                return
            
            # Create BM25 index
            try:
                if BM25_AVAILABLE and all_texts:
                    tokenized_texts = [text.lower().split() for text in all_texts]
                    self.bm25_index = BM25Okapi(tokenized_texts)
                    logger.info(f"Created BM25 index with {len(all_texts)} documents")
                else:
                    if not BM25_AVAILABLE:
                        logger.warning("BM25 not available, skipping keyword search")
                    self.bm25_index = None
            except Exception as e:
                logger.error(f"Error creating BM25 index: {e}")
                self.bm25_index = None
            
            # Store texts and metadata
            self.chunk_texts = all_texts
            self.chunk_metadata = all_metadata
            
            # Save indices (only locally)
            if not os.path.exists('/mount/src'):
                self._save_indices()
            
            logger.info(f"RAG Pipeline loaded: {len(self.chunk_texts)} chunks from {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error creating indices: {e}")
            self._create_empty_indices()
    
    def _create_empty_indices(self):
        """Create empty indices as fallback"""
        dimension = 1536  # OpenAI embedding dimension
        self.faiss_index = faiss.IndexFlatIP(dimension)
        self.bm25_index = None
        self.chunk_texts = []
        self.chunk_metadata = []
        logger.warning("Created empty indices")
    
    def _save_indices(self):
        """Save indices to disk"""
        if not self.faiss_index or not self.chunk_texts:
            logger.warning("No indices to save")
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
    
    def search(self, query: str, department: str = None, top_k: int = 50) -> List[Dict[str, Any]]:
        """Perform hybrid search"""
        if not self.chunk_texts or len(self.chunk_texts) == 0:
            logger.warning("No chunks available for search")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        # Expand search for better coverage
        search_top_k = min(top_k * 2, 200)
        
        # Dense search (FAISS)
        dense_results = []
        if self.embedding_model and self.faiss_index is not None and self.faiss_index.ntotal > 0:
            try:
                query_embedding = self.embedding_model.embed_query(query)
                query_embedding = np.array([query_embedding]).astype('float32')
                faiss.normalize_L2(query_embedding)
                
                dense_scores, dense_indices = self.faiss_index.search(query_embedding, search_top_k)
                
                for score, idx in zip(dense_scores[0], dense_indices[0]):
                    if idx < len(self.chunk_texts):
                        # Filter by department if specified
                        if department and self.chunk_metadata[idx].get('department') != department:
                            continue
                        
                        dense_results.append({
                            "chunk_id": idx,
                            "text": self.chunk_texts[idx],
                            "metadata": self.chunk_metadata[idx],
                            "score": float(score),
                            "type": "dense"
                        })
            except Exception as e:
                logger.error(f"Error in dense search: {e}")
        
        # Sparse search (BM25)
        sparse_results = []
        if BM25_AVAILABLE and len(self.chunk_texts) > 0 and self.bm25_index is not None:
            try:
                tokenized_query = query.lower().split()
                expanded_query = tokenized_query + [word for word in tokenized_query if len(word) > 3]
                
                bm25_scores = self.bm25_index.get_scores(expanded_query)
                sparse_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:search_top_k]
                
                for idx in sparse_indices:
                    if BM25_AVAILABLE and bm25_scores[idx] > 0.1:
                        # Filter by department if specified
                        if department and self.chunk_metadata[idx].get('department') != department:
                            continue
                        
                        sparse_results.append({
                            "chunk_id": idx,
                            "text": self.chunk_texts[idx],
                            "metadata": self.chunk_metadata[idx],
                            "score": float(bm25_scores[idx]),
                            "type": "sparse"
                        })
            except Exception as e:
                logger.error(f"Error in BM25 search: {e}")
        
        # Combine and deduplicate results
        combined_results = self._merge_results(dense_results, sparse_results)
        
        # Apply re-ranking if available
        if self.reranker and combined_results:
            combined_results = self.rerank_results(query, combined_results, top_k)
        
        # Apply MMR for diversity
        if len(combined_results) > top_k:
            combined_results = self.apply_mmr(combined_results, top_k=top_k)
        
        return combined_results[:top_k]
    
    def _merge_results(self, dense_results: List[Dict], sparse_results: List[Dict]) -> List[Dict]:
        """Merge dense and sparse search results"""
        # Create a dictionary to store combined results
        combined = {}
        
        # Add dense results
        for result in dense_results:
            chunk_id = result["chunk_id"]
            if chunk_id not in combined:
                combined[chunk_id] = result.copy()
                combined[chunk_id]["dense_score"] = result["score"]
                combined[chunk_id]["sparse_score"] = 0.0
            else:
                combined[chunk_id]["dense_score"] = result["score"]
        
        # Add sparse results
        for result in sparse_results:
            chunk_id = result["chunk_id"]
            if chunk_id not in combined:
                combined[chunk_id] = result.copy()
                combined[chunk_id]["dense_score"] = 0.0
                combined[chunk_id]["sparse_score"] = result["score"]
            else:
                combined[chunk_id]["sparse_score"] = result["score"]
        
        # Calculate combined scores
        for result in combined.values():
            # Normalize scores (assuming they're in [0, 1])
            dense_score = result["dense_score"]
            sparse_score = result["sparse_score"]
            
            # Weighted combination (adjust weights as needed)
            combined_score = 0.7 * dense_score + 0.3 * sparse_score
            result["score"] = combined_score
        
        # Sort by combined score
        return sorted(combined.values(), key=lambda x: x["score"], reverse=True)
    
    def rerank_results(self, query: str, results: List[Dict], top_n: int = 10) -> List[Dict]:
        """Re-rank results using cross-encoder"""
        if not self.reranker or not results:
            return results
        
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
            return results[:top_n]
    
    def apply_mmr(self, results: List[Dict], lambda_param: float = 0.7, top_k: int = 10) -> List[Dict]:
        """Apply Maximal Marginal Relevance for diversity"""
        if len(results) <= top_k or not results:
            return results
        
        if not self.embedding_model:
            return results[:top_k]
        
        try:
            texts = [result["text"] for result in results]
            embeddings = self.embedding_model.embed_documents(texts)
            embeddings = np.array(embeddings)
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms
            
            # MMR algorithm
            selected = []
            remaining = list(range(len(results)))
            
            # Select first result (highest score)
            selected.append(remaining.pop(0))
            
            while len(selected) < top_k and remaining:
                best_idx = None
                best_score = -1
                
                for idx in remaining:
                    # Relevance score (original score)
                    relevance = results[idx]["score"]
                    
                    # Max similarity to already selected
                    max_sim = 0
                    for sel_idx in selected:
                        sim = np.dot(embeddings[idx], embeddings[sel_idx])
                        max_sim = max(max_sim, sim)
                    
                    # MMR score
                    mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = idx
                
                if best_idx is not None:
                    selected.append(best_idx)
                    remaining.remove(best_idx)
                else:
                    break
            
            return [results[i] for i in selected]
        except Exception as e:
            logger.error(f"Error in MMR: {e}")
            return results[:top_k]

# Global instance
_rag_pipeline = None

def get_rag_pipeline():
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = SimpleRAGPipeline()
    return _rag_pipeline
