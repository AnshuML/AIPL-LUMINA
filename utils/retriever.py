import os
import pickle
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from config import *
from utils.llm_handler import embed_fn as embed_text

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Paths
faiss_path = os.path.join(INDEX_DIR, "faiss_index")
bm25_path = os.path.join(INDEX_DIR, "bm25.pkl")

# Load or build FAISS vector store
if os.path.exists(faiss_path):
    vectordb = FAISS.load_local(faiss_path, embed_text)
    with open(os.path.join(faiss_path, "texts.pkl"), "rb") as f:
        texts = pickle.load(f)
else:
    # If you have a function to load all your policy texts, use it here
    # For example, you might want to process your PDFs and get all chunks
    from utils.pdf_processor import process_pdfs
    pdf_dir = UPLOAD_FOLDER
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    pdf_paths = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    docs = []
    for path in pdf_paths:
        docs.extend(process_pdfs([path]))
    texts = [doc["content"] for doc in docs]
    vectordb = FAISS.from_texts(texts, embed_text)
    vectordb.save_local(faiss_path)
    with open(os.path.join(faiss_path, "texts.pkl"), "wb") as f:
        pickle.dump(texts, f)

# Build or load BM25 index
if os.path.exists(bm25_path):
    with open(bm25_path, "rb") as f:
        bm25 = pickle.load(f)
else:
    tokenized_corpus = [text.split(" ") for text in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25, f)

def hybrid_search(query, top_k=7):
    """Hybrid search: semantic (FAISS) + keyword (BM25)"""
    # Semantic search
    dense_results = vectordb.similarity_search(query, k=top_k * 2)
    dense_texts = [r.page_content for r in dense_results]

    # Keyword search
    tokenized_query = query.lower().split(" ")
    bm_scores = bm25.get_scores(tokenized_query)
    bm_top_idx = sorted(range(len(bm_scores)), key=lambda i: bm_scores[i], reverse=True)[:top_k]
    sparse_texts = [texts[i] for i in bm_top_idx]

    # Combine, deduplicate, and prioritize
    combined_texts = list(dict.fromkeys(dense_texts + sparse_texts))  # preserves order, removes duplicates
    return combined_texts[:top_k]