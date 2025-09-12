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

# Import our enhanced modules
from rag_pipeline import get_rag_pipeline
from utils.llm_handler import llm_handler
from models import get_db, Query, User
from sqlalchemy.orm import Session

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

# Add this function
def render_markdown(text):
    html = markdown(text)
    st.markdown(html, unsafe_allow_html=True)

# Set page config
st.set_page_config(
    page_title="Welcome To AIPL LUMINA", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def main():
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Welcome To AIPL LUMINA</h1>
        <p>Your intelligent companion for company policies and procedures</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for authentication and settings
    with st.sidebar:
        st.header("🔐 Authentication")
        
        if not st.session_state.user_authenticated:
            st.markdown("**Please authenticate to continue**")
            email = st.text_input("Email Address", placeholder="your.email@aiplabro.com")
            
            if st.button("Authenticate"):
                if email and ("@aiplabro.com" in email or "@ajitindustries.com" in email):
                    st.session_state.user_email = email
                    st.session_state.user_authenticated = True
                    
                    # Log user authentication
                    activity_logger.log_user_login(
                        email=email,
                        department="Pending Selection",
                        language="en"
                    )
                    
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
                activity_logger.log_user_login(
                    email=st.session_state.user_email,
                    department=st.session_state.department_selected,
                    language=selected_lang
                )
                
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
                        # Display main answer without confidence text
                        answer = response_data.get('answer', message['content'])
                        # Remove "Answer (in English) — Confidence: High" pattern
                        import re
                        answer = re.sub(r'\*\*Answer \(in [^)]+\) — Confidence: [^*]+\*\*', '', answer).strip()
                        st.markdown(f"<div class='chat-message assistant-message'>{answer}</div>", unsafe_allow_html=True)
                        
                        # Sources removed for cleaner UI
                    else:
                        st.markdown(f"<div class='chat-message assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
        
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
                        rag_pipeline = get_rag_pipeline()
                        
                        # Get context for the query
                        context_chunks, context_text = rag_pipeline.get_context_for_llm(
                            query=prompt,
                            department=st.session_state.department_selected,
                            max_tokens=4000
                        )
                        
                        if not context_chunks:
                            # No relevant context found
                            response_data = {
                                "answer": f"I couldn't find specific information about your query in the {st.session_state.department_selected} department documents. Please try rephrasing your question or contact HR for assistance.",
                                "confidence": "low",
                                "sources": [],
                                "chunk_ids": [],
                                "model_used": "gpt-4",
                                "response_time": 0
                            }
                        else:
                            # Generate answer using LLM
                            response_data = llm_handler.generate_answer(
                                query=prompt,
                                context_chunks=context_chunks,
                                department=st.session_state.department_selected,
                                language=st.session_state.language_selected
                            )
                        
                        # Display response without confidence text
                        answer = response_data['answer']
                        # Remove "Answer (in English) — Confidence: High" pattern
                        import re
                        answer = re.sub(r'\*\*Answer \(in [^)]+\) — Confidence: [^*]+\*\*', '', answer).strip()
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
                            activity_logger.log_query(
                                user_id=user.id,
                                question=prompt,
                                answer=response_data['answer'],
                                department=st.session_state.department_selected,
                                language=st.session_state.language_selected,
                                response_data=response_data
                            )
                        except Exception as e:
                            st.error(f"Error logging query: {e}")
                    
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
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>© 2024 Ajit Industries Pvt. Ltd. | Powered by AI | <a href="http://localhost:8000/admin" target="_blank">Admin Panel</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
