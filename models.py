from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hr_chatbot.db")

# For cloud deployment, use in-memory database if file database fails
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Warning: Could not create database engine with {DATABASE_URL}: {e}")
    # Fallback to in-memory database
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_database():
    """Initialize the database and create tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)  # For password authentication
    department = Column(String, nullable=True)  # Selected department
    preferred_language = Column(String, default="en")
    role = Column(String, default="user")  # user, admin, editor, viewer
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    queries = relationship("Query", back_populates="user")
    admin_actions = relationship("AdminAction", back_populates="admin")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    department = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_user = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    language = Column(String, default="en")
    is_processed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    last_indexed = Column(DateTime, nullable=True)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)  # Store additional metadata
    embedding_id = Column(String, nullable=True)  # Reference to FAISS index
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    department = Column(String, nullable=False)
    language = Column(String, default="en")
    responder = Column(String, default="AI")  # AI or human
    model_used = Column(String, nullable=True)
    confidence_score = Column(String, nullable=True)  # low/medium/high
    response_time = Column(Float, nullable=True)  # in seconds
    chunk_ids = Column(JSON, nullable=True)  # List of retrieved chunk IDs
    sources = Column(JSON, nullable=True)  # Source documents with snippets
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="queries")

class AdminAction(Base):
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String, nullable=False)  # upload, delete, reindex, user_create, etc.
    target_type = Column(String, nullable=True)  # document, user, etc.
    target_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)  # Additional action details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = relationship("User", back_populates="admin_actions")

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    priority = Column(String, default="medium")  # low, medium, high, urgent
    assigned_to = Column(String, nullable=True)  # Admin email
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String, nullable=True)

# Create all tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
