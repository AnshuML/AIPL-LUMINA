"""
Simplified HR Chatbot without database dependency
"""

import os
import streamlit as st
import requests
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
    print("🌐 Running on Streamlit Cloud - Simple Version")
    print(f"🌐 Working directory: {os.getcwd()}")

# Import simple configuration
from simple_config import config
from simple_rag_pipeline import get_rag_pipeline
from utils.llm_handler import llm_handler

# Import enhanced RAG pipeline with error handling
try:
    from enhanced_rag_pipeline import process_query_enhanced, BM25_AVAILABLE, CROSS_ENCODER_AVAILABLE
    ENHANCED_RAG_AVAILABLE = True
except ImportError:
    print("Warning: Enhanced RAG pipeline not available, falling back to simple pipeline")
    process_query_enhanced = None
    BM25_AVAILABLE = False
    CROSS_ENCODER_AVAILABLE = False
    ENHANCED_RAG_AVAILABLE = False

# Setup directories
config.setup_directories()

# Page configuration
st.set_page_config(
    page_title="Welcome To AIPL Lumina",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Dark Theme
st.markdown("""
<style>
    /* Dark theme for entire app */
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .main-header {
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        border: 1px solid #333;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
        border: none;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        margin-right: 20%;
        border: none;
    }
    
    .status-info {
        background-color: #2c3e50;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
        color: white;
    }
    
    /* Dark theme for sidebar */
    .css-1d391kg {
        background-color: #2c3e50;
    }
    
    /* Dark theme for selectbox */
    .stSelectbox > div > div {
        background-color: #34495e;
        color: white;
    }
    
    /* Dark theme for chat input */
    .stChatInput > div > div {
        background-color: #34495e;
        border: 1px solid #555;
    }
    
    /* Dark theme for expander */
    .streamlit-expander {
        background-color: #2c3e50;
        border: 1px solid #555;
    }
    
    /* Footer styling */
    .footer {
        background-color: #2c3e50;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        color: #bdc3c7;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Check if user is logged in
    if not st.session_state.get("logged_in", False):
        st.warning("🔐 Please login first to access the chatbot")
        st.info("Click the 'Login' button in the sidebar to continue")
        return
    
    # Debug: Print session state
    print(f"🔍 DEBUG: User is logged in - {st.session_state.get('user_email', 'No email')}")
    print(f"🔍 DEBUG: User name - {st.session_state.get('user_name', 'No name')}")
    
    # Get user information from session state
    user_email = st.session_state.get("user_email", "")
    user_name = st.session_state.get("user_name", "")
    department = st.session_state.get("department", "HR")
    language = st.session_state.get("language", "en")
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1> Welcome To AIPL Lumina</h1>
        <p>Your intelligent HR assistant for company policies and procedures</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User info display
    st.markdown(f"""
    <div style="background-color: #2c3e50; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
        <p style="margin: 0; color: #bdc3c7;">👤 <strong>{user_name}</strong> ({user_email}) | 🏢 {department} | 🌐 {config.LANGUAGES[language]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Simplified
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # Department selection
        department = st.selectbox(
            "Select Department",
            config.DEPARTMENTS,
            index=config.DEPARTMENTS.index(department) if department in config.DEPARTMENTS else 0
        )
        
        # Language selection
        language = st.selectbox(
            "Select Language",
            list(config.LANGUAGES.keys()),
            format_func=lambda x: config.LANGUAGES[x],
            index=list(config.LANGUAGES.keys()).index(language) if language in config.LANGUAGES else 0
        )
        
        # Logout button
        if st.button("🚪 Logout", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Update session state if changed
        if department != st.session_state.get("department"):
            st.session_state.department = department
        if language != st.session_state.get("language"):
            st.session_state.language = language
    
    # Main chat interface
    
    # Initialize session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"{int(time.time())}_{hash(user_email)}"
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"<div class='chat-message {message['role']}-message'>{message['content']}</div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input(f"Ask about {department} policies..."):
        # Debug: Print prompt
        print(f"🔍 DEBUG: User asked question: {prompt}")
        print(f"🔍 DEBUG: User email: {st.session_state.get('user_email', 'No email')}")
        print(f"🔍 DEBUG: User name: {st.session_state.get('user_name', 'No name')}")
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(f"<div class='chat-message user-message'>{prompt}</div>", unsafe_allow_html=True)
        
        # Force logging of user query immediately
        try:
            query_data = {
                "user_email": st.session_state.get("user_email", "unknown"),
                "user_name": st.session_state.get("user_name", "unknown"),
                "question": prompt,
                "answer": "Processing...",
                "department": department,
                "language": language,
                "chunks_used": 0,
                "sources": [],
                "confidence": "processing",
                "response_time_seconds": 0,
                "model_used": "processing",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"🔍 DEBUG: Logging user query immediately for {query_data['user_email']}")
            print(f"🔍 DEBUG: Question: {prompt}")
            print(f"🔍 DEBUG: User: {st.session_state.get('user_name', 'No name')}")
            
            # Force logging
            config.log_activity("queries", query_data)
            print(f"✅ User query logged immediately")
            
            # Verify log was written
            logs = config.get_logs("queries", limit=5)
            print(f"🔍 DEBUG: Total queries after logging: {len(logs)}")
            
        except Exception as e:
            print(f"❌ Error logging user query immediately: {e}")
            import traceback
            traceback.print_exc()
        
        # Process query
        try:
            with st.spinner("Lumina Thinking..."):
                # Debug: Print session state
                print(f"🔍 DEBUG: Session state - logged_in: {st.session_state.get('logged_in', False)}")
                print(f"🔍 DEBUG: Session state - user_email: {st.session_state.get('user_email', 'None')}")
                print(f"🔍 DEBUG: Session state - user_name: {st.session_state.get('user_name', 'None')}")
            
                # Use enhanced RAG pipeline for robust processing
                print(f"🔍 DEBUG: Processing query with enhanced RAG: {prompt[:50]}...")
                response_data = process_query_enhanced(prompt, department, language)
                response = response_data.get('answer', 'Sorry, I could not generate a response.')
                print(f"🔍 DEBUG: Generated response: {response[:100]}...")
                
                # Log the query with complete user information
                try:
                    # Get client IP and user agent
                    client_ip = st.get_client_ip() if hasattr(st, 'get_client_ip') else 'unknown'
                    user_agent = st.get_user_agent() if hasattr(st, 'get_user_agent') else 'unknown'
                except Exception as e:
                    print(f"❌ Error getting client info: {e}")
                    client_ip = 'unknown'
                    user_agent = 'unknown'
                
                query_data = {
                    "user_email": st.session_state.get("user_email", "unknown"),
                    "user_name": st.session_state.get("user_name", "unknown"),
                    "question": prompt,
                    "answer": response,
                    "department": department,
                    "language": language,
                    "chunks_used": response_data.get('chunks_used', 0),
                    "sources": response_data.get('sources', []),
                    "confidence": response_data.get('confidence', 'medium'),
                    "response_time_seconds": response_data.get('response_time', 0),
                    "model_used": response_data.get('model_used', 'gpt-4'),
                    "timestamp": datetime.now().isoformat(),
                    "enhanced_processing": True,
                    "session_id": st.session_state.session_id,
                    "user_ip": client_ip,
                    "platform": {
                        "type": "web",
                        "user_agent": user_agent
                    },
                    "context": {
                        "total_messages": len(st.session_state.messages),
                        "session_duration": time.time() - float(st.session_state.session_id.split('_')[0])
                    }
                }
                    
                # Debug: Print query data
                print(f"🔍 DEBUG: Attempting to log query for {query_data['user_email']}")
                print(f"🔍 DEBUG: Question: {query_data['question'][:50]}...")
                
                # Force logging
                config.log_activity("queries", query_data)
                print(f"✅ Query logged successfully for {st.session_state.get('user_email', 'unknown')}")
                
                # Verify log was written
                logs = config.get_logs("queries", limit=5)
                print(f"🔍 DEBUG: Total queries in log: {len(logs)}")
                
                # Force refresh admin panel
                # st.rerun()  # Commented out to prevent page refresh
                
        except Exception as e:
            print(f"❌ Error logging query: {e}")
            import traceback
            traceback.print_exc()
            
        # Display response
        print(f"🔍 DEBUG: About to display response: {response[:100]}...")
        
        # Create a container for the response
        with st.container():
            st.markdown("**🤖 Assistant:**")
            st.markdown(response)
            st.markdown("---")
        
        print(f"✅ DEBUG: Response displayed successfully")
        
        # Add response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})
    
        # Show sources
        sources = response_data.get('sources', [])
        if sources:
            with st.expander("📚 Sources"):
                for i, source in enumerate(sources, 1):
                    st.write(f"**{i}.** {source}")
                st.write(f"**Chunks Used:** {response_data.get('chunks_used', 0)}")
                st.write(f"**Confidence:** {response_data.get('confidence', 'Unknown')}")
        else:
            # No relevant chunks found
            response = "I couldn't find relevant information in the uploaded documents. Please make sure documents are uploaded for this department or try rephrasing your question."
            print(f"🔍 DEBUG: No chunks found, using default response: {response[:100]}...")
            
            # Create a container for the response
            with st.container():
                st.markdown("**🤖 Assistant:**")
                st.markdown(response)
                st.markdown("---")
            
            print(f"✅ DEBUG: No chunks response displayed successfully")
            
            # Add response to session state
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Log the query with complete user information
            try:
                query_data = {
                    "user_email": st.session_state.get("user_email", "unknown"),
                    "user_name": st.session_state.get("user_name", "unknown"),
                    "question": prompt,
                    "answer": response,
                    "department": department,
                    "language": language,
                    "chunks_used": 0,
                    "sources": [],
                    "confidence": "low",
                    "response_time_seconds": 0,
                    "model_used": "none",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Debug: Print query data
                print(f"🔍 DEBUG: Attempting to log query for {query_data['user_email']}")
                print(f"🔍 DEBUG: Question: {query_data['question'][:50]}...")
                
                # Force logging
                config.log_activity("queries", query_data)
                print(f"✅ Query logged successfully for {st.session_state.get('user_email', 'unknown')}")
                
                # Verify log was written
                logs = config.get_logs("queries", limit=5)
                print(f"🔍 DEBUG: Total queries in log: {len(logs)}")
                
                # Force refresh admin panel
                # st.rerun()  # Commented out to prevent page refresh
                
            except Exception as e:
                print(f"❌ Error logging query: {e}")
                import traceback
                traceback.print_exc()
        
            except Exception as e:
            # Handle any exceptions that occur during query processing
               error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"🔍 DEBUG: Error occurred: {error_msg}")
        
            # Create a container for the error response
            with st.container():
                st.markdown("**🤖 Assistant:**")
                st.markdown(f"❌ {error_msg}")
                st.markdown("---")
            
            print(f"Error processing query: {e}")
            
            # Add error message to session state
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # Log the error with complete user information
            try:
                config.log_activity("errors", {
                    "user_email": st.session_state.get("user_email", "unknown"),
                    "user_name": st.session_state.get("user_name", "unknown"),
                    "question": prompt,
                    "error": str(e),
                    "department": department,
                    "language": language,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"✅ Error logged successfully for {st.session_state.get('user_email', 'unknown')}")
            except Exception as log_error:
                print(f"❌ Error logging error: {log_error}")
    
    # Session state is now managed within each response section
    # No need for this additional management
    
    # Footer
    st.markdown("---")
    st.markdown("**Powered by advanced AI technology for accurate, context-based answers**")

if __name__ == "__main__":
    main()
