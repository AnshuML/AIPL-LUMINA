#!/usr/bin/env python3
"""
Test the streamlit app directly
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_streamlit_app():
    """Test the streamlit app directly"""
    print("🔍 Testing streamlit app...")
    
    try:
        # Import the app module
        from app import ensure_sample_data, get_rag_pipeline
        
        print("✅ App imports successfully")
        
        # Test sample data function
        print("\n🔍 Testing ensure_sample_data...")
        ensure_sample_data()
        print("✅ Sample data function completed")
        
        # Test RAG pipeline
        print("\n🔍 Testing RAG pipeline...")
        rag = get_rag_pipeline()
        print(f"✅ RAG pipeline loaded: {len(rag.chunk_texts)} chunks")
        
        # Test search
        results = rag.search("leave policy", "HR", 3)
        print(f"✅ Search test: {len(results)} results")
        
        if results:
            print("✅ App should be working correctly")
        else:
            print("❌ App has search issues")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streamlit_app()
