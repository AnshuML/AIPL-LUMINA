"""
Simplified  Chatbot without database dependency
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
    #page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Dark Theme
st.markdown("""
<style>
    /* Modern theme for AIPL Lumina */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #ffffff;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f3460 0%, #533483 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .chat-message {
        padding: 1.2rem;
        border-radius: 20px;
        margin: 0.8rem 0;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        position: relative;
    }
    
    .user-message {
        background: linear-gradient(135deg, #533483 0%, #0f3460 100%);
        color: white;
        margin-left: 25%;
        border: none;
        transform: translateX(10px);
        transition: transform 0.3s ease;
    }
    
    .user-message::before {
        content: "👤";
        position: absolute;
        left: -50px;
        top: 50%;
        transform: translateY(-50%);
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        border: 3px solid #fff;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
        color: white;
        margin-right: 25%;
        border: none;
        transform: translateX(-10px);
        transition: transform 0.3s ease;
    }
    
    .assistant-message::before {
        content: "🤖";
        position: absolute;
        right: -50px;
        top: 50%;
        transform: translateY(-50%);
        background: linear-gradient(135deg, #667eea, #764ba2);
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        border: 3px solid #fff;
    }
    
    .lumina-brand {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .status-info {
        background: rgba(15, 52, 96, 0.6);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 4px solid #533483;
        margin: 1.2rem 0;
        color: white;
        backdrop-filter: blur(4px);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
    }
    
    /* Modern theme for sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
        backdrop-filter: blur(4px);
    }
    
    /* Modern theme for selectbox */
    .stSelectbox > div > div {
        background: rgba(15, 52, 96, 0.6);
        color: white;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 8px;
    }
    
    /* Modern theme for chat input */
    .stChatInput > div > div {
        background: rgba(15, 52, 96, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        backdrop-filter: blur(4px);
    }
    
    /* Modern theme for expander */
    .streamlit-expander {
        background: rgba(15, 52, 96, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        backdrop-filter: blur(4px);
    }
    
    /* Footer styling */
    .footer {
        background: rgba(15, 52, 96, 0.6);
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 2.5rem;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Ensure chat input has same width as other elements */
    .stChatInput > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    .stChatInput input {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Hide Streamlit default chat message icons */
    .stChatMessage > div > div > div > div > div {
        display: none !important;
    }
    
    .stChatMessage > div > div > div > div {
        display: none !important;
    }
    
    /* Hide any remaining generic icons */
    .stChatMessage [data-testid="chatAvatarIcon-user"],
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize error message variable
    error_msg = "An unexpected error occurred"
    
    # Check if user is logged in
    if not st.session_state.get("logged_in", False):
        # Import login module
        from login import main as login_main
        login_main()
        return
    
    # Debug: Print session state
    print(f"🔍 DEBUG: User is logged in - {st.session_state.get('user_email', 'No email')}")
    print(f"🔍 DEBUG: User name - {st.session_state.get('user_name', 'No name')}")
    
    # Get user information from session state
    user_email = st.session_state.get("user_email", "")
    user_name = st.session_state.get("user_name", "")
    department = st.session_state.get("department", "HR")
    language = st.session_state.get("language", "en")
    
    # Initialize messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Show welcome screen only if no messages exist
    if not st.session_state.messages:
        # Dynamic greeting based on time - simplified and reliable
        # Get current time
        now = datetime.now()
        current_hour = now.hour
        current_time = now.strftime("%H:%M")
        
        # Simple, reliable greeting logic
        if 5 <= current_hour < 12:
            greeting = "Good morning!"
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon!"
        elif 17 <= current_hour < 22:  # Extended evening until 10 PM
            greeting = "Good evening!"
        else:
            greeting = "Good night!"
        
        # Debug: Print current time and greeting
        print(f"🕐 Current time: {current_time} (Hour: {current_hour})")
        print(f"👋 Generated greeting: {greeting}")
        
        # Welcome Screen - Professional Horizontal Layout (Same width as other elements)
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; min-height: 40vh; padding: 1rem;">
            <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 20px; padding: 2.5rem 4rem; text-align: center; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3); border: 2px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); max-width: 100%; width: 100%; min-height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <h1 style="font-size: 4rem; font-weight: bold; color: #ffffff; margin: 0 0 0.8rem 0; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; letter-spacing: 2px;">AIPL LUMINA</h1>
                <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; margin-top: 0.5rem;">
                    <span style="font-size: 1.2rem; color: #ff6b9d; font-weight: 600; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">AIPL Group</span>
                    <span style="font-size: 1.2rem; color: #ffd700; font-weight: 500; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{greeting}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # User info display (always show) - Same width as AIPL Lumina
    st.markdown(f"""
    <div style="display: flex; justify-content: center; padding: 0 1rem;">
        <div style="background-color: #2c3e50; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center; width: 100%; max-width: 100%;">
            <p style="margin: 0; color: #bdc3c7;">👤 <strong>{user_name}</strong> ({user_email}) | 🏢 {department} | 🌐 {config.LANGUAGES[language]}</p>
        </div>
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
    
    # Display chat messages with custom styling (no generic icons)
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            st.markdown(f"""
            <div class='chat-message {message['role']}-message'>
                <div class='lumina-brand'>🤖 Lumina Assistant</div>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='chat-message {message['role']}-message'>
                <div class='lumina-brand'>👤 You</div>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input - Same width as other elements
    if prompt := st.chat_input(f"Ask about {department} policies..."):
        # Debug: Print prompt
        print(f"🔍 DEBUG: User asked question: {prompt}")
        print(f"🔍 DEBUG: User email: {st.session_state.get('user_email', 'No email')}")
        print(f"🔍 DEBUG: User name: {st.session_state.get('user_name', 'No name')}")
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message (no generic icon)
        st.markdown(f"""
        <div class='chat-message user-message'>
            <div class='lumina-brand'>👤 You</div>
            {prompt}
        </div>
        """, unsafe_allow_html=True)
        
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
            
            # Force logging with error handling
            try:
                result = config.log_activity("queries", query_data)
                print(f"✅ User query logged immediately: {result}")
            except Exception as e:
                print(f"❌ Failed to log user query: {e}")
                import traceback
                traceback.print_exc()
            
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
                
                # Get client IP and user agent
                try:
                    client_ip = st.get_client_ip() if hasattr(st, 'get_client_ip') else 'unknown'
                    user_agent = st.get_user_agent() if hasattr(st, 'get_user_agent') else 'unknown'
                except Exception as e:
                    print(f"❌ Error getting client info: {e}")
                    client_ip = 'unknown'
                    user_agent = 'unknown'
                
                # Prepare query data for logging
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
                
                # Log the query
                try:
                    print(f"🔍 DEBUG: Attempting to log query for {query_data['user_email']}")
                    print(f"🔍 DEBUG: Question: {query_data['question'][:50]}...")
                    
                    try:
                        result = config.log_activity("queries", query_data)
                        print(f"✅ Query logged successfully for {st.session_state.get('user_email', 'unknown')}: {result}")
                    except Exception as e:
                        print(f"❌ Failed to log query: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Verify log was written
                    logs = config.get_logs("queries", limit=5)
                    print(f"🔍 DEBUG: Total queries in log: {len(logs)}")
                    
                except Exception as e:
                    print(f"❌ Error logging query: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Display response
                print(f"🔍 DEBUG: About to display response: {response[:100]}...")
                
                # Create a container for the response
                with st.container():
                    st.markdown(f"""
                    <div class='chat-message assistant-message'>
                        <div class='lumina-brand'>🤖 Lumina Assistant</div>
                        {response}
                    </div>
                    """, unsafe_allow_html=True)
                
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
                    no_chunks_response = "I couldn't find relevant information in the uploaded documents. Please make sure documents are uploaded for this department or try rephrasing your question."
                    print(f"🔍 DEBUG: No chunks found, using default response: {no_chunks_response[:100]}...")
                    
                    # Create a container for the no chunks response
                    with st.container():
                        st.markdown(f"""
                        <div class='chat-message assistant-message'>
                            <div class='lumina-brand'>🤖 Lumina Assistant</div>
                            {no_chunks_response}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    print(f"✅ DEBUG: No chunks response displayed successfully")
                    
                    # Add no chunks response to session state
                    st.session_state.messages.append({"role": "assistant", "content": no_chunks_response})
                    
                    # Log the no chunks query
                    try:
                        no_chunks_query_data = {
                            "user_email": st.session_state.get("user_email", "unknown"),
                            "user_name": st.session_state.get("user_name", "unknown"),
                            "question": prompt,
                            "answer": no_chunks_response,
                            "department": department,
                            "language": language,
                            "chunks_used": 0,
                            "sources": [],
                            "confidence": "low",
                            "response_time_seconds": 0,
                            "model_used": "fallback",
                            "timestamp": datetime.now().isoformat(),
                            "enhanced_processing": False,
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
                        
                        print(f"🔍 DEBUG: Attempting to log no chunks query for {no_chunks_query_data['user_email']}")
                        try:
                            result = config.log_activity("queries", no_chunks_query_data)
                            print(f"✅ No chunks query logged successfully for {st.session_state.get('user_email', 'unknown')}: {result}")
                        except Exception as e:
                            print(f"❌ Failed to log no chunks query: {e}")
                            import traceback
                            traceback.print_exc()
                        
                    except Exception as e:
                        print(f"❌ Error logging no chunks query: {e}")
                        import traceback
                        traceback.print_exc()
                        
        except Exception as e:
            # Handle any exceptions that occur during query processing
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(f"🔍 DEBUG: Error occurred: {error_msg}")
            
            # Ensure error_msg is defined
            if 'error_msg' not in locals():
                error_msg = "An unexpected error occurred"
            
            # Create a container for the error response
            with st.container():
                st.markdown(f"""
                <div class='chat-message assistant-message'>
                    <div class='lumina-brand'>🤖 Lumina Assistant</div>
                    ❌ {error_msg}
                </div>
                """, unsafe_allow_html=True)
            
            # Add error message to session state
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Footer
    st.markdown("---")
    st.markdown("**Powered by advanced AI technology for accurate, context-based answers**")

if __name__ == "__main__":
    main()
