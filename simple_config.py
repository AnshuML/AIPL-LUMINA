"""
Simple configuration without database dependency
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Import streamlit only when available (for cloud deployment)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

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
            # Get the base directory for logs
            base_dir = os.getenv('STREAMLIT_LOG_DIR', cls.LOGS_DIR)
            
            # Ensure logs directory exists with department subdirectories
            try:
                os.makedirs(base_dir, exist_ok=True)
                for dept in cls.DEPARTMENTS:
                    os.makedirs(os.path.join(base_dir, dept), exist_ok=True)
                print(f"✅ Created logs directory structure: {base_dir}")
            except Exception as dir_error:
                print(f"⚠️ Could not create logs directory {base_dir}: {dir_error}")
                # Try alternative directory for cloud deployment
                base_dir = "/tmp/logs" if os.path.exists("/tmp") else "."
                try:
                    os.makedirs(base_dir, exist_ok=True)
                    for dept in cls.DEPARTMENTS:
                        os.makedirs(os.path.join(base_dir, dept), exist_ok=True)
                    print(f"✅ Created alternative logs directory: {base_dir}")
                except Exception as alt_dir_error:
                    print(f"⚠️ Could not create alternative logs directory: {alt_dir_error}")
                    base_dir = "."
            
            # Determine department from data or use 'general'
            department = data.get('department', 'general').upper()
            if department not in cls.DEPARTMENTS:
                department = 'general'
            
            # Create department-specific log file
            log_dir = os.path.join(base_dir, department)
            log_file = os.path.join(log_dir, f"{activity_type}.json")
            
            # Add additional metadata
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "department": department,
                "user_ip": data.get('user_ip', 'unknown'),
                "session_id": data.get('session_id', 'unknown'),
                "platform": "streamlit_cloud" if os.getenv('STREAMLIT_RUNTIME') else "local",
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
            
            # Ensure write permissions
            try:
                # Try to write to rotated log file first
                with open(rotated_log_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
                
                # Update latest log file
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(logs[-1000:], f, indent=2, ensure_ascii=False)  # Keep last 1000 entries
                
                print(f"✅ Successfully logged {activity_type} activity to {log_file}")
                
            except (PermissionError, OSError) as write_error:
                print(f"⚠️ Could not write to log files: {write_error}")
                # If we can't write to file system, store in session state if available
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    if not hasattr(st.session_state, 'temp_logs'):
                        st.session_state.temp_logs = []
                    st.session_state.temp_logs.append(log_entry)
                    print(f"ℹ️ Stored log in session state due to write restrictions")
                else:
                    print(f"ℹ️ Could not store log due to write restrictions and no session state available")
                    # At least print the log entry for debugging
                    print(f"📝 Log entry: {json.dumps(log_entry, indent=2)}")
            
        except Exception as e:
            print(f"Error: Could not log activity: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: at least print the log entry for debugging
            print(f"📝 Fallback log entry: {json.dumps(log_entry, indent=2)}")
    
    @classmethod
    def get_logs(cls, activity_type: str, limit: int = 100, department: str = None) -> List[Dict]:
        """Get activity logs with optional department filter"""
        try:
            # Get the base directory for logs
            base_dir = os.getenv('STREAMLIT_LOG_DIR', cls.LOGS_DIR)
            
            # If department is specified, look in department directory
            if department and department != 'All':
                log_dir = os.path.join(base_dir, department)
            else:
                log_dir = base_dir
            
            # Ensure directory exists
            if not os.path.exists(log_dir):
                return []
            
            log_file = os.path.join(log_dir, f"{activity_type}.json")
            
            # Check session state for temporary logs first
            temp_logs = []
            if STREAMLIT_AVAILABLE and hasattr(st, 'session_state') and hasattr(st.session_state, 'temp_logs'):
                temp_logs = [log for log in st.session_state.temp_logs 
                            if log.get('activity_type') == activity_type]
            
            # Then try to read from file
            file_logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        file_logs = json.load(f)
                    print(f"✅ Loaded {len(file_logs)} logs from {log_file}")
                except Exception as load_error:
                    print(f"⚠️ Error loading logs from file {log_file}: {load_error}")
                    # Try alternative directory
                    alt_log_file = os.path.join(".", f"{activity_type}.json")
                    if os.path.exists(alt_log_file):
                        try:
                            with open(alt_log_file, 'r', encoding='utf-8') as f:
                                file_logs = json.load(f)
                            print(f"✅ Loaded {len(file_logs)} logs from alternative file {alt_log_file}")
                        except Exception as alt_load_error:
                            print(f"⚠️ Error loading logs from alternative file: {alt_load_error}")
            else:
                print(f"ℹ️ Log file does not exist: {log_file}")
            
            # Combine and sort logs by timestamp
            all_logs = temp_logs + file_logs
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return all_logs[:limit]  # Return last N entries
            
        except Exception as e:
            print(f"Warning: Could not get logs: {e}")
            return []
    
    @classmethod
    def export_all_logs(cls, department: str = None) -> Dict[str, List[Dict]]:
        """Export all logs for all activity types"""
        try:
            activity_types = ["queries", "user_logins", "uploads", "errors", "system"]
            all_logs = {}
            
            for activity_type in activity_types:
                logs = cls.get_logs(activity_type, limit=1000, department=department)
                all_logs[activity_type] = logs
            
            return all_logs
            
        except Exception as e:
            print(f"Warning: Could not export logs: {e}")
            return {}

# Global instance
config = SimpleConfig()
