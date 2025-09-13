# This file redirects to app.py for Streamlit Cloud
# The main application is in app.py

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for cloud deployment
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')

# Cloud deployment optimizations
if os.path.exists('/mount/src'):
    # Streamlit Cloud environment
    os.environ.setdefault('DISABLE_FILE_LOGGING', 'true')
    print("🌐 Streamlit Cloud environment detected")

# Import and run the main app
from app import main

# Ensure main function is called
if __name__ == "__main__":
    main()
