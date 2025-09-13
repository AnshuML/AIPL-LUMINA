#!/usr/bin/env python3
"""
Installation script for AIPL Lumina HR Chatbot
This script ensures all dependencies are installed with compatible versions
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🔧 Installing AIPL Lumina HR Chatbot Dependencies...")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install base requirements
    print("\n📦 Installing base requirements...")
    if not run_command("pip install --upgrade pip"):
        print("❌ Failed to upgrade pip")
        sys.exit(1)
    
    # Install specific versions to avoid conflicts
    packages = [
        "streamlit>=1.28.0",
        "openai>=1.0.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.1.0",
        "sentence-transformers>=2.2.0,<3.0.0",
        "huggingface_hub>=0.16.0,<0.20.0",
        "faiss-cpu>=1.7.4",
        "rank-bm25>=0.2.2",
        "PyPDF2>=3.0.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}"):
            print(f"⚠️  Warning: Failed to install {package}")
    
    print("\n🎉 Installation completed!")
    print("\n📝 Next steps:")
    print("1. Set your OpenAI API key:")
    print("   Windows: $env:OPENAI_API_KEY='your-api-key-here'")
    print("   Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
    print("2. Run the application:")
    print("   python simple_launcher.py both")

if __name__ == "__main__":
    main()
