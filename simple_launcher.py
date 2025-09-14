#!/usr/bin/env python3
"""
Simple launcher for HR Chatbot without database dependency
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set OpenAI API key from environment or prompt user
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️  OpenAI API key not found in environment variables.")
    print("Please set OPENAI_API_KEY environment variable.")
    print("For local development, you can set it in your terminal:")
    print("Windows: $env:OPENAI_API_KEY='your-api-key-here'")
    print("Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
    print("\nOr you can set it directly in this session:")
    api_key = input("Enter your OpenAI API key: ").strip()
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        print("✅ API key set for this session")
    else:
        print("❌ No API key provided. Exiting.")
        sys.exit(1)

def setup_environment():
    """Setup the environment for the simple version"""
    print("🔧 Setting up simple environment...")
    
    # Verify OpenAI API key is set
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key found")
    else:
        print("❌ OpenAI API key not found")
        return False
    
    # Create necessary directories
    directories = ["documents", "logs", "index"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
        
        # Create department subdirectories
        departments = ["HR", "IT", "SALES", "MARKETING", "ACCOUNTS", "FACTORY", "CO-ORDINATION"]
        for dept in departments:
            dept_dir = os.path.join(directory, dept)
            os.makedirs(dept_dir, exist_ok=True)
    
    print("✅ Environment setup complete!")

def run_chat():
    """Run the chat application with login"""
    print("🚀 Starting AIPL Lumina HR Chatbot with Login...")
    env = os.environ.copy()
    subprocess.run([sys.executable, "-m", "streamlit", "run", "main_app.py", "--server.port", "8501"], env=env)

def run_admin():
    """Run the admin panel"""
    print("🚀 Starting Admin Panel...")
    env = os.environ.copy()
    subprocess.run([sys.executable, "-m", "streamlit", "run", "simple_admin.py", "--server.port", "8502"], env=env)

def run_both():
    """Run both applications"""
    print("🚀 Starting both applications...")
    print("📱 Chat App: http://localhost:8501")
    print("⚙️ Admin Panel: http://localhost:8502")
    
    env = os.environ.copy()
    
    # Start admin panel in background
    admin_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "simple_admin.py", "--server.port", "8502"], env=env)
    
    # Start chat app in foreground
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main_app.py", "--server.port", "8501"], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        admin_process.terminate()

def main():
    parser = argparse.ArgumentParser(description="HR Chatbot - Simple Version")
    parser.add_argument("command", choices=["setup", "chat", "admin", "both"], 
                       help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_environment()
    elif args.command == "chat":
        run_chat()
    elif args.command == "admin":
        run_admin()
    elif args.command == "both":
        run_both()

if __name__ == "__main__":
    main()
