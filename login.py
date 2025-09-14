"""
Login Page for AIPL Lumina HR Chatbot
"""

import streamlit as st
import os
from datetime import datetime
from simple_config import config

# Page configuration
st.set_page_config(
    page_title="Login - AIPL Lumina",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Dark Theme
st.markdown("""
<style>
    /* Modern theme for AIPL Lumina */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #ffffff;
    }
    
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2.5rem;
        background: linear-gradient(135deg, #0f3460 0%, #533483 100%);
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h1 {
        color: #ffffff;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .login-header p {
        color: #bdc3c7;
        font-size: 1.1rem;
    }
    
    .login-form {
        background: rgba(15, 52, 96, 0.6);
        padding: 2rem;
        border-radius: 20px;
        margin: 1.2rem 0;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .stTextInput > div > div > input {
        background: rgba(15, 52, 96, 0.6);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 12px;
        padding: 0.85rem;
        backdrop-filter: blur(4px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #533483 0%, #0f3460 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.85rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: #bdc3c7;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="login-container">
        <div class="login-header">
            <h1>Welcome To AIPL Lumina</h1>
            <p>Your intelligent HR assistant for company policies and procedures</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Form
    st.markdown("""
    <div class="login-form">
    """, unsafe_allow_html=True)
    
    st.subheader("🔐 Login to Continue")
    
    # Login form
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "📧 Email Address",
                placeholder="Enter your email address",
                help="Enter your company email address"
            )
        
        with col2:
            name = st.text_input(
                "👤 Full Name",
                placeholder="Enter your full name",
                help="Enter your complete name"
            )
        
        # Department and Language selection
        col3, col4 = st.columns(2)
        
        with col3:
            department = st.selectbox(
                "🏢 Department",
                config.DEPARTMENTS,
                help="Select your department"
            )
        
        with col4:
            language = st.selectbox(
                "🌐 Language",
                list(config.LANGUAGES.keys()),
                format_func=lambda x: config.LANGUAGES[x],
                help="Select your preferred language"
            )
        
        # Login button
        login_button = st.form_submit_button(
            "🚀 Start Chatting",
            type="primary",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle login
    if login_button:
        if email and name:
            # Store user information in session state
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.department = department
            st.session_state.language = language
            st.session_state.logged_in = True
            
            # Log user login
            config.log_activity("user_logins", {
                "user_email": email,
                "user_name": name,
                "login_time": datetime.now().isoformat(),
                "department": department,
                "language": language
            })
            
            # Redirect to chat
            st.success("✅ Login successful! Redirecting to chat...")
            st.rerun()
        else:
            st.error("❌ Please fill in all required fields")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>🔒 Secure Login | Powered by AIPL Lumina</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
