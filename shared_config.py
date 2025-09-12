"""
Shared configuration for AIPL Chatbot
This file ensures both app.py and admin_app.py use the same configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Shared configuration
class SharedConfig:
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hr_chatbot.db")
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "aipl-secret-key-2024")
    
    # Application ports
    CHAT_PORT = 8501
    ADMIN_PORT = 8502
    
    # RAG Pipeline configuration
    RAG_CONFIG = {
        "embedding_model": "text-embedding-3-large",
        "chunk_size": 400,
        "chunk_overlap": 80,
        "faiss_path": "index/faiss_index",
        "bm25_path": "index/bm25.pkl"
    }
    
    # Departments
    DEPARTMENTS = [
        "HR", "IT", "SALES", "MARKETING", 
        "ACCOUNTS", "FACTORY", "CO-ORDINATION"
    ]
    
    # Languages
    LANGUAGES = {
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
    
    # Allowed email domains
    ALLOWED_DOMAINS = ["@aiplabro.com", "@ajitindustries.com"]
    
    @classmethod
    def is_valid_email(cls, email):
        """Check if email is from allowed domain."""
        return any(email.endswith(domain) for domain in cls.ALLOWED_DOMAINS)
    
    @classmethod
    def get_rag_config(cls):
        """Get RAG pipeline configuration."""
        return cls.RAG_CONFIG.copy()
    
    @classmethod
    def get_departments(cls):
        """Get list of departments."""
        return cls.DEPARTMENTS.copy()
    
    @classmethod
    def get_languages(cls):
        """Get language mapping."""
        return cls.LANGUAGES.copy()

# Global instance
config = SharedConfig()
