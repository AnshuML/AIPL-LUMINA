import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import io
import base64

from models import get_db, User, Document, DocumentChunk, Query, AdminAction, SupportTicket, SystemConfig
from auth import get_current_admin_user
from rag_pipeline import get_rag_pipeline
from utils.pdf_processor import process_pdfs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AIPL Admin Panel", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()

# Admin panel routes
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Main admin dashboard."""
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": current_user
    })

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Documents management page."""
    return templates.TemplateResponse("documents.html", {
        "request": request,
        "user": current_user
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Logs and audit page."""
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "user": current_user
    })

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Analytics page."""
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": current_user
    })

# API endpoints for documents
@app.get("/api/documents")
async def get_documents(
    department: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all documents with optional filtering."""
    query = db.query(Document)
    
    if department:
        query = query.filter(Document.department == department)
    
    documents = query.offset(skip).limit(limit).all()
    
    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "department": doc.department,
                "file_size": doc.file_size,
                "upload_user": doc.upload_user,
                "upload_date": doc.upload_date.isoformat(),
                "language": doc.language,
                "is_processed": doc.is_processed,
                "chunk_count": doc.chunk_count,
                "last_indexed": doc.last_indexed.isoformat() if doc.last_indexed else None
            }
            for doc in documents
        ]
    }

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    language: str = Form(default="en"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload and process a new document."""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.pptx', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Create upload directory if it doesn't exist
        upload_dir = f"uploads/{department}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        document = Document(
            filename=file.filename,
            original_filename=file.filename,
            department=department,
            file_path=file_path,
            file_size=len(content),
            upload_user=current_user.email,
            language=language
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document
        try:
            # Process PDFs
            if file_extension == '.pdf':
                chunks_data = process_pdfs([file_path])
                
                # Create document chunks
                for i, chunk_data in enumerate(chunks_data):
                    chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=i,
                        content=chunk_data["content"],
                        metadata=chunk_data.get("metadata", {})
                    )
                    db.add(chunk)
                
                # Update document status
                document.is_processed = True
                document.chunk_count = len(chunks_data)
                document.last_indexed = datetime.utcnow()
                db.commit()
                
                # Add to RAG pipeline
                rag_pipeline = get_rag_pipeline()
                chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
                rag_pipeline.add_document(document, chunks)
                
                # Log admin action
                admin_action = AdminAction(
                    admin_id=current_user.id,
                    action_type="upload",
                    target_type="document",
                    target_id=document.id,
                    details={"filename": file.filename, "department": department}
                )
                db.add(admin_action)
                db.commit()
                
                return {"message": "Document uploaded and processed successfully", "document_id": document.id}
            else:
                return {"message": "Document uploaded successfully. Processing for other formats coming soon.", "document_id": document.id}
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {"message": "Document uploaded but processing failed", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Delete document
        db.delete(document)
        
        # Log admin action
        admin_action = AdminAction(
            admin_id=current_user.id,
            action_type="delete",
            target_type="document",
            target_id=document_id,
            details={"filename": document.filename}
        )
        db.add(admin_action)
        db.commit()
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Re-index a document."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Re-process document
        if document.file_path.endswith('.pdf'):
            chunks_data = process_pdfs([document.file_path])
            
            # Delete existing chunks
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            
            # Create new chunks
            for i, chunk_data in enumerate(chunks_data):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_data["content"],
                    metadata=chunk_data.get("metadata", {})
                )
                db.add(chunk)
            
            # Update document status
            document.chunk_count = len(chunks_data)
            document.last_indexed = datetime.utcnow()
            db.commit()
            
            # Re-add to RAG pipeline
            rag_pipeline = get_rag_pipeline()
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
            rag_pipeline.add_document(document, chunks)
            
            # Log admin action
            admin_action = AdminAction(
                admin_id=current_user.id,
                action_type="reindex",
                target_type="document",
                target_id=document_id,
                details={"filename": document.filename}
            )
            db.add(admin_action)
            db.commit()
            
            return {"message": "Document re-indexed successfully"}
        else:
            return {"message": "Re-indexing not supported for this file type"}
    
    except Exception as e:
        logger.error(f"Error re-indexing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoints for logs
@app.get("/api/logs")
async def get_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[str] = None,
    user_email: Optional[str] = None,
    model: Optional[str] = None,
    confidence: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get query logs with filtering."""
    query = db.query(Query)
    
    # Apply filters
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(Query.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(Query.created_at <= end_dt)
    
    if department:
        query = query.filter(Query.department == department)
    
    if user_email:
        query = query.filter(Query.user_id.in_(
            db.query(User.id).filter(User.email.ilike(f"%{user_email}%"))
        ))
    
    if model:
        query = query.filter(Query.model_used == model)
    
    if confidence:
        query = query.filter(Query.confidence_score == confidence)
    
    # Get total count
    total_count = query.count()
    
    # Get paginated results
    logs = query.order_by(desc(Query.created_at)).offset(skip).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_email": db.query(User.email).filter(User.id == log.user_id).scalar(),
                "question_text": log.question_text,
                "answer_text": log.answer_text,
                "department": log.department,
                "language": log.language,
                "responder": log.responder,
                "model_used": log.model_used,
                "confidence_score": log.confidence_score,
                "response_time": log.response_time,
                "chunk_ids": log.chunk_ids,
                "sources": log.sources,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total_count": total_count,
        "has_more": skip + limit < total_count
    }

@app.get("/api/logs/export")
async def export_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[str] = None,
    format: str = "csv",
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export logs to CSV or PDF."""
    try:
        # Get logs with same filtering as get_logs
        query = db.query(Query)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Query.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Query.created_at <= end_dt)
        
        if department:
            query = query.filter(Query.department == department)
        
        logs = query.order_by(desc(Query.created_at)).all()
        
        # Convert to DataFrame
        data = []
        for log in logs:
            user_email = db.query(User.email).filter(User.id == log.user_id).scalar()
            data.append({
                "Timestamp": log.created_at.isoformat(),
                "User Email": user_email,
                "Department": log.department,
                "Question": log.question_text,
                "Answer": log.answer_text,
                "Responder": log.responder,
                "Model Used": log.model_used,
                "Confidence": log.confidence_score,
                "Response Time": log.response_time,
                "Language": log.language
            })
        
        df = pd.DataFrame(data)
        
        if format == "csv":
            # Return CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return JSONResponse(
                content={"csv_data": output.getvalue()},
                headers={"Content-Disposition": "attachment; filename=query_logs.csv"}
            )
        else:
            return {"message": "PDF export not implemented yet"}
    
    except Exception as e:
        logger.error(f"Error exporting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoints for analytics
@app.get("/api/analytics/overview")
async def get_analytics_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get analytics overview data."""
    try:
        # Base query
        query = db.query(Query)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Query.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Query.created_at <= end_dt)
        
        # Total queries
        total_queries = query.count()
        
        # Queries by department
        dept_queries = db.query(
            Query.department,
            func.count(Query.id).label('count')
        ).group_by(Query.department).all()
        
        # Active users
        active_users = db.query(
            func.count(func.distinct(Query.user_id)).label('count')
        ).scalar()
        
        # Average response time
        avg_response_time = db.query(
            func.avg(Query.response_time)
        ).scalar() or 0
        
        # Confidence distribution
        confidence_dist = db.query(
            Query.confidence_score,
            func.count(Query.id).label('count')
        ).group_by(Query.confidence_score).all()
        
        # Language distribution
        language_dist = db.query(
            Query.language,
            func.count(Query.id).label('count')
        ).group_by(Query.language).all()
        
        return {
            "total_queries": total_queries,
            "active_users": active_users,
            "avg_response_time": round(avg_response_time, 2),
            "department_queries": [{"department": d, "count": c} for d, c in dept_queries],
            "confidence_distribution": [{"confidence": c, "count": count} for c, count in confidence_dist],
            "language_distribution": [{"language": l, "count": count} for l, count in language_dist]
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/charts")
async def get_analytics_charts(
    chart_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get chart data for analytics."""
    try:
        # Base query
        query = db.query(Query)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Query.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Query.created_at <= end_dt)
        
        if chart_type == "department_queries":
            # Bar chart: Queries per department
            data = db.query(
                Query.department,
                func.count(Query.id).label('count')
            ).group_by(Query.department).all()
            
            fig = px.bar(
                x=[d for d, c in data],
                y=[c for d, c in data],
                title="Queries per Department",
                labels={"x": "Department", "y": "Number of Queries"}
            )
            
        elif chart_type == "response_time":
            # Bar chart: Average response time by model
            data = db.query(
                Query.model_used,
                func.avg(Query.response_time).label('avg_time')
            ).group_by(Query.model_used).all()
            
            fig = px.bar(
                x=[m for m, t in data],
                y=[t for m, t in data],
                title="Average Response Time by Model",
                labels={"x": "Model", "y": "Average Response Time (seconds)"}
            )
            
        elif chart_type == "confidence_distribution":
            # Pie chart: Confidence distribution
            data = db.query(
                Query.confidence_score,
                func.count(Query.id).label('count')
            ).group_by(Query.confidence_score).all()
            
            fig = px.pie(
                values=[c for conf, c in data],
                names=[conf for conf, c in data],
                title="Confidence Score Distribution"
            )
            
        elif chart_type == "language_distribution":
            # Pie chart: Language distribution
            data = db.query(
                Query.language,
                func.count(Query.id).label('count')
            ).group_by(Query.language).all()
            
            fig = px.pie(
                values=[c for l, c in data],
                names=[l for l, c in data],
                title="Language Distribution"
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid chart type")
        
        # Convert to JSON
        chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        return {"chart_data": chart_json}
    
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System configuration endpoints
@app.get("/api/config")
async def get_system_config(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system configuration."""
    configs = db.query(SystemConfig).all()
    return {config.key: config.value for config in configs}

@app.post("/api/config")
async def update_system_config(
    config_data: Dict[str, str],
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update system configuration."""
    try:
        for key, value in config_data.items():
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                config.value = value
                config.updated_at = datetime.utcnow()
                config.updated_by = current_user.email
            else:
                config = SystemConfig(
                    key=key,
                    value=value,
                    updated_by=current_user.email
                )
                db.add(config)
        
        db.commit()
        return {"message": "Configuration updated successfully"}
    
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
