#!/usr/bin/env python3
"""
AIPL Enterprise RAG Chatbot - Main Application Runner
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "uploads",
        "uploads/HR",
        "uploads/IT", 
        "uploads/SALES",
        "uploads/MARKETING",
        "uploads/ACCOUNTS",
        "uploads/FACTORY",
        "uploads/CO-ORDINATION",
        "index",
        "static",
        "templates",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def run_streamlit():
    """Run the Streamlit chat application."""
    print("🚀 Starting Streamlit chat application...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "127.0.0.1",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Streamlit application stopped")

def run_admin_app():
    """Run the Streamlit admin panel."""
    print("🚀 Starting Streamlit admin panel...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "admin_app.py",
            "--server.port", "8502",
            "--server.address", "127.0.0.1",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Admin app stopped")

def run_both():
    """Run both applications concurrently."""
    print("🚀 Starting both applications...")
    
    # Start Streamlit in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Give Streamlit time to start
    time.sleep(3)
    
    # Start Admin App
    try:
        run_admin_app()
    except KeyboardInterrupt:
        print("\n🛑 All applications stopped")

def show_help():
    """Show help information."""
    print("""
🏢 AIPL Enterprise RAG Chatbot

Usage: python main.py [command]

    Commands:
  chat        Run only the Streamlit chat application (port 8501)
  admin       Run only the Streamlit admin panel (port 8502)
  both        Run both applications concurrently (default)
  install     Install dependencies only
  setup       Setup directories and check environment
  help        Show this help message

Environment Variables Required:
  OPENAI_API_KEY    - Your OpenAI API key
  SECRET_KEY        - Secret key for JWT tokens

Optional Environment Variables:
  DATABASE_URL      - Database URL (default: sqlite:///hr_chatbot.db)
  GOOGLE_API_KEY    - Google API key (if using Gemini)

Access Points:
  Chat Application: http://localhost:8501
  Admin Panel:      http://localhost:8502

For more information, see the README.md file.
""")

def main():
    """Main application entry point."""
    if len(sys.argv) < 2:
        command = "both"
    else:
        command = sys.argv[1].lower()
    
    print("🏢 AIPL Enterprise RAG Chatbot")
    print("=" * 50)
    
    if command == "help":
        show_help()
        return
    
    if command == "install":
        if not install_dependencies():
            sys.exit(1)
        return
    
    if command == "setup":
        create_directories()
        if not check_environment():
            sys.exit(1)
        print("✅ Setup completed successfully")
        return
    
    # Check environment for running applications
    if not check_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies if needed
    try:
        import streamlit
        import fastapi
        import openai
    except ImportError:
        print("📦 Installing missing dependencies...")
        if not install_dependencies():
            sys.exit(1)
    
    # Run the appropriate command
    if command == "chat":
        run_streamlit()
    elif command == "admin":
        run_admin_app()
    elif command == "both":
        run_both()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
