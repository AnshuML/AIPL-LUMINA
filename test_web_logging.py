#!/usr/bin/env python3
"""
Test web logging functionality
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_config import config

st.set_page_config(
    page_title="Test Web Logging",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Test Web Logging")

if st.button("Test Query Logging"):
    try:
        config.log_activity("queries", {
            "user_email": "test@aiplabro.com",
            "user_name": "Test User",
            "question": "Test question from web",
            "answer": "Test answer from web",
            "department": "HR",
            "language": "en",
            "chunks_used": 1,
            "sources": ["test.pdf"],
            "confidence": "high",
            "response_time_seconds": 1.5,
            "model_used": "gpt-4",
            "timestamp": datetime.now().isoformat()
        })
        st.success("✅ Query logged successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

if st.button("Test Login Logging"):
    try:
        config.log_activity("user_logins", {
            "user_email": "test@aiplabro.com",
            "user_name": "Test User",
            "login_time": datetime.now().isoformat(),
            "department": "HR",
            "language": "en"
        })
        st.success("✅ Login logged successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Show current logs
st.subheader("Current Logs")
queries = config.get_logs("queries", limit=5)
logins = config.get_logs("user_logins", limit=5)

st.write(f"**Queries:** {len(queries)}")
st.write(f"**Logins:** {len(logins)}")

if queries:
    st.write("**Latest Query:**")
    st.json(queries[-1])

if logins:
    st.write("**Latest Login:**")
    st.json(logins[-1])
