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

# Custom CSS for Dark Theme
st.markdown("""
<style>
    /* Dark theme for admin panel */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    
    .success-card {
        background-color: #1a4d1a;
        border-left-color: #28a745;
        color: #ffffff;
    }
    
    .warning-card {
        background-color: #4d3a00;
        border-left-color: #ffc107;
        color: #ffffff;
    }
    
    .error-card {
        background-color: #4d1a1a;
        border-left-color: #dc3545;
        color: #ffffff;
    }
    
    /* Dark theme for file uploader */
    .uploadedFile {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 2px dashed #666;
    }
    
    /* Dark theme for selectbox */
    .stSelectbox > div > div {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Dark theme for buttons */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
    }
    
    /* Dark theme for tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e1e1e;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Dark theme for sidebar */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* Indexing button styling */
    .index-btn {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .index-btn:hover {
        background: linear-gradient(45deg, #ee5a24, #ff6b6b);
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
                    st.info("💡 Remember to click 'Rebuild Index' to make the new document searchable in the chatbot.")
                    
                    # Refresh the page to show updated document list
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error uploading document: {str(e)}")
        
        # Indexing Section
        st.markdown("---")
        st.subheader("🔄 Document Indexing")
        
        # Show current index status
        try:
            from simple_rag_pipeline import get_rag_pipeline
            rag_pipeline = get_rag_pipeline()
            total_chunks = len(rag_pipeline.chunk_texts)
            total_docs = len(config.get_documents())
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.metric("📄 Total Documents", total_docs)
            
            with col2:
                st.metric("🔍 Searchable Chunks", total_chunks)
            
            with col3:
                if total_chunks > 0:
                    st.success("✅ Index Ready")
                else:
                    st.warning("⚠️ Index Empty")
        
        except Exception as e:
            st.error(f"❌ Error checking index status: {str(e)}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("📝 After uploading documents, click 'Rebuild Index' to make them searchable in the chatbot.")
        
        with col2:
            if st.button("🔄 Rebuild Index", type="primary", help="Process all documents and rebuild search index"):
                with st.spinner("🔄 Rebuilding index... This may take a few minutes."):
                    try:
                        # Get RAG pipeline and rebuild indices
                        rag_pipeline = get_rag_pipeline()
                        rag_pipeline.rebuild_indices()
                        
                        # Get document count
                        total_docs = len(config.get_documents())
                        total_chunks = len(rag_pipeline.chunk_texts)
                        
                        st.success(f"✅ Index rebuilt successfully!")
                        st.info(f"📊 Processed {total_docs} documents into {total_chunks} searchable chunks")
                        
                        # Log the indexing activity
                        config.log_activity("indexing", {
                            "action": "rebuild_index",
                            "total_documents": total_docs,
                            "total_chunks": total_chunks,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Force refresh the page to show updated metrics
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error rebuilding index: {str(e)}")
                        st.error("Please check the console for detailed error information.")
        
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
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📈 Query Statistics")
        
        with col2:
            col2a, col2b = st.columns(2)
            with col2a:
                if st.button("🔄 Refresh Logs", help="Refresh the analytics data"):
                    st.rerun()
            with col2b:
                if st.button("📥 Download Logs", help="Download all logs as JSON"):
                    # Create a comprehensive log export
                    all_logs = {
                        "queries": config.get_logs("queries", limit=1000),
                        "user_logins": config.get_logs("user_logins", limit=1000),
                        "uploads": config.get_logs("uploads", limit=1000),
                        "indexing": config.get_logs("indexing", limit=1000),
                        "export_timestamp": datetime.now().isoformat(),
                        "total_queries": len(config.get_logs("queries", limit=1000)),
                        "total_logins": len(config.get_logs("user_logins", limit=1000)),
                        "total_uploads": len(config.get_logs("uploads", limit=1000))
                    }
                    
                    # Convert to JSON
                    import json
                    log_json = json.dumps(all_logs, indent=2, ensure_ascii=False)
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download Complete Logs",
                        data=log_json,
                        file_name=f"aipl_lumina_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        queries = config.get_logs("queries", limit=100)
        user_logins = config.get_logs("user_logins", limit=50)
        uploads = config.get_logs("uploads", limit=50)
        
        # Show current activity summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Queries", len(queries))
        with col2:
            st.metric("👥 User Logins", len(user_logins))
        with col3:
            st.metric("📁 Document Uploads", len(uploads))
        with col4:
            st.metric("🔄 Indexing Events", len(config.get_logs("indexing", limit=50)))
        
        # Debug information
        st.write(f"**Debug:** Found {len(queries)} query logs, {len(user_logins)} login logs, {len(uploads)} upload logs")
        
        # Check if logs directory exists and show files
        logs_dir = config.LOGS_DIR
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
            st.write(f"**Log Files:** {', '.join(log_files)}")
        else:
            st.warning(f"Logs directory not found: {logs_dir}")
        
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
        
        # Recent Activity Section
        st.subheader("📋 Recent Activity")
        
        # Show recent user logins
        if user_logins:
            st.write("**Recent User Logins:**")
            for login in user_logins[-5:]:
                data = login['data']
                st.write(f"• **{data.get('user_name', 'Unknown')}** ({data.get('user_email', 'Unknown')}) - {data.get('department', 'Unknown')} - {login['timestamp'][:19]}")
        
        # Show recent uploads
        if uploads:
            st.write("**Recent Document Uploads:**")
            for upload in uploads[-5:]:
                data = upload['data']
                st.write(f"• **{data.get('filename', 'Unknown')}** - {data.get('department', 'Unknown')} - {upload['timestamp'][:19]}")
        
        # Recent Queries Detail (always show if there are queries)
        if queries:
            st.subheader("📋 Recent Queries Detail")
            
            # Show last 10 queries in detail
            recent_queries = queries[-10:] if len(queries) > 10 else queries
            
            for i, query in enumerate(reversed(recent_queries)):
                with st.expander(f"Query {len(queries) - i}: {query['data'].get('question', 'No question')[:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {query['data'].get('user_name', 'Unknown')} ({query['data'].get('user_email', 'Unknown')})")
                        st.write(f"**Department:** {query['data'].get('department', 'Unknown')}")
                        st.write(f"**Language:** {query['data'].get('language', 'Unknown')}")
                        st.write(f"**Time:** {query['timestamp']}")
                    
                    with col2:
                        st.write(f"**Chunks Used:** {query['data'].get('chunks_used', 0)}")
                        st.write(f"**Response Time:** {query['data'].get('response_time_seconds', 0):.2f}s")
                        st.write(f"**Confidence:** {query['data'].get('confidence', 'Unknown')}")
                        st.write(f"**Sources:** {', '.join(query['data'].get('sources', []))}")
                    
                    st.write("**Question:**")
                    st.write(query['data'].get('question', 'No question'))
                    
                    st.write("**Answer:**")
                    st.write(query['data'].get('answer', 'No answer')[:500] + "..." if len(query['data'].get('answer', '')) > 500 else query['data'].get('answer', 'No answer'))
    
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
