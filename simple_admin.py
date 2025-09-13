"""
Simplified Admin Panel without database dependency
"""

import os
import streamlit as st
import shutil
from datetime import datetime
from simple_config import config

# Page configuration
st.set_page_config(
    page_title="Admin Panel - Simple Version",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Admin Panel - Simple Version</h1>
        <p>Manage documents and monitor system status</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("📊 Quick Stats")
        
        # Document counts by department
        total_docs = 0
        for dept in config.DEPARTMENTS:
            dept_docs = len(config.get_documents(dept))
            total_docs += dept_docs
            st.write(f"**{dept}:** {dept_docs} documents")
        
        st.markdown("---")
        st.write(f"**Total Documents:** {total_docs}")
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        recent_queries = config.get_logs("queries", limit=5)
        if recent_queries:
            for query in recent_queries:
                data = query['data']
                user_name = data.get('user_name', 'Unknown')
                question = data.get('question', 'Unknown')[:50]
                st.write(f"• **{user_name}:** {question}...")
        else:
            st.write("No recent queries")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Documents", "📊 Analytics", "🔧 System", "📝 Logs"])
    
    with tab1:
        st.header("📄 Document Management")
        
        # Upload new document
        st.subheader("Upload New Document")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type="pdf",
                help="Upload PDF documents for specific departments"
            )
        
        with col2:
            department = st.selectbox(
                "Select Department",
                config.DEPARTMENTS,
                key="upload_dept"
            )
        
        if uploaded_file is not None:
            if st.button("📤 Upload Document", type="primary"):
                try:
                    # Create department directory
                    dept_dir = os.path.join(config.DOCUMENTS_DIR, department)
                    os.makedirs(dept_dir, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(dept_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Log the upload
                    config.log_activity("uploads", {
                        "filename": uploaded_file.name,
                        "department": department,
                        "size": uploaded_file.size,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully to {department} department!")
                    
                    # Refresh the page to show updated document list
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error uploading document: {str(e)}")
        
        # Document list
        st.subheader("📋 Current Documents")
        
        for dept in config.DEPARTMENTS:
            documents = config.get_documents(dept)
            if documents:
                st.write(f"**{dept} Department ({len(documents)} documents):**")
                
                for doc in documents:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.write(f"📄 {doc['filename']}")
                    
                    with col2:
                        st.write(f"📊 {doc['size']:,} bytes")
                    
                    with col3:
                        st.write(f"📅 {doc['modified'][:10]}")
                    
                    with col4:
                        if st.button("🗑️", key=f"delete_{doc['filename']}"):
                            try:
                                os.remove(doc['filepath'])
                                st.success(f"✅ Deleted {doc['filename']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting file: {str(e)}")
                
                st.markdown("---")
    
    with tab2:
        st.header("📊 Analytics")
        
        # Query statistics
        st.subheader("📈 Query Statistics")
        
        queries = config.get_logs("queries", limit=100)
        if queries:
            # Department breakdown
            dept_counts = {}
            user_counts = {}
            total_response_time = 0
            response_times = []
            
            for query in queries:
                data = query['data']
                dept = data.get('department', 'Unknown')
                user_email = data.get('user_email', 'Unknown')
                response_time = data.get('response_time_seconds', 0)
                
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
                user_counts[user_email] = user_counts.get(user_email, 0) + 1
                total_response_time += response_time
                if response_time > 0:
                    response_times.append(response_time)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Queries by Department:**")
                for dept, count in dept_counts.items():
                    st.write(f"• {dept}: {count} queries")
                
                st.write("**Top Users:**")
                sorted_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
                for user, count in sorted_users[:5]:
                    st.write(f"• {user}: {count} queries")
            
            with col2:
                st.write("**Recent Queries:**")
                for query in queries[-10:]:
                    data = query['data']
                    user_name = data.get('user_name', 'Unknown')
                    question = data.get('question', 'Unknown')[:50]
                    response_time = data.get('response_time_seconds', 0)
                    st.write(f"• **{user_name}:** {question}... ({response_time:.2f}s)")
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    st.write(f"**Average Response Time:** {avg_response_time:.2f} seconds")
        else:
            st.info("No queries found")
        
        # Upload statistics
        st.subheader("📤 Upload Statistics")
        
        uploads = config.get_logs("uploads", limit=100)
        if uploads:
            # Department breakdown
            dept_uploads = {}
            for upload in uploads:
                dept = upload['data'].get('department', 'Unknown')
                dept_uploads[dept] = dept_uploads.get(dept, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Uploads by Department:**")
                for dept, count in dept_uploads.items():
                    st.write(f"• {dept}: {count} uploads")
            
            with col2:
                st.write("**Recent Uploads:**")
                for upload in uploads[-10:]:
                    st.write(f"• {upload['data'].get('filename', 'Unknown')}")
        else:
            st.info("No uploads found")
    
    with tab3:
        st.header("🔧 System Status")
        
        # RAG Pipeline status
        st.subheader("🤖 RAG Pipeline Status")
        
        try:
            from simple_rag_pipeline import get_rag_pipeline
            rag_pipeline = get_rag_pipeline()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="status-card success-card">
                    <h4>✅ Chunks</h4>
                    <p>{len(rag_pipeline.chunk_texts)} chunks loaded</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="status-card success-card">
                    <h4>✅ FAISS Index</h4>
                    <p>{rag_pipeline.faiss_index.ntotal if rag_pipeline.faiss_index else 0} vectors</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="status-card success-card">
                    <h4>✅ BM25 Index</h4>
                    <p>{'Available' if rag_pipeline.bm25_index else 'Not Available'}</p>
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.markdown(f"""
            <div class="status-card error-card">
                <h4>❌ RAG Pipeline Error</h4>
                <p>{str(e)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # System information
        st.subheader("💻 System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Environment:**")
            if os.path.exists('/mount/src'):
                st.write("• Streamlit Cloud")
            else:
                st.write("• Local Development")
            
            st.write("**Working Directory:**")
            st.write(f"• {os.getcwd()}")
        
        with col2:
            st.write("**Directories:**")
            st.write(f"• Documents: {config.DOCUMENTS_DIR}")
            st.write(f"• Logs: {config.LOGS_DIR}")
            st.write(f"• Index: {config.INDEX_DIR}")
        
        # Actions
        st.subheader("🔄 Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh RAG Pipeline", type="primary"):
                try:
                    # Recreate RAG pipeline
                    from simple_rag_pipeline import get_rag_pipeline
                    global _rag_pipeline
                    _rag_pipeline = None
                    get_rag_pipeline()
                    st.success("✅ RAG Pipeline refreshed!")
                except Exception as e:
                    st.error(f"❌ Error refreshing RAG pipeline: {str(e)}")
        
        with col2:
            if st.button("🧹 Clear Logs"):
                try:
                    for log_type in ["queries", "uploads", "errors"]:
                        log_file = os.path.join(config.LOGS_DIR, f"{log_type}.json")
                        if os.path.exists(log_file):
                            os.remove(log_file)
                    st.success("✅ Logs cleared!")
                except Exception as e:
                    st.error(f"❌ Error clearing logs: {str(e)}")
        
        with col3:
            if st.button("📊 Export Logs"):
                try:
                    # Create export file
                    export_data = {}
                    for log_type in ["queries", "uploads", "errors"]:
                        export_data[log_type] = config.get_logs(log_type, limit=1000)
                    
                    export_file = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(export_file, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Logs exported to {export_file}")
                except Exception as e:
                    st.error(f"❌ Error exporting logs: {str(e)}")
    
    with tab4:
        st.header("📝 System Logs")
        
        # Log type selection
        log_type = st.selectbox(
            "Select Log Type",
            ["queries", "user_logins", "uploads", "errors"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Get logs
        logs = config.get_logs(log_type, limit=100)
        
        if logs:
            st.write(f"**{len(logs)} {log_type} found:**")
            
            for i, log in enumerate(reversed(logs)):  # Show newest first
                data = log['data']
                timestamp = log['timestamp'][:19]
                
                if log_type == "queries":
                    user_name = data.get('user_name', 'Unknown')
                    user_email = data.get('user_email', 'Unknown')
                    question = data.get('question', 'Unknown')[:100]
                    response_time = data.get('response_time_seconds', 0)
                    confidence = data.get('confidence', 'Unknown')
                    
                    with st.expander(f"Query #{len(logs) - i} - {user_name} ({timestamp})"):
                        st.write(f"**👤 User:** {user_name} ({user_email})")
                        st.write(f"**❓ Question:** {data.get('question', 'Unknown')}")
                        st.write(f"**🤖 Answer:** {data.get('answer', 'Unknown')}")
                        st.write(f"**🏢 Department:** {data.get('department', 'Unknown')}")
                        st.write(f"**🌐 Language:** {data.get('language', 'Unknown')}")
                        st.write(f"**⏱️ Response Time:** {response_time:.2f} seconds")
                        st.write(f"**🎯 Confidence:** {confidence}")
                        st.write(f"**📊 Chunks Used:** {data.get('chunks_used', 0)}")
                        st.write(f"**📚 Sources:** {', '.join(data.get('sources', []))}")
                        st.write(f"**🤖 Model:** {data.get('model_used', 'Unknown')}")
                        st.write(f"**📅 Timestamp:** {timestamp}")
                
                elif log_type == "user_logins":
                    user_name = data.get('user_name', 'Unknown')
                    user_email = data.get('user_email', 'Unknown')
                    department = data.get('department', 'Unknown')
                    language = data.get('language', 'Unknown')
                    
                    with st.expander(f"Login #{len(logs) - i} - {user_name} ({timestamp})"):
                        st.write(f"**👤 User:** {user_name} ({user_email})")
                        st.write(f"**🏢 Department:** {department}")
                        st.write(f"**🌐 Language:** {language}")
                        st.write(f"**📅 Login Time:** {timestamp}")
                
                else:
                    with st.expander(f"{log_type.title()} #{len(logs) - i} - {timestamp}"):
                        st.json(data)
        else:
            st.info(f"No {log_type} found")

if __name__ == "__main__":
    main()
