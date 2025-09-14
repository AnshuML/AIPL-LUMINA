"""
Robust configuration with simplified logging system
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
    """Robust configuration with simplified logging system"""
    
    # Directories
    DOCUMENTS_DIR = "documents"
    LOGS_DIR = "logs"
    INDEX_DIR = "index"
    
    # Departments
    DEPARTMENTS = [
        "HR", "IT", "SALES", "MARKETING", 
        "ACCOUNTS", "FACTORY", "CO-ORDINATION", "GENERAL"
    ]
    
    # Languages
    LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "gu": "Gujarati",
        "mr": "Marathi",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi"
    }
    
    @staticmethod
    def sanitize_for_json(obj):
        """Recursively sanitize data to ensure JSON serialization"""
        if isinstance(obj, dict):
            return {key: SimpleConfig.sanitize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [SimpleConfig.sanitize_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        else:
            # Convert any other object to string
            return str(obj)
    
    @classmethod
    def log_activity(cls, activity_type: str, data: Dict[str, Any]) -> None:
        """Simplified, robust log activity to JSON file"""
        try:
            # Get the base directory for logs
            base_dir = os.getenv('STREAMLIT_LOG_DIR', cls.LOGS_DIR)
            
            # Ensure logs directory exists
            try:
                os.makedirs(base_dir, exist_ok=True)
            except Exception as dir_error:
                print(f"⚠️ Could not create logs directory {base_dir}: {dir_error}")
                base_dir = "/tmp/logs" if os.path.exists("/tmp") else "."
                try:
                    os.makedirs(base_dir, exist_ok=True)
                except Exception as alt_dir_error:
                    print(f"⚠️ Could not create alternative logs directory: {alt_dir_error}")
                    base_dir = "."
            
            # Get department from data (normalize to uppercase)
            department = data.get('department', 'GENERAL').upper()
            if department not in cls.DEPARTMENTS:
                department = 'GENERAL'
            
            # Sanitize data to ensure JSON serialization
            sanitized_data = cls.sanitize_for_json(data)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "department": department,
                "user_ip": sanitized_data.get('user_ip', 'unknown'),
                "session_id": sanitized_data.get('session_id', 'unknown'),
                "platform": "streamlit_cloud" if os.getenv('STREAMLIT_RUNTIME') else "local",
                "data": sanitized_data
            }
            
            # Main log file (unified)
            main_log_file = os.path.join(base_dir, f"{activity_type}.json")
            
            # Load existing logs
            logs = []
            if os.path.exists(main_log_file):
                try:
                    with open(main_log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception as load_error:
                    print(f"Warning: Error loading existing logs: {load_error}")
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            logs = logs[-1000:]
            
            # Save logs
            try:
                with open(main_log_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
                print(f"✅ Successfully logged {activity_type} activity to {main_log_file}")
                
            except Exception as write_error:
                print(f"⚠️ Could not write to log file: {write_error}")
                # Fallback: store in session state if available
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    if not hasattr(st.session_state, 'temp_logs'):
                        st.session_state.temp_logs = []
                    st.session_state.temp_logs.append(log_entry)
                    print(f"ℹ️ Stored log in session state due to write restrictions")
            
        except Exception as e:
            print(f"Error: Could not log activity: {e}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    def get_logs(cls, activity_type: str, limit: int = 100, department: str = None) -> List[Dict]:
        """Get activity logs with optional department filter"""
        try:
            # Get the base directory for logs
            base_dir = os.getenv('STREAMLIT_LOG_DIR', cls.LOGS_DIR)
            
            # Main log file
            log_file = os.path.join(base_dir, f"{activity_type}.json")
            
            # Check session state for temporary logs first
            temp_logs = []
            if STREAMLIT_AVAILABLE and hasattr(st, 'session_state') and hasattr(st.session_state, 'temp_logs'):
                temp_logs = [log for log in st.session_state.temp_logs 
                            if log.get('activity_type') == activity_type]
            
            # Load logs from file
            file_logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        file_logs = json.load(f)
                except Exception as load_error:
                    print(f"Warning: Error loading logs from file: {load_error}")
            
            # Combine and sort logs by timestamp
            all_logs = temp_logs + file_logs
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Filter by department if specified
            if department and department != 'All':
                filtered_logs = []
                for log in all_logs:
                    log_dept = log.get('department', '').upper()
                    if log_dept == department.upper():
                        filtered_logs.append(log)
                all_logs = filtered_logs
            
            return all_logs[:limit]  # Return last N entries
            
        except Exception as e:
            print(f"Warning: Could not get logs: {e}")
            return []
    
    @classmethod
    def setup_directories(cls):
        """Setup required directories"""
        try:
            os.makedirs(cls.DOCUMENTS_DIR, exist_ok=True)
            os.makedirs(cls.LOGS_DIR, exist_ok=True)
            os.makedirs(cls.INDEX_DIR, exist_ok=True)
            print("✅ Directory setup completed successfully")
        except Exception as e:
            print(f"❌ Error setting up directories: {e}")
    
    @classmethod
    def get_documents(cls, department: str = None) -> List[Dict]:
        """Get list of documents, optionally filtered by department"""
        documents = []
        
        try:
            if department:
                # Get documents for specific department
                dept_dir = os.path.join(cls.DOCUMENTS_DIR, department)
                if os.path.exists(dept_dir):
                    for filename in os.listdir(dept_dir):
                        if filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
                            filepath = os.path.join(dept_dir, filename)
                            stat = os.stat(filepath)
                            documents.append({
                                'filename': filename,
                                'filepath': filepath,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'department': department
                            })
            else:
                # Get all documents from all departments
                for dept in cls.DEPARTMENTS:
                    dept_docs = cls.get_documents(dept)
                    documents.extend(dept_docs)
            
        except Exception as e:
            print(f"Error getting documents: {e}")
        
        return documents

# Create global instance
config = SimpleConfig()
