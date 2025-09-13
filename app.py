import os
import streamlit as st
import requests
from markdown import markdown
from datetime import datetime
import json
from typing import Dict, Any
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up paths for cloud deployment
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cloud deployment optimizations
if os.path.exists('/mount/src'):
    # Streamlit Cloud environment
    os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
    os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    # Disable file logging on cloud
    os.environ.setdefault('DISABLE_FILE_LOGGING', 'true')

# Import shared configuration
from shared_config import config

# Import our enhanced modules
from rag_pipeline import get_rag_pipeline
from utils.llm_handler import llm_handler
from models import get_db, Query, User, Document, DocumentChunk, init_database
from sqlalchemy.orm import Session

# Initialize database
init_database()

# Import logger - works in both local and cloud environments
try:
    from utils.logger import activity_logger
except ImportError:
    # Fallback logger for any import issues
    class FallbackLogger:
        def log_user_login(self, *args, **kwargs): 
            print(f"LOG: User login - {args}, {kwargs}")
        def log_query(self, *args, **kwargs): 
            print(f"LOG: Query - {args}, {kwargs}")
        def log_admin_action(self, *args, **kwargs): 
            print(f"LOG: Admin action - {args}, {kwargs}")
    activity_logger = FallbackLogger()

# Add this function
def render_markdown(text):
    html = markdown(text)
    st.markdown(html, unsafe_allow_html=True)

