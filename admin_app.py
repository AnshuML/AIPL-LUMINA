import os
import streamlit as st
import requests
from datetime import datetime, timedelta
import json
from typing import Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import io
from datetime import datetime

# Load environment variables
load_dotenv()

# Import our modules
try:
    from models import get_db, User, Document, Query, AdminAction, SupportTicket
    from sqlalchemy.orm import Session
    from sqlalchemy import func, desc, and_
    
    # Conditional logger import - only on local development
    if not os.path.exists('/mount/src'):
        from utils.logger import activity_logger
    else:
        # Create a dummy logger for Streamlit Cloud
        class DummyLogger:
            def log_user_login(self, *args, **kwargs): pass
            def log_query(self, *args, **kwargs): pass
            def log_admin_action(self, *args, **kwargs): pass
        activity_logger = DummyLogger()
    
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False

# Set page config
st.set_page_config(
    page_title="AIPL LUMINA Admin Panel", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Complete Dark Theme CSS for Admin Panel
st.markdown("""
<style>
    /* Root app styling */
    .stApp {
        background-color: #0e1117 !important;
        color: #e2e8f0 !important;
    }
    
    /* Main container */
    .main .block-container {
        background-color: #0e1117 !important;
        color: #e2e8f0 !important;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar complete dark theme */
    .css-1d391kg, .css-1lcbmhc, .css-1v0mbdj {
        background-color: #1a1a1a !important;
    }
    
    /* All text elements with proper font sizes */
    h1 { color: #e2e8f0 !important; font-size: 2rem !important; }
    h2 { color: #e2e8f0 !important; font-size: 1.5rem !important; }
    h3 { color: #e2e8f0 !important; font-size: 1.25rem !important; }
    h4 { color: #e2e8f0 !important; font-size: 1.1rem !important; }
    h5 { color: #e2e8f0 !important; font-size: 1rem !important; }
    h6 { color: #e2e8f0 !important; font-size: 0.9rem !important; }
    p { color: #e2e8f0 !important; font-size: 0.9rem !important; }
    span { color: #e2e8f0 !important; font-size: 0.9rem !important; }
    div { color: #e2e8f0 !important; font-size: 0.9rem !important; }
    
    /* All buttons */
    .stButton > button {
        background-color: #4a5568 !important;
        color: #e2e8f0 !important;
        border: 1px solid #718096 !important;
    }
    
    .stButton > button:hover {
        background-color: #718096 !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Cards and containers */
    .card {
        background-color: #1a202c !important;
        border: 1px solid #4a5568 !important;
        color: #e2e8f0 !important;
    }
    
    /* Tables */
    .stDataFrame {
        background-color: #1a202c !important;
        color: #e2e8f0 !important;
    }
    
    /* Log entries - dark theme */
    .log-entry {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
        color: #e2e8f0 !important;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .log-entry:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    }
    
    .log-entry strong {
        color: #e2e8f0 !important;
        font-weight: 600;
    }
    
    /* Metric cards dark theme */
    .metric-card {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
        color: #e2e8f0 !important;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        border: 1px solid #4a5568;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
    }
    
    .metric-card h3 {
        color: #e2e8f0 !important;
        font-size: 1rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        color: #e2e8f0 !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Streamlit metric styling */
    .stMetric {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stMetric > div {
        color: #e2e8f0 !important;
    }
    
    .stMetric [data-testid="metric-container"] {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Dataframe styling */
    .stDataFrame table {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }
    
    .stDataFrame th {
        background-color: #4a5568 !important;
        color: #e2e8f0 !important;
    }
    
    .stDataFrame td {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4a5568;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #718096;
    }
    
    /* Override any remaining light elements */
    * {
        color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Beautiful Custom CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .metric-card h3 {
        color: #2d3748;
        font-size: 1rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        color: #1a202c;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Upload Area */
    .upload-area {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #e2e8f0;
    }
    
    .upload-area:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        transform: scale(1.02);
    }
    
    .upload-area::before {
        content: '📁';
        font-size: 4rem;
        display: block;
        margin-bottom: 1rem;
        opacity: 0.7;
    }
    
    /* Log Entries */
    .log-entry {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .log-entry:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .log-entry strong {
        color: #2d3748;
        font-weight: 600;
    }
    
    /* Error Messages */
    .error-message {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        color: #742a2a;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #f56565;
        box-shadow: 0 4px 15px rgba(245, 101, 101, 0.2);
    }
    
    .success-message {
        background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
        color: #22543d;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #48bb78;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.2);
    }
    
    /* Sidebar Styles */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f7fafc 0%, #edf2f7 100%);
    }
    
    .sidebar .sidebar-content .block-container {
        padding-top: 2rem;
    }
    
    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        border: 1px solid #e2e8f0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Form Styles */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* File Uploader */
    .stFileUploader > div {
        border-radius: 15px;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
    }
    
    /* Date Input */
    .stDateInput > div > div {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
    }
    
    /* Loading Spinner */
    .stSpinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8, #6b46c1);
    }
</style>
""", unsafe_allow_html=True)

def check_admin_auth():
    """Beautiful admin authentication check"""
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        st.markdown("""
        <div class="main-header">
            <h1>🔐 AIPL LUMINA Admin Panel</h1>
            <p>Secure access to your enterprise dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown("### 🔑 Admin Authentication")
                with st.form("admin_login"):
                    email = st.text_input("📧 Email Address", placeholder="admin@aiplabro.com", help="Enter your admin email")
                    password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                    submit = st.form_submit_button("🚀 Login to Dashboard", use_container_width=True)
                    
                    if submit:
                        if email == "admin@aiplabro.com" and password == "admin123":
                            st.session_state.admin_logged_in = True
                            
                            # Log admin login
                            try:
                                activity_logger.log_admin_action(
                                    admin_email=email,
                                    action_type="admin_login",
                                    details={"login_time": datetime.utcnow().isoformat()}
                                )
                            except Exception as e:
                                # Logging failed, but don't break the login process
                                print(f"Warning: Could not log admin action: {e}")
                            
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials. Please try again.")
        return False
    return True

def get_stats():
    """Get dashboard statistics with error handling"""
    try:
        db = next(get_db())
        try:
            total_users = db.query(User).count()
            total_documents = db.query(Document).count()
            total_queries = db.query(Query).count()
            total_tickets = db.query(SupportTicket).count()
            
            return {
                'users': total_users,
                'documents': total_documents,
                'queries': total_queries,
                'tickets': total_tickets
            }
        finally:
            db.close()
    except Exception as e:
        # Don't show error in sidebar, just return zeros
        return {'users': 0, 'documents': 0, 'queries': 0, 'tickets': 0}

def main():
    if not check_admin_auth():
        return
    
    # Beautiful main header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 AIPL LUMINA Admin Panel</h1>
        <p>Your intelligent enterprise management dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Admin Controls")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        with st.spinner("Loading statistics..."):
            stats = get_stats()
        
        # Beautiful metric display
        st.metric("👥 Total Users", f"{stats['users']:,}", delta=None)
        st.metric("📄 Documents", f"{stats['documents']:,}", delta=None)
        st.metric("💬 Queries", f"{stats['queries']:,}", delta=None)
        st.metric("🎫 Support Tickets", f"{stats['tickets']:,}", delta=None)
        
        st.markdown("---")
        st.markdown("### 🚀 Quick Actions")
        if st.button("📊 Refresh Data", use_container_width=True):
            st.rerun()
        if st.button("📈 View Analytics", use_container_width=True):
            st.info("Navigate to Analytics tab")
    
    # Main content tabs with beautiful styling
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📄 Documents", "📋 Logs", "📈 Analytics"])
    
    with tab1:
        st.header("📊 Dashboard Overview")
        
        # Beautiful metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>👥 Users</h3>
                <h2>{stats['users']:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📄 Documents</h3>
                <h2>{stats['documents']:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>💬 Queries</h3>
                <h2>{stats['queries']:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎫 Tickets</h3>
                <h2>{stats['tickets']:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent activity section
        st.subheader("📈 Recent Activity")
        
        try:
            db = next(get_db())
            try:
                recent_queries = db.query(Query).order_by(desc(Query.created_at)).limit(5).all()
                
                if recent_queries:
                    for query in recent_queries:
                        st.markdown(f"""
                        <div class="log-entry">
                            <strong>👤 User:</strong> {query.user_email} | 
                            <strong>🏢 Department:</strong> {query.department} | 
                            <strong>⏰ Time:</strong> {query.created_at.strftime('%Y-%m-%d %H:%M')}
                            <br><strong>💬 Query:</strong> {query.query_text[:100]}...
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("📭 No recent queries found")
            finally:
                db.close()
        except Exception as e:
            st.error(f"❌ Error fetching recent activity: {str(e)}")
    
    with tab2:
        st.header("📄 Document Management")
        
        # Beautiful upload section
        st.subheader("📤 Upload Documents")
        
        # Department selection
        st.markdown("### 🏢 Select Department")
        department_options = ["HR", "IT", "SALES", "MARKETING", "ACCOUNTS", "FACTORY", "CO-ORDINATION", "GENERAL"]
        selected_department = st.selectbox(
            "Choose department for file upload:",
            department_options,
            help="Select the department this document belongs to"
        )
        
        st.markdown("---")
        
        st.markdown("### 📁 File Upload")
        st.markdown("""
        <div class="upload-area">
            <h3>📁 Drag & Drop PDF Files Here</h3>
            <p>Or use the file picker below to upload your documents to <strong>{}</strong> department</p>
        </div>
        """.format(selected_department), unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help=f"Select a PDF file to upload to {selected_department} department")
        
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🚀 Upload and Process", use_container_width=True):
                    try:
                        # Create department-specific upload directory
                        dept_upload_dir = f"uploads/{selected_department}"
                        os.makedirs(dept_upload_dir, exist_ok=True)
                        
                        # Save file to department folder
                        file_path = f"uploads/{selected_department}/{uploaded_file.name}"
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Save to database
                        db = next(get_db())
                        try:
                            new_document = Document(
                                filename=uploaded_file.name,
                                original_filename=uploaded_file.name,
                                file_path=file_path,
                                file_size=uploaded_file.size,
                                department=selected_department,
                                upload_user="admin@aiplabro.com",
                                upload_date=datetime.now(),
                                is_processed=False
                            )
                            db.add(new_document)
                            db.commit()
                        finally:
                            db.close()
                        
                        # Process document with RAG pipeline
                        try:
                            from rag_pipeline import get_rag_pipeline
                            from utils.pdf_processor import process_pdfs
                            from models import DocumentChunk
                            
                            # Process the PDF
                            processed_docs = process_pdfs([file_path])
                            texts = [doc_data["content"] for doc_data in processed_docs]
                            
                            # Create document chunks in database
                            db = next(get_db())
                            try:
                                db_doc = db.query(Document).filter(Document.id == new_document.id).first()
                                if db_doc:
                                    # Create chunks in database
                                    for i, text in enumerate(texts):
                                        chunk = DocumentChunk(
                                            document_id=db_doc.id,
                                            chunk_index=i,
                                            content=text,
                                            chunk_metadata={
                                                "filename": uploaded_file.name,
                                                "department": selected_department,
                                                "file_path": file_path,
                                                "upload_date": datetime.now().isoformat()
                                            }
                                        )
                                        db.add(chunk)
                                    
                                    # Update document as processed
                                    db_doc.is_processed = True
                                    db_doc.chunk_count = len(texts)
                                    db_doc.last_indexed = datetime.now()
                                    db.commit()
                                    
                                    # Add to RAG pipeline
                                    rag_pipeline = get_rag_pipeline()
                                    rag_pipeline.add_documents(
                                        texts=texts,
                                        metadata=[{
                                            "filename": uploaded_file.name,
                                            "department": selected_department,
                                            "file_path": file_path,
                                            "upload_date": datetime.now().isoformat()
                                        }] * len(texts)
                                    )
                            finally:
                                db.close()
                            
                            st.success(f"✅ File {uploaded_file.name} uploaded and processed for {selected_department} department!")
                            st.info("🔄 Document is now searchable in the chatbot!")
                            
                        except Exception as e:
                            st.warning(f"⚠️ File uploaded but processing failed: {str(e)}")
                            st.info("🔄 Document will be processed later")
                        
                        st.rerun()  # Refresh to show updated document list
                        
                    except Exception as e:
                        import traceback
                        st.error(f"❌ Error uploading file: {str(e)}")
                        st.error(f"Full error: {traceback.format_exc()}")
            
            with col2:
                st.info(f"📄 **File Details:**\n- **Name:** {uploaded_file.name}\n- **Size:** {uploaded_file.size:,} bytes\n- **Type:** PDF")
        
        # Document list
        st.subheader("📋 Uploaded Documents")
        
        # Department filter for documents
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_department = st.selectbox(
                "Filter by department:",
                ["All"] + department_options,
                help="Filter documents by department"
            )
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Add reprocess button
        if st.button("🔄 Reprocess All Documents", use_container_width=True):
            try:
                from rag_pipeline import get_rag_pipeline
                from utils.pdf_processor import process_pdfs
                from models import DocumentChunk
                
                db = next(get_db())
                try:
                    unprocessed_docs = db.query(Document).filter(Document.is_processed == False).all()
                    
                    if unprocessed_docs:
                        rag_pipeline = get_rag_pipeline()
                        processed_count = 0
                        
                        for doc in unprocessed_docs:
                            try:
                                # Process the PDF
                                processed_docs = process_pdfs([doc.file_path])
                                texts = [doc_data["content"] for doc_data in processed_docs]
                                
                                # Create document chunks in database
                                for i, text in enumerate(texts):
                                    chunk = DocumentChunk(
                                        document_id=doc.id,
                                        chunk_index=i,
                                        content=text,
                                        chunk_metadata={
                                            "filename": doc.original_filename,
                                            "department": doc.department,
                                            "file_path": doc.file_path,
                                            "upload_date": doc.upload_date.isoformat()
                                        }
                                    )
                                    db.add(chunk)
                                
                                # Add to RAG pipeline
                                rag_pipeline.add_documents(
                                    texts=texts,
                                    metadata=[{
                                        "filename": doc.original_filename,
                                        "department": doc.department,
                                        "file_path": doc.file_path,
                                        "upload_date": doc.upload_date.isoformat()
                                    }] * len(texts)
                                )
                                
                                # Update document as processed
                                doc.is_processed = True
                                doc.chunk_count = len(texts)
                                doc.last_indexed = datetime.now()
                                processed_count += 1
                                
                            except Exception as e:
                                st.warning(f"⚠️ Failed to process {doc.original_filename}: {str(e)}")
                        
                        db.commit()
                        st.success(f"✅ Processed {processed_count} documents! They are now searchable in the chatbot.")
                        
                    else:
                        st.info("📭 No unprocessed documents found")
                        
                finally:
                    db.close()
                    
            except Exception as e:
                st.error(f"❌ Error reprocessing documents: {str(e)}")
        
        try:
            db = next(get_db())
            try:
                if filter_department == "All":
                    documents = db.query(Document).order_by(desc(Document.upload_date)).all()
                else:
                    documents = db.query(Document).filter(Document.department == filter_department).order_by(desc(Document.upload_date)).all()
                
                if documents:
                    st.markdown(f"**📊 Total Documents: {len(documents)}**")
                    if filter_department != "All":
                        st.markdown(f"**🏢 Department: {filter_department}**")
                    st.markdown("---")
                    
                    for doc in documents:
                        col1, col2, col3 = st.columns([4, 1, 1])
                        
                        with col1:
                            # Department color mapping
                            dept_colors = {
                                "HR": "#667eea",
                                "IT": "#764ba2", 
                                "SALES": "#f093fb",
                                "MARKETING": "#f5576c",
                                "ACCOUNTS": "#4facfe",
                                "FACTORY": "#43e97b",
                                "CO-ORDINATION": "#fa709a",
                                "GENERAL": "#667eea"
                            }
                            dept_color = dept_colors.get(doc.department, "#667eea")
                            
                            st.markdown(f"""
                            <div style="padding: 1rem; background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); border-radius: 10px; border-left: 4px solid {dept_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <h4 style="margin: 0; color: #e2e8f0;">📄 {doc.original_filename}</h4>
                                    <span style="background: {dept_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600;">🏢 {doc.department}</span>
                                </div>
                                <p style="margin: 0; color: #a0aec0;">
                                    📏 Size: {doc.file_size:,} bytes | 
                                    📅 Uploaded: {doc.upload_date.strftime('%Y-%m-%d %H:%M')} |
                                    {'✅ Processed' if doc.is_processed else '⏳ Pending'} |
                                    📄 {doc.chunk_count} chunks
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("📄 View", key=f"view_{doc.id}", help="View document"):
                                st.info("View functionality will be implemented")
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{doc.id}", help="Delete document"):
                                try:
                                    db = next(get_db())
                                    try:
                                        db_doc = db.query(Document).filter(Document.id == doc.id).first()
                                        if db_doc:
                                            db.delete(db_doc)
                                            db.commit()
                                            st.success(f"✅ {doc.original_filename} deleted successfully!")
                                            st.rerun()
                                    finally:
                                        db.close()
                                except Exception as e:
                                    st.error(f"❌ Error deleting document: {str(e)}")
                else:
                    st.markdown("""
                    <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); border-radius: 15px; border: 2px dashed #4a5568;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">📁</div>
                        <h3 style="color: #e2e8f0; margin-bottom: 0.5rem;">No Documents Yet</h3>
                        <p style="color: #a0aec0; margin: 0;">Upload your first PDF document to get started</p>
                    </div>
                    """, unsafe_allow_html=True)
            finally:
                db.close()
        except Exception as e:
            st.info("📭 No documents in database yet")
    
    with tab3:
        st.header("📋 System Logs & Activity")
        
        # Filter options
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            log_type = st.selectbox("📝 Log Type", ["All", "Queries", "User Logins", "Admin Actions"], help="Filter by log type")
        with col2:
            department_filter = st.selectbox("🏢 Department", ["All", "HR", "IT", "SALES", "MARKETING", "ACCOUNTS", "FACTORY"], help="Filter by department")
        with col3:
            date_filter = st.date_input("📅 Date", value=datetime.now().date(), help="Filter by date")
        with col4:
            if st.button("🔍 Apply Filters", use_container_width=True):
                st.info("🔍 Filters applied!")
        with col5:
            if st.button("📊 Export to Excel", use_container_width=True):
                st.info("📊 Preparing Excel export...")
        
        # Show department-specific information
        if department_filter != "All":
            st.info(f"📊 Showing logs for {department_filter} department")
            
            # Department-specific stats
            try:
                db = next(get_db())
                try:
                    dept_queries = db.query(Query).filter(Query.department == department_filter).count()
                    dept_users = db.query(User).filter(User.department == department_filter).count()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"📊 {department_filter} Queries", dept_queries)
                    with col2:
                        st.metric(f"👥 {department_filter} Users", dept_users)
                    with col3:
                        # Recent activity
                        recent_queries = db.query(Query).filter(
                            Query.department == department_filter,
                            Query.created_at >= datetime.now() - timedelta(days=1)
                        ).count()
                        st.metric(f"📈 Last 24h", recent_queries)
                finally:
                    db.close()
            except Exception as e:
                st.error(f"Error loading department stats: {e}")
        
        # Activity Summary
        st.subheader("📊 Activity Summary")
        try:
            summary = activity_logger.get_user_activity_summary(days=7)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🟢 Active Users (7 days)", summary.get('active_users', 0))
            with col2:
                st.metric("💬 Total Queries (7 days)", summary.get('total_queries', 0))
            with col3:
                st.metric("🏢 Departments", len(summary.get('department_breakdown', {})))
            with col4:
                st.metric("👥 Top Users", len(summary.get('top_users', [])))
        except Exception as e:
            st.error(f"Error loading summary: {e}")
        
        # Detailed Logs
        st.subheader("📋 Detailed Activity Logs")
        
        # Query logs
        if log_type in ["All", "Queries"]:
            st.markdown("#### 💬 Query Logs")
            try:
                db = next(get_db())
                try:
                    # Join Query with User to get user email
                    query = db.query(Query, User).join(User, Query.user_id == User.id)
                    
                    # Apply department filter
                    if department_filter != "All":
                        query = query.filter(Query.department == department_filter)
                    
                    # Apply date filter
                    query = query.filter(func.date(Query.created_at) == date_filter)
                    
                    queries = query.order_by(desc(Query.created_at)).limit(20).all()
                    
                    if queries:
                        for query, user in queries:
                            # Format confidence with color
                            confidence_color = {
                                'high': '#4CAF50',
                                'medium': '#FF9800', 
                                'low': '#F44336'
                            }.get(query.confidence_score, '#9E9E9E')
                            
                            st.markdown(f"""
                            <div class="log-entry">
                                <strong>⏰ Time:</strong> {query.created_at.strftime('%Y-%m-%d %H:%M:%S')} | 
                                <strong>👤 User:</strong> {user.email} | 
                                <strong>🏢 Department:</strong> {query.department} |
                                <strong>🌐 Language:</strong> {query.language}
                                <br><strong>💬 Query:</strong> {query.question_text}
                                <br><strong>🤖 Response:</strong> {query.answer_text[:200] if query.answer_text else 'No response'}...
                                <br><strong>📊 Confidence:</strong> <span style="color: {confidence_color};">{query.confidence_score.upper()}</span> | 
                                <strong>⏱️ Response Time:</strong> {query.response_time:.2f}s | 
                                <strong>🤖 Model:</strong> {query.model_used}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("📭 No query logs found")
                finally:
                    db.close()
            except Exception as e:
                st.error(f"❌ Error fetching query logs: {str(e)}")
        
        # User login logs
        if log_type in ["All", "User Logins"]:
            st.markdown("#### 👤 User Login Logs")
            try:
                db = next(get_db())
                try:
                    query = db.query(User.email, User.department, User.last_login, User.preferred_language)
                    
                    # Apply department filter
                    if department_filter != "All":
                        query = query.filter(User.department == department_filter)
                    
                    recent_users = query.order_by(desc(User.last_login)).limit(20).all()
                    
                    if recent_users:
                        for user in recent_users:
                            st.markdown(f"""
                            <div class="log-entry">
                                <strong>⏰ Last Login:</strong> {user.last_login.strftime('%Y-%m-%d %H:%M:%S')} | 
                                <strong>👤 User:</strong> {user.email} | 
                                <strong>🏢 Department:</strong> {user.department or 'Not Selected'} |
                                <strong>🌐 Language:</strong> {user.preferred_language}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("📭 No user login logs found")
                finally:
                    db.close()
            except Exception as e:
                st.error(f"❌ Error fetching user logs: {str(e)}")
        
        # Admin action logs
        if log_type in ["All", "Admin Actions"]:
            st.markdown("#### 🔧 Admin Action Logs")
            try:
                db = next(get_db())
                try:
                    admin_actions = db.query(AdminAction, User).join(User, AdminAction.admin_id == User.id).order_by(desc(AdminAction.created_at)).limit(20).all()
                    
                    if admin_actions:
                        for action, admin in admin_actions:
                            st.markdown(f"""
                            <div class="log-entry">
                                <strong>⏰ Time:</strong> {action.created_at.strftime('%Y-%m-%d %H:%M:%S')} | 
                                <strong>👤 Admin:</strong> {admin.email} | 
                                <strong>🔧 Action:</strong> {action.action_type} |
                                <strong>🎯 Target:</strong> {action.target_type or 'N/A'}
                                <br><strong>📝 Details:</strong> {str(action.details) if action.details else 'No details'}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("📭 No admin action logs found")
                finally:
                    db.close()
            except Exception as e:
                st.error(f"❌ Error fetching admin logs: {str(e)}")
        
        # Excel Export Section
        st.subheader("📊 Export Logs to Excel")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_type = st.selectbox("📝 Export Type", ["All Logs", "Queries Only", "User Logins Only", "Admin Actions Only"], help="Select what to export")
        
        with col2:
            export_days = st.number_input("📅 Last N Days", min_value=1, max_value=365, value=30, help="Number of days to include")
        
        with col3:
            if st.button("📥 Download Excel File", use_container_width=True):
                try:
                    # Get data based on export type
                    db = next(get_db())
                    try:
                        if export_type == "All Logs" or export_type == "Queries Only":
                            # Export queries
                            query_data = db.query(Query, User).join(User, Query.user_id == User.id).order_by(desc(Query.created_at)).limit(1000).all()
                            
                            if query_data:
                                queries_df = pd.DataFrame([{
                                    'Timestamp': query.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                    'User Email': user.email,
                                    'Department': query.department,
                                    'Language': query.language,
                                    'Question': query.question_text,
                                    'Answer': query.answer_text[:500] if query.answer_text else '',
                                    'Confidence': query.confidence_score,
                                    'Response Time (s)': query.response_time,
                                    'Model Used': query.model_used
                                } for query, user in query_data])
                            else:
                                queries_df = pd.DataFrame()
                        
                        if export_type == "All Logs" or export_type == "User Logins Only":
                            # Export user logins
                            users_data = db.query(User).order_by(desc(User.last_login)).limit(1000).all()
                            
                            if users_data:
                                users_df = pd.DataFrame([{
                                    'User Email': user.email,
                                    'Department': user.department or 'Not Set',
                                    'Preferred Language': user.preferred_language,
                                    'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                                    'Created At': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'created_at') and user.created_at else 'Unknown'
                                } for user in users_data])
                            else:
                                users_df = pd.DataFrame()
                        
                        if export_type == "All Logs" or export_type == "Admin Actions Only":
                            # Export admin actions
                            admin_data = db.query(AdminAction, User).join(User, AdminAction.admin_id == User.id).order_by(desc(AdminAction.created_at)).limit(1000).all()
                            
                            if admin_data:
                                admin_df = pd.DataFrame([{
                                    'Timestamp': action.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                    'Admin Email': admin.email,
                                    'Action Type': action.action_type,
                                    'Target Type': action.target_type or 'N/A',
                                    'Details': str(action.details) if action.details else 'No details'
                                } for action, admin in admin_data])
                            else:
                                admin_df = pd.DataFrame()
                        
                        # Create Excel file
                        output = io.BytesIO()
                        
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            if export_type == "All Logs":
                                if not queries_df.empty:
                                    queries_df.to_excel(writer, sheet_name='User Queries', index=False)
                                if not users_df.empty:
                                    users_df.to_excel(writer, sheet_name='User Logins', index=False)
                                if not admin_df.empty:
                                    admin_df.to_excel(writer, sheet_name='Admin Actions', index=False)
                            elif export_type == "Queries Only" and not queries_df.empty:
                                queries_df.to_excel(writer, sheet_name='User Queries', index=False)
                            elif export_type == "User Logins Only" and not users_df.empty:
                                users_df.to_excel(writer, sheet_name='User Logins', index=False)
                            elif export_type == "Admin Actions Only" and not admin_df.empty:
                                admin_df.to_excel(writer, sheet_name='Admin Actions', index=False)
                        
                        output.seek(0)
                        
                        # Download button
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"aipl_logs_{export_type.lower().replace(' ', '_')}_{timestamp}.xlsx"
                        
                        st.download_button(
                            label="📥 Download Excel File",
                            data=output.getvalue(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                        st.success(f"✅ Excel file '{filename}' ready for download!")
                        
                    finally:
                        db.close()
                        
                except Exception as e:
                    st.error(f"❌ Error creating Excel file: {str(e)}")
    
    with tab4:
        st.header("📈 Analytics & Insights")
        
        # Create columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Quick Stats")
            try:
                db = next(get_db())
                try:
                    # Total users
                    total_users = db.query(User).count()
                    st.metric("👥 Total Users", total_users)
                    
                    # Active users (logged in last 7 days)
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    active_users = db.query(User).filter(User.last_login >= week_ago).count()
                    st.metric("🟢 Active Users (7 days)", active_users)
                    
                    # Total queries
                    total_queries = db.query(Query).count()
                    st.metric("💬 Total Queries", total_queries)
                    
                    # Average response time
                    avg_response_time = db.query(func.avg(Query.response_time)).scalar()
                    if avg_response_time:
                        st.metric("⏱️ Avg Response Time", f"{avg_response_time:.2f}s")
                    else:
                        st.metric("⏱️ Avg Response Time", "N/A")
                        
                finally:
                    db.close()
            except Exception as e:
                st.error(f"Error loading stats: {e}")
        
        with col2:
            st.subheader("🎯 Department Distribution")
            try:
                db = next(get_db())
                try:
                    # Department-wise user count
                    dept_users = db.query(User.department, func.count(User.id)).group_by(User.department).all()
                    if dept_users:
                        df_dept = pd.DataFrame(dept_users, columns=['Department', 'Users'])
                        fig_dept = px.pie(df_dept, values='Users', names='Department', 
                                        title='👥 Users by Department')
                        fig_dept.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="Inter", size=12)
                        )
                        st.plotly_chart(fig_dept, use_container_width=True)
                    else:
                        st.info("No department data available")
                finally:
                    db.close()
            except Exception as e:
                st.error(f"Error loading department stats: {e}")
        
        # Full width charts
        st.subheader("📈 Detailed Analytics")
        
        try:
            db = next(get_db())
            try:
                # Department-wise queries
                dept_stats = db.query(Query.department, func.count(Query.id)).group_by(Query.department).all()
                
                if dept_stats:
                    col1, col2 = st.columns(2)
                    with col1:
                        df = pd.DataFrame(dept_stats, columns=['Department', 'Queries'])
                        fig = px.bar(df, x='Department', y='Queries', 
                                   title='📊 Queries by Department',
                                   color='Queries',
                                   color_continuous_scale='viridis')
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="Inter", size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Confidence distribution
                        conf_stats = db.query(Query.confidence_score, func.count(Query.id)).group_by(Query.confidence_score).all()
                        if conf_stats:
                            df_conf = pd.DataFrame(conf_stats, columns=['Confidence', 'Count'])
                            fig_conf = px.pie(df_conf, values='Count', names='Confidence', 
                                            title='📊 Response Confidence Distribution')
                            fig_conf.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="Inter", size=12)
                            )
                            st.plotly_chart(fig_conf, use_container_width=True)
                else:
                    st.info("📊 No department data available yet")
                
                # Daily query trends
                daily_stats = db.query(
                    func.date(Query.created_at).label('date'),
                    func.count(Query.id).label('queries')
                ).group_by(func.date(Query.created_at)).order_by('date').all()
                
                if daily_stats:
                    df_daily = pd.DataFrame(daily_stats, columns=['Date', 'Queries'])
                    fig_daily = px.line(df_daily, x='Date', y='Queries', 
                                      title='📈 Daily Query Trends',
                                      color_discrete_sequence=['#667eea'])
                    fig_daily.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter", size=12)
                    )
                    st.plotly_chart(fig_daily, use_container_width=True)
                else:
                    st.info("📈 No daily trend data available yet")
                
                # User activity with proper join
                user_stats = db.query(User.email, func.count(Query.id)).join(Query, User.id == Query.user_id).group_by(User.email).order_by(desc(func.count(Query.id))).limit(10).all()
                
                if user_stats:
                    df_users = pd.DataFrame(user_stats, columns=['User', 'Queries'])
                    fig_users = px.bar(df_users, x='User', y='Queries', 
                                     title='👥 Top Active Users')
                    fig_users.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter", size=12)
                    )
                    st.plotly_chart(fig_users, use_container_width=True)
                else:
                    st.info("👥 No user activity data available yet")
                    
                # Recent user logins
                st.subheader("🕐 Recent User Activity")
                recent_users = db.query(User.email, User.department, User.last_login).order_by(desc(User.last_login)).limit(10).all()
                if recent_users:
                    df_recent = pd.DataFrame(recent_users, columns=['Email', 'Department', 'Last Login'])
                    st.dataframe(df_recent, use_container_width=True)
                else:
                    st.info("No recent user activity")
                    
            finally:
                db.close()
        except Exception as e:
            st.error(f"❌ Error generating analytics: {str(e)}")

if __name__ == "__main__":
    main()