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

# Set OpenAI API key from environment or secrets.toml
if not os.getenv("OPENAI_API_KEY"):
    # Try to load from secrets.toml
    try:
        import toml
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            with open(secrets_path, 'r') as f:
                secrets = toml.load(f)
                if 'OPENAI_API_KEY' in secrets:
                    os.environ["OPENAI_API_KEY"] = secrets['OPENAI_API_KEY']
                    print("✅ OpenAI API key loaded from secrets.toml")
                else:
                    print("⚠️  OpenAI API key not found in secrets.toml")
    except Exception as e:
        print(f"⚠️  Could not load secrets.toml: {e}")
    
    # If still not found, show warning
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not found. Please set it manually.")
        print("You can set it in your terminal:")
        print("Windows: $env:OPENAI_API_KEY='your-api-key-here'")
        print("Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
        print("Or set it in .streamlit/secrets.toml file")
        print("RAG pipeline will be limited to text search only.")

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
    subprocess.run([sys.executable, "-m", "streamlit", "run", "simple_app.py", "--server.port", "8501"], env=env)

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
        subprocess.run([sys.executable, "-m", "streamlit", "run", "simple_app.py", "--server.port", "8501"], env=env)
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
