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
        """Create necessary directories with enhanced structure"""
        try:
            # Create main directories
            for directory in [cls.DOCUMENTS_DIR, cls.LOGS_DIR, cls.INDEX_DIR]:
                os.makedirs(directory, exist_ok=True)
                
                # Create department subdirectories
                for dept in cls.DEPARTMENTS:
                    dept_dir = os.path.join(directory, dept)
                    os.makedirs(dept_dir, exist_ok=True)
                    
                    # Create log type subdirectories in each department
                    if directory == cls.LOGS_DIR:
                        # Create a 'general' directory for non-department specific logs
                        general_dir = os.path.join(directory, 'general')
                        os.makedirs(general_dir, exist_ok=True)
                        
                        # Create archive directory for rotated logs
                        archive_dir = os.path.join(dept_dir, 'archive')
                        os.makedirs(archive_dir, exist_ok=True)
                        
                        # Create directories for different log types
                        log_types = ['queries', 'uploads', 'user_logins', 'errors', 'system']
                        for log_type in log_types:
                            log_type_dir = os.path.join(dept_dir, log_type)
                            os.makedirs(log_type_dir, exist_ok=True)
            
            print("✅ Directory setup completed successfully")
            
        except Exception as e:
            print(f"Error: Could not create directories: {e}")
            import traceback
            traceback.print_exc()
    
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
        """Enhanced log activity to JSON file with better organization"""
        try:
            # Ensure logs directory exists with department subdirectories
            os.makedirs(cls.LOGS_DIR, exist_ok=True)
            for dept in cls.DEPARTMENTS:
                os.makedirs(os.path.join(cls.LOGS_DIR, dept), exist_ok=True)
            
            # Determine department from data or use 'general'
            department = data.get('department', 'general').upper()
            if department not in cls.DEPARTMENTS:
                department = 'general'
            
            # Create department-specific log file
            log_dir = os.path.join(cls.LOGS_DIR, department)
            log_file = os.path.join(log_dir, f"{activity_type}.json")
            
            # Add additional metadata
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "department": department,
                "user_ip": data.get('user_ip', 'unknown'),
                "session_id": data.get('session_id', 'unknown'),
                "data": data
            }
            
            # Load existing logs
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception as load_error:
                    print(f"Warning: Error loading existing logs: {load_error}")
            
            # Add new log entry
            logs.append(log_entry)
            
            # Save logs with daily rotation
            today = datetime.now().strftime('%Y-%m-%d')
            rotated_log_file = os.path.join(log_dir, f"{activity_type}_{today}.json")
            
            with open(rotated_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            # Update latest log file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs[-1000:], f, indent=2, ensure_ascii=False)  # Keep last 1000 entries in current file
            
        except Exception as e:
            print(f"Error: Could not log activity: {e}")
            import traceback
            traceback.print_exc()
    
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
