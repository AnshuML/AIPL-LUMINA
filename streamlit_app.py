# Streamlit Cloud Entry Point
# This file is the main entry point for Streamlit Cloud deployment

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for cloud deployment
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')

# Import and run the main app
from app import main

# Ensure main function is called
if __name__ == "__main__":
    main()
