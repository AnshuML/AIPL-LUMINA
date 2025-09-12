import streamlit as st
import os

st.set_page_config(
    page_title="AIPL LUMINA Test", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏢 AIPL LUMINA - Test Page")

st.write("If you can see this, the basic app is working!")

# Test imports
try:
    from markdown import markdown
    st.success("✅ Markdown import successful")
except Exception as e:
    st.error(f"❌ Markdown import failed: {e}")

try:
    from dotenv import load_dotenv
    st.success("✅ dotenv import successful")
except Exception as e:
    st.error(f"❌ dotenv import failed: {e}")

try:
    from models import get_db
    st.success("✅ Models import successful")
except Exception as e:
    st.error(f"❌ Models import failed: {e}")

try:
    from utils.logger import activity_logger
    st.success("✅ Logger import successful")
except Exception as e:
    st.error(f"❌ Logger import failed: {e}")

# Test database connection
try:
    db = next(get_db())
    st.success("✅ Database connection successful")
    db.close()
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")

st.write("Environment variables:")
st.write(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
st.write(f"SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
