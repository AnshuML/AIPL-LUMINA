"""
Comprehensive logging utility for AIPL Chatbot
Captures all user activities, queries, and system events
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models import User, Query, AdminAction, get_db

class ActivityLogger:
    """Centralized logging system for all user activities"""
    
    def __init__(self):
        # Check if we're on Streamlit Cloud
        if os.path.exists('/mount/src'):
            # On Streamlit Cloud - disable all logging
            self.logger = None
            print("🌐 Streamlit Cloud detected - logging disabled")
        else:
            # Local development - enable logging
            self.setup_logging()
    
    def setup_logging(self):
        """Setup file and console logging"""
        # Setup handlers - console only for Streamlit Cloud compatibility
        handlers = [logging.StreamHandler()]
        
        # Only try file logging in local development
        # Streamlit Cloud has restricted file system access
        try:
            # Check if we're in a local environment (not Streamlit Cloud)
            # Streamlit Cloud has /mount/src directory, local doesn't
            if not os.path.exists('/mount/src'):
                # Create logs directory if it doesn't exist
                os.makedirs('logs', exist_ok=True)
                # Test if we can write to the logs directory
                test_file = 'logs/test_write.tmp'
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                # If we get here, we can write to logs directory
                handlers.append(logging.FileHandler('logs/activity.log'))
                print("✅ File logging enabled for local development")
            else:
                print("🌐 Streamlit Cloud detected - using console logging only")
        except (OSError, PermissionError, FileNotFoundError) as e:
            # If we can't write to logs directory, just use console logging
            print(f"⚠️ File logging disabled: {e}")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
    
    def log_user_login(self, email: str, department: str, language: str, ip_address: str = None):
        """Log user login activity"""
        # Skip logging on Streamlit Cloud
        if not self.logger:
            return
            
        try:
            db = next(get_db())
            try:
                # Get or create user
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    user = User(
                        email=email,
                        username=email.split('@')[0],
                        department=department,
                        preferred_language=language,
                        last_login=datetime.utcnow()
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    self.logger.info(f"New user created: {email}")
                else:
                    # Update last login
                    user.last_login = datetime.utcnow()
                    user.department = department
                    user.preferred_language = language
                    db.commit()
                
                # Log to file
                login_data = {
                    "event": "user_login",
                    "email": email,
                    "department": department,
                    "language": language,
                    "ip_address": ip_address,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.info(f"User login: {json.dumps(login_data)}")
                
                return user
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Error logging user login: {e}")
            return None
    
    def log_query(self, user_id: int, question: str, answer: str, department: str, 
                  language: str, response_data: Dict[str, Any]):
        """Log user query with complete metadata"""
        # Skip logging on Streamlit Cloud
        if not self.logger:
            return
            
        try:
            db = next(get_db())
            try:
                query_log = Query(
                    user_id=user_id,
                    question_text=question,
                    answer_text=answer,
                    department=department,
                    language=language,
                    responder="AI",
                    model_used=response_data.get('model_used', 'gpt-4'),
                    confidence_score=response_data.get('confidence', 'low'),
                    response_time=response_data.get('response_time', 0),
                    chunk_ids=response_data.get('chunk_ids', []),
                    sources=response_data.get('sources', [])
                )
                db.add(query_log)
                db.commit()
                
                # Log to file
                query_data = {
                    "event": "user_query",
                    "user_id": user_id,
                    "question": question,
                    "answer_length": len(answer),
                    "department": department,
                    "language": language,
                    "confidence": response_data.get('confidence', 'low'),
                    "response_time": response_data.get('response_time', 0),
                    "model_used": response_data.get('model_used', 'gpt-4'),
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.info(f"User query: {json.dumps(query_data)}")
                
                return query_log
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Error logging query: {e}")
            return None
    
    def log_admin_action(self, admin_email: str, action_type: str, target_type: str = None, 
                        target_id: int = None, details: Dict[str, Any] = None):
        """Log admin actions"""
        # Skip logging on Streamlit Cloud
        if not self.logger:
            return
            
        try:
            db = next(get_db())
            try:
                # Get admin user
                admin = db.query(User).filter(User.email == admin_email).first()
                if not admin:
                    self.logger.error(f"Admin user not found: {admin_email}")
                    return None
                
                admin_action = AdminAction(
                    admin_id=admin.id,
                    action_type=action_type,
                    target_type=target_type,
                    target_id=target_id,
                    details=details or {}
                )
                db.add(admin_action)
                db.commit()
                
                # Log to file
                action_data = {
                    "event": "admin_action",
                    "admin_email": admin_email,
                    "action_type": action_type,
                    "target_type": target_type,
                    "target_id": target_id,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.logger.info(f"Admin action: {json.dumps(action_data)}")
                
                return admin_action
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Error logging admin action: {e}")
            return None
    
    def log_system_event(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log system events"""
        event_data = {
            "event": "system_event",
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(f"System event: {json.dumps(event_data)}")
    
    def get_user_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary for the last N days"""
        try:
            db = next(get_db())
            try:
                from datetime import timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Active users
                active_users = db.query(User).filter(User.last_login >= cutoff_date).count()
                
                # Total queries
                total_queries = db.query(Query).filter(Query.created_at >= cutoff_date).count()
                
                # Department breakdown
                dept_queries = db.query(Query.department, db.func.count(Query.id)).filter(
                    Query.created_at >= cutoff_date
                ).group_by(Query.department).all()
                
                # Top users
                top_users = db.query(User.email, db.func.count(Query.id)).join(
                    Query, User.id == Query.user_id
                ).filter(Query.created_at >= cutoff_date).group_by(
                    User.email
                ).order_by(db.func.count(Query.id).desc()).limit(5).all()
                
                return {
                    "active_users": active_users,
                    "total_queries": total_queries,
                    "department_breakdown": dict(dept_queries),
                    "top_users": [{"email": email, "queries": count} for email, count in top_users],
                    "period_days": days
                }
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Error getting activity summary: {e}")
            return {}

# Global logger instance
activity_logger = ActivityLogger()
