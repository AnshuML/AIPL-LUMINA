import os
from dotenv import load_dotenv
load_dotenv()

# Gemini Configuration
# Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Now loaded from .env

# Paths
DATA_DIR = "data"
INDEX_DIR = "index"
UPLOAD_FOLDER = os.path.join(DATA_DIR, "pdfs")
CHROMA_PERSIST_DIR = os.path.join(INDEX_DIR, "chroma_db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Embedding Model
model="models/embedding-001"
