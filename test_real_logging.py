#!/usr/bin/env python3
"""
Test real user logging functionality
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_config import config

st.set_page_config(
    page_title="Test Real Logging",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Test Real User Logging")

# Simulate user login
if st.button("Simulate User Login"):
    try:
        login_data = {
            "user_email": "rsm.west@aiplabro.com",
            "user_name": "Kishore More",
            "login_time": datetime.now().isoformat(),
            "department": "HR",
            "language": "en"
        }
        
        config.log_activity("user_logins", login_data)
        st.success("✅ Login logged successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Simulate user query
if st.button("Simulate User Query"):
    try:
        query_data = {
            "user_email": "rsm.west@aiplabro.com",
            "user_name": "Kishore More",
            "question": "What is the leave policy?",
            "answer": "The leave policy allows 12 days of annual leave per year.",
            "department": "HR",
            "language": "en",
            "chunks_used": 2,
            "sources": ["HR_Policy.pdf"],
            "confidence": "high",
            "response_time_seconds": 2.5,
            "model_used": "gpt-4",
            "timestamp": datetime.now().isoformat()
        }
        
        config.log_activity("queries", query_data)
        st.success("✅ Query logged successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Show current logs
st.subheader("Current Logs")
queries = config.get_logs("queries", limit=10)
logins = config.get_logs("user_logins", limit=10)

st.write(f"**Queries:** {len(queries)}")
st.write(f"**Logins:** {len(logins)}")

if queries:
    st.write("**Latest Queries:**")
    for i, query in enumerate(queries[-3:]):
        st.write(f"{i+1}. {query['data']['user_name']} ({query['data']['user_email']}): {query['data']['question'][:50]}...")

if logins:
    st.write("**Latest Logins:**")
    for i, login in enumerate(logins[-3:]):
        st.write(f"{i+1}. {login['data']['user_name']} ({login['data']['user_email']}) - {login['timestamp'][:19]}")