# Set page config
st.set_page_config(
    page_title="Welcome To AIPL Lumina", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add URL parameter handling for admin panel
query_params = st.query_params
is_admin = query_params.get("admin", "false").lower() == "true"

# Initialize session state FIRST
if "messages" not in st.session_state:
    st.session_state.messages = []
if "department_selected" not in st.session_state:
    st.session_state.department_selected = None
if "language_selected" not in st.session_state:
    st.session_state.language_selected = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False

# Complete Dark Theme CSS
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
    .css-1d391kg {
        background-color: #1a1a1a !important;
    }
    
    .css-1lcbmhc {
        background-color: #1a1a1a !important;
    }
    
    .css-1v0mbdj {
        background-color: #1a1a1a !important;
    }
    
    /* Sidebar text */
    .css-1v0mbdj .css-1v0mbdj {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar headers */
    .css-1v0mbdj h1, .css-1v0mbdj h2, .css-1v0mbdj h3, 
    .css-1v0mbdj h4, .css-1v0mbdj h5, .css-1v0mbdj h6 {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar paragraphs */
    .css-1v0mbdj p {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar buttons */
    .css-1v0mbdj .stButton > button {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    .css-1v0mbdj .stButton > button:hover {
        background-color: #4a5568 !important;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Department tag */
    .department-tag {
        background: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* Confidence colors */
    .confidence-high { color: #4CAF50; font-weight: bold; }
    .confidence-medium { color: #FF9800; font-weight: bold; }
    .confidence-low { color: #F44336; font-weight: bold; }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background: #2d3748;
        color: #e2e8f0;
        margin-left: 20%;
        border: 1px solid #4a5568;
    }
    
    .assistant-message {
        background: #1a202c;
        color: #e2e8f0;
        margin-right: 20%;
        border: 1px solid #4a5568;
    }
    
    /* Chat message containers */
    .stChatMessage {
        background-color: transparent !important;
    }
    
    .stChatMessage > div {
        background-color: transparent !important;
    }
    
    /* All text elements */
    .stMarkdown {
        color: #e2e8f0 !important;
    }
    
    /* Input field - query bar */
    .stTextInput > div > div > input {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #a0aec0 !important;
    }
    
    /* All buttons */
    .stButton > button {
        background-color: #4a5568 !important;
        color: #e2e8f0 !important;
        border: 1px solid #718096 !important;
    }
    
    .stButton > button:hover {
        background-color: #718096 !important;
    }
    
    /* All text elements */
    h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    
    p, span, div {
        color: #e2e8f0 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4a5568 !important;
    }
    
    /* Selectbox dropdown */
    .stSelectbox > div > div > div {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }
    
    /* Chat input container */
    .stChatInput {
        background-color: #1a202c !important;
    }
    
    .stChatInput > div {
        background-color: #1a202c !important;
    }
    
    /* Footer */
    .footer {
        color: #a0aec0 !important;
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
    
    /* Specific overrides for Streamlit elements */
    .css-1d391kg, .css-1v0mbdj, .css-1lcbmhc {
        background-color: #1a1a1a !important;
    }
    
    /* Chat container */
    .stChatMessageContainer {
        background-color: transparent !important;
    }
    
    /* Message bubbles */
    .stChatMessage > div > div {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Department options
DEPARTMENTS = ["HR", "IT", "SALES", "MARKETING", "ACCOUNTS", "FACTORY", "CO-ORDINATION"]

# Language options
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

def debug_rag_pipeline():
    """Debug function to check RAG pipeline status"""
    try:
        rag_pipeline = get_rag_pipeline()
        print(f"🔍 RAG Pipeline Debug:")
        print(f"  - Chunk texts: {len(rag_pipeline.chunk_texts)}")
        print(f"  - Chunk metadata: {len(rag_pipeline.chunk_metadata)}")
        print(f"  - FAISS index: {rag_pipeline.faiss_index.ntotal if rag_pipeline.faiss_index else 'None'}")
        print(f"  - BM25 index: {len(rag_pipeline.chunk_texts) if rag_pipeline.bm25_index else 'None'}")
        print(f"  - Embedding model: {'Available' if rag_pipeline.embedding_model else 'None'}")
        
        # Test search with a meaningful query
        test_results = rag_pipeline.search("leave policy", "HR", 1)
        print(f"  - Test search results: {len(test_results)}")
        
        return True
    except Exception as e:
        print(f"❌ RAG Pipeline Debug Error: {e}")
        return False

def ensure_sample_data():
    """Load documents from admin panel uploads and rebuild RAG pipeline"""
    try:
        # Check if we're in cloud environment
        is_cloud_env = os.path.exists('/mount/src')  # Streamlit Cloud
        
        if is_cloud_env:
            print("🌐 Streamlit Cloud environment detected")
            # Check if documents exist from admin panel
            db = next(get_db())
            doc_count = db.query(Document).count()
            if doc_count > 0:
                print(f"✅ Found {doc_count} existing documents from admin panel")
                # Force RAG pipeline rebuild to ensure latest data is loaded
                try:
                    from rag_pipeline import get_rag_pipeline
                    rag_pipeline = get_rag_pipeline()
                    print(f"🔄 RAG pipeline loaded with {len(rag_pipeline.chunk_texts)} chunks")
                except Exception as e:
                    print(f"⚠️ Error loading RAG pipeline: {e}")
            else:
                print("📋 No documents found - please upload documents via admin panel")
                print("💡 Admin panel: https://your-app-name.streamlit.app/admin")
        
        db = next(get_db())
        try:
            # Check if we have any documents
            doc_count = db.query(Document).count()
            chunk_count = db.query(DocumentChunk).count()
            
            print(f"Found {doc_count} documents with {chunk_count} chunks")
            
            # Always rebuild RAG pipeline with existing documents
            if doc_count > 0 and chunk_count > 0:
                print("Loading documents from admin panel uploads...")
                
                # Get all processed documents
                processed_docs = db.query(Document).filter(Document.is_processed == True).all()
                
                if processed_docs:
                    print(f"Found {len(processed_docs)} processed documents")
                    
                    # Clear existing indices to force rebuild
                    try:
                        if os.path.exists("index/faiss_index"):
                            os.remove("index/faiss_index")
                        if os.path.exists("index/bm25.pkl"):
                            os.remove("index/bm25.pkl")
                        print("Cleared old indices")
                    except Exception as e:
                        print(f"Error clearing indices: {e}")
                    
                    # Rebuild with all existing documents
                    all_texts = []
                    all_metadata = []
                    
                    for doc in processed_docs:
                        print(f"Loading document: {doc.filename} (Department: {doc.department})")
                        
                        # Get chunks for this document
                        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
                        print(f"  Found {len(chunks)} chunks")
                        
                        for chunk in chunks:
                            all_texts.append(chunk.content)
                            all_metadata.append(chunk.chunk_metadata)
                    
                    if all_texts:
                        # Force rebuild RAG pipeline
                        rag_pipeline = get_rag_pipeline()
                        print(f"Successfully loaded {len(all_texts)} chunks from {len(processed_docs)} documents")
                        
                        # Test search to verify it's working
                        test_results = rag_pipeline.search("leave policy", "HR", 1)
                        print(f"Test search results: {len(test_results)}")
                        if test_results:
                            print("✅ RAG pipeline is working correctly")
                        else:
                            print("❌ RAG pipeline search failed")
                    else:
                        print("No chunks found in existing documents")
                else:
                    print("No processed documents found")
            
            # Only create sample data if absolutely no documents exist
            elif doc_count == 0 and chunk_count == 0:
                print("No documents found, creating minimal sample data...")
                
                # Create a minimal sample document
                sample_doc = Document(
                    filename="sample_hr_policies.pdf",
                    original_filename="sample_hr_policies.pdf",
                    department="HR",
                    file_path="sample_hr_policies.pdf",
                    file_size=5000,
                    upload_user="system",
                    upload_date=datetime.utcnow(),
                    language="en",
                    is_processed=True,
                    chunk_count=0
                )
                db.add(sample_doc)
                db.commit()
                db.refresh(sample_doc)
                
                # Create minimal sample chunks
                sample_chunks = [
                    "WELCOME TO HR CHATBOT: This is a sample document. Please contact admin to upload your actual HR documents for accurate answers.",
                    "SAMPLE POLICY: This is placeholder content. Upload real documents to get specific policy information.",
                    "DOCUMENT UPLOAD: Contact admin to upload your company's actual HR policies, procedures, and documents for accurate responses."
                ]
                
                for i, chunk_text in enumerate(sample_chunks):
                    chunk = DocumentChunk(
                        document_id=sample_doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        chunk_metadata={
                            "filename": "sample_hr_policies.pdf",
                            "department": "HR",
                            "file_path": "sample_hr_policies.pdf",
                            "upload_date": datetime.utcnow().isoformat()
                        }
                    )
                    db.add(chunk)
                
                # Update document chunk count
                sample_doc.chunk_count = len(sample_chunks)
                sample_doc.last_indexed = datetime.utcnow()
                
                db.commit()
                
                # Rebuild RAG pipeline with new data
                rag_pipeline = get_rag_pipeline()
                rag_pipeline.add_documents(
                    texts=sample_chunks,
                    metadata=[{
                        "filename": "sample_hr_policies.pdf",
                        "department": "HR",
                        "file_path": "sample_hr_policies.pdf",
                        "upload_date": datetime.utcnow().isoformat()
                    }] * len(sample_chunks)
                )
            else:
                print("Documents exist but no chunks found - this might indicate a processing issue")
                
        finally:
            db.close()
    except Exception as e:
        # If there's an error, just continue - the app should still work
        print(f"Error in ensure_sample_data: {e}")
        import traceback
        traceback.print_exc()
        pass

def show_admin_panel():
    """Show admin panel functionality"""
    try:
        # Import admin functionality
        from admin_app import main as admin_main
        admin_main()
    except Exception as e:
        st.error(f"Error loading admin panel: {e}")
        st.info("Please ensure all admin dependencies are installed.")

def main():
    # Check if admin panel is requested
    if is_admin:
        show_admin_panel()
        return
    
    # Debug RAG pipeline status
    debug_rag_pipeline()
    
    # Ensure sample data exists
    ensure_sample_data()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Welcome To AIPL Lumina</h1>
        <p>Your intelligent companion for company policies and procedures</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for authentication and settings
    with st.sidebar:
        st.header("🔐 Authentication")
        
        # Admin panel link
        if st.button("🔧 Admin Panel", use_container_width=True):
            st.query_params.admin = "true"
            st.rerun()
        
        if not st.session_state.user_authenticated:
            st.markdown("**Please authenticate to continue**")
            email = st.text_input("Email Address", placeholder="your.email@aiplabro.com")
            
            if st.button("Authenticate"):
                if email and ("@aiplabro.com" in email or "@ajitindustries.com" in email):
                    st.session_state.user_email = email
                    st.session_state.user_authenticated = True
                    
                    # Log user authentication
                    try:
                        activity_logger.log_user_login(
                            email=email,
                            department="Pending Selection",
                            language="en"
                        )
                    except Exception as e:
                        # Logging failed, but don't break the authentication process
                        print(f"Warning: Could not log user login: {e}")
                    
                    st.success("✅ Authenticated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Please use a valid company email address (@aiplabro.com or @ajitindustries.com)")
        else:
            st.success(f"✅ Logged in as: {st.session_state.user_email}")
            if st.button("Logout"):
                st.session_state.user_authenticated = False
                st.session_state.department_selected = None
                st.session_state.language_selected = None
                st.session_state.messages = []
                st.rerun()
        
        # Department selection
        if st.session_state.user_authenticated and not st.session_state.department_selected:
            st.header("🏢 Select Department")
            st.markdown("Choose your department to get relevant information:")
            
            cols = st.columns(2)
            for i, dept in enumerate(DEPARTMENTS):
                with cols[i % 2]:
                    if st.button(f"🏢 {dept}", key=f"dept_{dept}", use_container_width=True):
                        st.session_state.department_selected = dept
                        st.rerun()
        
        # Language selection
        if st.session_state.department_selected and not st.session_state.language_selected:
            st.header("🌐 Select Language")
            st.markdown("Choose your preferred language for responses:")
            
            # Auto-detect language from first message if available
            if st.session_state.messages:
                first_message = st.session_state.messages[0]["content"]
                detected_lang = llm_handler.detect_language(first_message)
                st.info(f"🔍 Detected language: {LANGUAGES.get(detected_lang, 'English')}")
            
            selected_lang = st.selectbox(
                "Choose Language:",
                options=list(LANGUAGES.keys()),
                format_func=lambda x: LANGUAGES[x],
                index=0
            )
            
            if st.button("Continue", use_container_width=True):
                st.session_state.language_selected = selected_lang
                
                # Log department and language selection
                try:
                    activity_logger.log_user_login(
                        email=st.session_state.user_email,
                        department=st.session_state.department_selected,
                        language=selected_lang
                    )
                except Exception as e:
                    # Logging failed, but don't break the process
                    print(f"Warning: Could not log user login: {e}")
                
                st.rerun()
        
        # Show current settings
        if st.session_state.department_selected and st.session_state.language_selected:
            st.header("⚙️ Current Settings")
            st.markdown(f"**Department:** <span class='department-tag'>{st.session_state.department_selected}</span>", unsafe_allow_html=True)
            st.markdown(f"**Language:** {LANGUAGES[st.session_state.language_selected]}")
            
            if st.button("🔄 Change Settings"):
                st.session_state.department_selected = None
                st.session_state.language_selected = None
                st.session_state.messages = []
                st.rerun()
            

    # Main chat interface
    if st.session_state.user_authenticated and st.session_state.department_selected and st.session_state.language_selected:
        
        # Department tag in main area
        st.markdown(f"<div class='department-tag'>[{st.session_state.department_selected}]</div>", unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.markdown(f"<div class='chat-message user-message'>{message['content']}</div>", unsafe_allow_html=True)
                else:
                    # Parse and display assistant response with proper formatting
                    response_data = message.get("response_data", {})
                    if response_data:
                        # Display main answer with improved formatting
                        answer = response_data.get('answer', message['content'])
                        # Clean up the response format
                        import re
                        answer = re.sub(r'\*\*Answer \(in [^)]+\) — Confidence: [^*]+\*\*\s*', '', answer).strip()
                        # Remove any remaining summary sections
                        answer = re.sub(r'\*\*Summary:\*\*.*$', '', answer, flags=re.MULTILINE).strip()
                        st.markdown(f"<div class='chat-message assistant-message'>{answer}</div>", unsafe_allow_html=True)
                    else:
                        # Clean up regular messages too
                        import re
                        answer = message['content']
                        answer = re.sub(r'\*\*Answer \(in [^)]+\) — Confidence: [^*]+\*\*\s*', '', answer).strip()
                        answer = re.sub(r'\*\*Summary:\*\*.*$', '', answer, flags=re.MULTILINE).strip()
                        st.markdown(f"<div class='chat-message assistant-message'>{answer}</div>", unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input(f"Ask about {st.session_state.department_selected} policies..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(f"<div class='chat-message user-message'>{prompt}</div>", unsafe_allow_html=True)
            
            # Process query
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        # Get RAG pipeline
                        try:
                            rag_pipeline = get_rag_pipeline()
                            
                            # Debug: Print RAG pipeline status
                            print(f"🔍 RAG Pipeline Status:")
                            print(f"  - Chunk texts: {len(rag_pipeline.chunk_texts)}")
                            print(f"  - Chunk metadata: {len(rag_pipeline.chunk_metadata)}")
                            print(f"  - FAISS index: {rag_pipeline.faiss_index.ntotal if rag_pipeline.faiss_index else 'None'}")
                            print(f"  - BM25 index: {len(rag_pipeline.chunk_texts) if rag_pipeline.bm25_index else 'None'}")
                            
                            # Test search before getting context
                            test_results = rag_pipeline.search(prompt, st.session_state.department_selected, 5)
                            print(f"  - Test search results: {len(test_results)}")
                            
                            # If no search results, try to rebuild RAG pipeline
                            if not test_results and len(rag_pipeline.chunk_texts) == 0:
                                print("🔄 No search results and empty chunks, rebuilding RAG pipeline...")
                                # Force rebuild by clearing indices
                                if os.path.exists("index/faiss_index"):
                                    os.remove("index/faiss_index")
                                if os.path.exists("index/bm25.pkl"):
                                    os.remove("index/bm25.pkl")
                                # Reinitialize RAG pipeline
                                import rag_pipeline
                                rag_pipeline.pipeline = None
                                rag_pipeline = get_rag_pipeline()
                                print(f"  - Rebuilt RAG pipeline with {len(rag_pipeline.chunk_texts)} chunks")
                            
                            # Get context for the query
                            context_chunks, context_text = rag_pipeline.get_context_for_llm(
                                query=prompt,
                                department=st.session_state.department_selected,
                                max_tokens=4000
                            )
                            
                            print(f"  - Context chunks found: {len(context_chunks)}")
                            print(f"  - Context text length: {len(context_text)}")
                            
                        except Exception as e:
                            st.error(f"Error initializing RAG pipeline: {e}")
                            print(f"❌ RAG Pipeline Error: {e}")
                            import traceback
                            traceback.print_exc()
                            context_chunks = []
                            context_text = ""
                        
                        if not context_chunks:
                            # No relevant context found - provide helpful response
                            if st.session_state.department_selected == "HR":
                                response_data = {
                                    "answer": f"I couldn't find specific information about '{prompt}' in the HR department documents. However, I can help you with general HR policies including:\n\n• **Attendance Policy**: Working hours, late arrivals, grace periods\n• **Leave Policy**: Casual leave, sick leave, earned leave, short leave\n• **Holiday Policy**: Sundays, declared holidays, compensatory leave\n• **Outdoor Duty**: OD requests and approval process\n• **Work From Home**: WFH policies and procedures\n\nPlease try rephrasing your question or ask about any of these specific topics. You can also contact HR for more detailed information.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "gpt-4",
                                    "response_time": 0
                                }
                            elif st.session_state.department_selected == "ACCOUNTS":
                                response_data = {
                                    "answer": f"I couldn't find specific information about '{prompt}' in the ACCOUNTS department documents. However, I can help you with general accounting policies including:\n\n• **Expense Reimbursement**: Original receipts required, monthly reports\n• **Budget Management**: Monthly reviews, variance analysis\n• **Payroll Processing**: Salary on last working day, overtime calculations\n• **Vendor Payments**: Three-way matching, 30-day terms\n• **Loan Policies**: Personal loans up to 3 months salary at 12% interest\n\nPlease try rephrasing your question or ask about any of these specific topics. You can also contact the ACCOUNTS department for more detailed information.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "gpt-4",
                                    "response_time": 0
                                }
                            elif st.session_state.department_selected == "IT":
                                response_data = {
                                    "answer": f"I couldn't find specific information about '{prompt}' in the IT department documents. However, I can help you with general IT policies including:\n\n• **System Access**: Unique credentials, password changes every 90 days\n• **Software Usage**: Only approved software, license compliance\n• **Data Security**: Regular backups, encryption for sensitive data\n• **Network Policies**: No personal devices, VPN for remote access\n• **Support Procedures**: 24/7 helpdesk, priority-based response\n\nPlease try rephrasing your question or ask about any of these specific topics. You can also contact the IT department for more detailed information.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "gpt-4",
                                    "response_time": 0
                                }
                            elif st.session_state.department_selected == "SALES":
                                response_data = {
                                    "answer": f"I couldn't find specific information about '{prompt}' in the SALES department documents. However, I can help you with general sales policies including:\n\n• **Target Setting**: Monthly targets, quarterly reviews\n• **Customer Relationship**: CRM system mandatory, data confidentiality\n• **Pricing Policies**: Standard pricing, discount approvals\n• **Order Processing**: 24-hour confirmation, credit checks\n• **Commission Structure**: 2% base commission, performance bonuses\n\nPlease try rephrasing your question or ask about any of these specific topics. You can also contact the SALES department for more detailed information.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "gpt-4",
                                    "response_time": 0
                                }
                            else:
                                response_data = {
                                    "answer": f"I couldn't find specific information about your query in the {st.session_state.department_selected} department documents. Please try rephrasing your question or contact the {st.session_state.department_selected} department for assistance.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "gpt-4",
                                    "response_time": 0
                                }
                        else:
                            # Generate answer using LLM
                            try:
                                response_data = llm_handler.generate_answer(
                                    query=prompt,
                                    context_chunks=context_chunks,
                                    department=st.session_state.department_selected,
                                    language=st.session_state.language_selected
                                )
                            except Exception as e:
                                st.error(f"Error generating answer: {e}")
                                response_data = {
                                    "answer": f"I encountered an error while processing your query. Please try again or contact the {st.session_state.department_selected} department for assistance.",
                                    "confidence": "low",
                                    "sources": [],
                                    "chunk_ids": [],
                                    "model_used": "error",
                                    "response_time": 0
                                }
                        
                        # Display response with improved formatting
                        answer = response_data['answer']
                        # Clean up the response format
                        import re
                        # Remove the confidence header but keep the content
                        answer = re.sub(r'\*\*Answer \(in [^)]+\) — Confidence: [^*]+\*\*\s*', '', answer).strip()
                        # Remove any remaining summary sections
                        answer = re.sub(r'\*\*Summary:\*\*.*$', '', answer, flags=re.MULTILINE).strip()
                        st.markdown(f"<div class='chat-message assistant-message'>{answer}</div>", unsafe_allow_html=True)
                        
                        # Sources display removed for cleaner UI
                        
                        # Add regenerate button
                        if st.button("🔄 Regenerate", key=f"regenerate_{len(st.session_state.messages)}"):
                            st.rerun()
                        
                        # Save response to session state
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_data['answer'],
                            "response_data": response_data
                        })
                        
                        # Log query using comprehensive logging system
                        try:
                            db = next(get_db())
                            
                            # Get or create user record
                            user = db.query(User).filter(User.email == st.session_state.user_email).first()
                            if not user:
                                user = User(
                                    email=st.session_state.user_email,
                                    username=st.session_state.user_email.split('@')[0],
                                    department=st.session_state.department_selected,
                                    preferred_language=st.session_state.language_selected,
                                    last_login=datetime.utcnow()
                                )
                                db.add(user)
                                db.commit()
                                db.refresh(user)
                            else:
                                # Update last login and department
                                user.last_login = datetime.utcnow()
                                user.department = st.session_state.department_selected
                                user.preferred_language = st.session_state.language_selected
                                db.commit()
                            
                            # Use comprehensive logging system
                            try:
                                activity_logger.log_query(
                                    user_id=user.id,
                                    question=prompt,
                                    answer=response_data['answer'],
                                    department=st.session_state.department_selected,
                                    language=st.session_state.language_selected,
                                    response_data=response_data
                                )
                            except Exception as e:
                                # Logging failed, but don't break the query process
                                print(f"⚠️ Logging error: {e}")
                        except Exception as e:
                            print(f"⚠️ Database error: {e}")
                            # Try to log to console as fallback
                            print(f"FALLBACK LOG: User: {st.session_state.user_email}, Query: {prompt}, Answer: {response_data['answer'][:100]}...")
                    
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "I apologize, but I encountered an error while processing your request. Please try again."
                        })

    else:
        # Show welcome message
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h2>Welcome to AIPL LUMINA</h2>
            <p>Please authenticate and select your department to get started.</p>
            <p>This AI assistant can help you with:</p>
            <ul style="text-align: left; max-width: 500px; margin: 0 auto;">
                <li>📋 Company policies and procedures</li>
                <li>🏢 Department-specific information</li>
                <li>❓ Frequently asked questions</li>
                <li>📞 Support ticket creation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Footer

if __name__ == "__main__":
    main()
