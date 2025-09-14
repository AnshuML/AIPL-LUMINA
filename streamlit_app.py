#!/usr/bin/env python3
"""
Main entry point for Streamlit Cloud deployment
Routes to the appropriate app based on URL or session state
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our main app
from main_app import main

if __name__ == "__main__":
    main()
