import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Now loaded from .env

DATA_DIR = "data"
INDEX_DIR = "index"
UPLOAD_FOLDER = os.path.join(DATA_DIR, "pdfs")
CHROMA_PERSIST_DIR = os.path.join(INDEX_DIR, "chroma_db")  # Not used for FAISS, but keep for compatibility
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Increased to preserve policy context
    chunk_overlap=200,
    separators=["\n\n", "\n", "•", "●", "- ", "* ", "."]
)

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join([page.extract_text() or "" for page in reader.pages])

def process_pdfs(pdf_paths, department=None):
    all_docs = []
    for path in pdf_paths:
        try:
            text = extract_text_from_pdf(path)
            if not text.strip():
                print(f"Warning: No text extracted from {path}")
                continue
                
            chunks = TEXT_SPLITTER.split_text(text)
            
            # Add metadata for policy type detection
            policy_type = "unknown"
            if "code" in path.lower():
                policy_type = "code"
            elif "leave" in path.lower():
                policy_type = "leave"
            elif "induction" in path.lower():
                policy_type = "induction"
            elif "attendance" in path.lower():
                policy_type = "attendance"
            elif "policy" in path.lower():
                policy_type = "policy"
            
            for chunk in chunks:
                if chunk.strip():  # Only add non-empty chunks
                    all_docs.append({
                        "content": chunk,
                        "metadata": {
                            "source": path,
                            "policy_type": policy_type,
                            "department": department or "unknown"
                        }
                    })
        except Exception as e:
            print(f"Error processing {path}: {e}")
            continue
    return all_docs
    
  
    
