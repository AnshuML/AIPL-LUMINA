"""
Simple configuration without database dependency
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

class SimpleConfig:
    """Simple configuration for file-based system"""
    
    # Directories
    DOCUMENTS_DIR = "documents"
    LOGS_DIR = "logs"
    INDEX_DIR = "index"
    
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
    
    # RAG Pipeline configuration
    RAG_CONFIG = {
        "embedding_model": "text-embedding-3-large",
        "chunk_size": 400,
        "chunk_overlap": 80,
        "faiss_path": "index/faiss_index",
        "bm25_path": "index/bm25.pkl"
    }
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        for directory in [cls.DOCUMENTS_DIR, cls.LOGS_DIR, cls.INDEX_DIR]:
            try:
                os.makedirs(directory, exist_ok=True)
                # Create department subdirectories
                for dept in cls.DEPARTMENTS:
                    dept_dir = os.path.join(directory, dept)
                    os.makedirs(dept_dir, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")
                # Continue with other directories
    
    @classmethod
    def get_documents(cls, department: str = None) -> List[Dict]:
        """Get list of documents"""
        documents = []
        if department:
            dept_dir = os.path.join(cls.DOCUMENTS_DIR, department)
            if os.path.exists(dept_dir):
                for filename in os.listdir(dept_dir):
                    if filename.endswith('.pdf'):
                        filepath = os.path.join(dept_dir, filename)
                        documents.append({
                            "filename": filename,
                            "department": department,
                            "filepath": filepath,
                            "size": os.path.getsize(filepath),
                            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        })
        else:
            for dept in cls.DEPARTMENTS:
                dept_dir = os.path.join(cls.DOCUMENTS_DIR, dept)
                if os.path.exists(dept_dir):
                    for filename in os.listdir(dept_dir):
                        if filename.endswith('.pdf'):
                            filepath = os.path.join(dept_dir, filename)
                            documents.append({
                                "filename": filename,
                                "department": dept,
                                "filepath": filepath,
                                "size": os.path.getsize(filepath),
                                "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                            })
        return documents
    
    @classmethod
    def log_activity(cls, activity_type: str, data: Dict):
        """Log activity to JSON file"""
        try:
            # Ensure logs directory exists
            os.makedirs(cls.LOGS_DIR, exist_ok=True)
            
            log_file = os.path.join(cls.LOGS_DIR, f"{activity_type}.json")
            
            # Load existing logs
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # Add new log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            logs.append(log_entry)
            
            # Save logs
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not log activity: {e}")
            # Continue without logging
    
    @classmethod
    def get_logs(cls, activity_type: str, limit: int = 100) -> List[Dict]:
        """Get activity logs"""
        try:
            # Ensure logs directory exists
            os.makedirs(cls.LOGS_DIR, exist_ok=True)
            
            log_file = os.path.join(cls.LOGS_DIR, f"{activity_type}.json")
            
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            return logs[-limit:]  # Return last N entries
        except Exception as e:
            print(f"Warning: Could not get logs: {e}")
            return []

# Global instance
config = SimpleConfig()
