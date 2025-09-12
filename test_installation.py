#!/usr/bin/env python3
"""
AIPL Enterprise RAG Chatbot - Installation Test Script
"""

import sys
import os
import importlib
from pathlib import Path
# Set environment variables directly for testing
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["SECRET_KEY"] = "your-secret-key-here"

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    required_modules = [
        'streamlit',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'openai',
        'faiss',
        'rank_bm25',
        'sentence_transformers',
        'pandas',
        'plotly',
        'pydantic',
        'jose',
        'passlib',
        'multipart'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ All required modules imported successfully!")
        return True

def test_environment():
    """Test environment variables."""
    print("\n🔧 Testing environment variables...")
    
    required_vars = ['OPENAI_API_KEY', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var}")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def test_directories():
    """Test if required directories exist."""
    print("\n📁 Testing directories...")
    
    required_dirs = [
        'uploads',
        'uploads/HR',
        'uploads/IT',
        'uploads/SALES',
        'uploads/MARKETING',
        'uploads/ACCOUNTS',
        'uploads/FACTORY',
        'uploads/CO-ORDINATION',
        'index',
        'static',
        'templates',
        'logs'
    ]
    
    missing_dirs = []
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"  ✅ {directory}")
        else:
            print(f"  ❌ {directory}")
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"\n❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    else:
        print("\n✅ All required directories exist!")
        return True

def test_database():
    """Test database connection."""
    print("\n🗄️ Testing database connection...")
    
    try:
        from models import get_db, User
        db = next(get_db())
        
        # Try to query users table
        user_count = db.query(User).count()
        print(f"  ✅ Database connection successful (Users: {user_count})")
        return True
        
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def test_rag_pipeline():
    """Test RAG pipeline initialization."""
    print("\n🤖 Testing RAG pipeline...")
    
    try:
        from rag_pipeline import get_rag_pipeline
        pipeline = get_rag_pipeline()
        print("  ✅ RAG pipeline initialized successfully")
        return True
        
    except Exception as e:
        import traceback
        print(f"  ❌ RAG pipeline initialization failed: {e}")
        print(f"  Traceback: {traceback.format_exc()}")
        return False

def test_llm_handler():
    """Test LLM handler initialization."""
    print("\n🧠 Testing LLM handler...")
    
    try:
        from utils.llm_handler import llm_handler
        print("  ✅ LLM handler initialized successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ LLM handler initialization failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🏢 AIPL Enterprise RAG Chatbot - Installation Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_environment,
        test_directories,
        test_database,
        test_rag_pipeline,
        test_llm_handler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("  python main.py both")
        print("\nAccess points:")
        print("  Chat Application: http://localhost:8501")
        print("  Admin Panel:      http://localhost:8000")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")
        print("\nCommon fixes:")
        print("  1. Install missing dependencies: python main.py install")
        print("  2. Set environment variables in .env file")
        print("  3. Create missing directories: python main.py setup")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
