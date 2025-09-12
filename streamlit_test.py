# Streamlit Cloud Test Entry Point
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the test app
from test_app import *
