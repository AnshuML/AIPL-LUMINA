"""
Main App Launcher for AIPL Lumina HR Chatbot
Handles login flow and routing
"""

import streamlit as st
import os
from datetime import datetime
from simple_config import config

# Setup directories first
config.setup_directories()

# Page configuration
st.set_page_config(
    page_title="AIPL Lumina HR Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cloud deployment optimizations
if os.path.exists('/mount/src'):
    # Streamlit Cloud environment
    os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
    os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    print("🌐 Running on Streamlit Cloud - AIPL Lumina HR Chatbot")
    print(f"🌐 Working directory: {os.getcwd()}")

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
    
    .nav-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: bold;
        margin: 0.5rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .user-info {
        background-color: #2c3e50;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Check if user is logged in
    if st.session_state.get("logged_in", False):
        show_chat_page()
    else:
        show_login_page()

def show_login_page():
    """Display simple login page"""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Welcome To AIPL Lumina</h1>
        <p>Your intelligent HR assistant for company policies and procedures</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    st.markdown("### 🔐 Login to Continue")
    
    with st.form("login_form"):
        # Email input with company domain validation
        email = st.text_input(
            "📧 Company Email Address",
            placeholder="Enter your company email (e.g., user@aiplabro.com)",
            help="Enter your company email address ending with @aiplabro.com or @ajitindustries.com"
        )
        
        # Name input
        name = st.text_input(
            "👤 Full Name",
            placeholder="Enter your full name",
            help="Enter your complete name"
        )
        
        # Login button
        login_button = st.form_submit_button(
            "🚀 Login",
            type="primary",
            use_container_width=True
        )
    
    # Handle login
    if login_button:
        if email and name:
            # Validate company email domain
            valid_domains = ["@aiplabro.com", "@ajitindustries.com"]
            if not any(email.lower().endswith(domain) for domain in valid_domains):
                st.error("❌ Please use a valid company email address (@aiplabro.com or @ajitindustries.com)")
            else:
                # Store user information in session state
                st.session_state.user_email = email
                st.session_state.user_name = name
                st.session_state.department = "HR"  # Default department
                st.session_state.language = "en"    # Default language
                st.session_state.logged_in = True
                
                # Log user login
                config.log_activity("user_logins", {
                    "user_email": email,
                    "user_name": name,
                    "login_time": datetime.now().isoformat(),
                    "department": "HR",
                    "language": "en"
                })
                
                # Show success and redirect
                st.success("✅ Login successful! Redirecting to chat...")
                st.rerun()
        else:
            st.error("❌ Please fill in all required fields")

def show_chat_page():
    """Display chat page"""
    # Import and run the chat functionality
    from simple_app import main as chat_main
    chat_main()

if __name__ == "__main__":
    main()
