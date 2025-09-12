"""
Shared Data Manager for AIPL Chatbot
This ensures data consistency between app.py and admin_app.py
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import get_db, User, Document, Query, AdminAction

class SharedDataManager:
    """Manages shared data between app and admin panel."""
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            db = next(get_db())
            
            # Get total users
            total_users = db.query(User).count()
            
            # Get active users (last 7 days)
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            active_users = db.query(User).filter(User.last_login >= cutoff_date).count()
            
            # Get department distribution
            dept_users = db.query(User.department, func.count(User.id)).group_by(User.department).all()
            dept_distribution = {dept: count for dept, count in dept_users if dept}
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "department_distribution": dept_distribution,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "department_distribution": {},
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        try:
            db = next(get_db())
            
            # Get total queries
            total_queries = db.query(Query).count()
            
            # Get queries from last 7 days
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            recent_queries = db.query(Query).filter(Query.created_at >= cutoff_date).count()
            
            # Get department distribution
            dept_queries = db.query(Query.department, func.count(Query.id)).group_by(Query.department).all()
            dept_distribution = {dept: count for dept, count in dept_queries if dept}
            
            # Get confidence distribution
            confidence_queries = db.query(Query.confidence, func.count(Query.id)).group_by(Query.confidence).all()
            confidence_distribution = {conf: count for conf, count in confidence_queries if conf}
            
            return {
                "total_queries": total_queries,
                "recent_queries": recent_queries,
                "department_distribution": dept_distribution,
                "confidence_distribution": confidence_distribution,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting query stats: {e}")
            return {
                "total_queries": 0,
                "recent_queries": 0,
                "department_distribution": {},
                "confidence_distribution": {},
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        try:
            db = next(get_db())
            
            # Get total documents
            total_documents = db.query(Document).count()
            
            # Get processed documents
            processed_documents = db.query(Document).filter(Document.is_processed == True).count()
            
            # Get department distribution
            dept_docs = db.query(Document.department, func.count(Document.id)).group_by(Document.department).all()
            dept_distribution = {dept: count for dept, count in dept_docs if dept}
            
            # Get total chunks
            total_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0
            
            return {
                "total_documents": total_documents,
                "processed_documents": processed_documents,
                "department_distribution": dept_distribution,
                "total_chunks": total_chunks,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {
                "total_documents": 0,
                "processed_documents": 0,
                "department_distribution": {},
                "total_chunks": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent queries."""
        try:
            db = next(get_db())
            queries = db.query(Query).order_by(Query.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": query.id,
                    "user_email": query.user.email if query.user else "Unknown",
                    "question": query.question,
                    "answer": query.answer,
                    "department": query.department,
                    "language": query.language,
                    "confidence": query.confidence,
                    "created_at": query.created_at.isoformat(),
                    "response_time": query.response_time
                }
                for query in queries
            ]
        except Exception as e:
            print(f"Error getting recent queries: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            # Check database connection
            db = next(get_db())
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check RAG pipeline
        try:
            from rag_pipeline import get_rag_pipeline
            rag_pipeline = get_rag_pipeline()
            rag_status = "healthy" if rag_pipeline.chunk_texts else "no_data"
        except Exception as e:
            rag_status = f"error: {str(e)}"
        
        # Check OpenAI API
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            # Simple test - just check if key is set
            api_status = "healthy" if os.getenv("OPENAI_API_KEY") else "no_key"
        except Exception as e:
            api_status = f"error: {str(e)}"
        
        return {
            "database": db_status,
            "rag_pipeline": rag_status,
            "openai_api": api_status,
            "last_checked": datetime.utcnow().isoformat()
        }
    
    def refresh_cache(self):
        """Refresh all cached data."""
        self.cache = {
            "user_stats": self.get_user_stats(),
            "query_stats": self.get_query_stats(),
            "document_stats": self.get_document_stats(),
            "system_health": self.get_system_health()
        }
        self.last_update = datetime.utcnow()
    
    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and not stale."""
        if not self.cache or not self.last_update:
            self.refresh_cache()
        
        # Check if cache is stale (older than 5 minutes)
        if (datetime.utcnow() - self.last_update).seconds > 300:
            self.refresh_cache()
        
        return self.cache.get(key)

# Global instance
shared_data_manager = SharedDataManager()
