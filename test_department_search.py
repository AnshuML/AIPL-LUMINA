#!/usr/bin/env python3
"""
Test search for different departments
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_department_search():
    """Test search for different departments"""
    print("🧪 Testing department-specific search...")
    
    try:
        from rag_pipeline import get_rag_pipeline
        
        # Get RAG pipeline
        rag = get_rag_pipeline()
        
        # Test queries for different departments
        test_cases = [
            ("HR", "leave policy"),
            ("HR", "attendance policy"),
            ("ACCOUNTS", "finfinity"),
            ("ACCOUNTS", "accounting"),
            ("HR", "work from home"),
        ]
        
        for department, query in test_cases:
            print(f"\n🔍 Testing: '{query}' in {department} department")
            
            # Test search
            results = rag.search(query, department, 3)
            print(f"📊 Found {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:2]):
                    print(f"  {i+1}. Score: {result['score']:.3f} - {result['text'][:80]}...")
            else:
                print("  ❌ No results found")
            
            # Test context retrieval
            context_chunks, context_text = rag.get_context_for_llm(
                query=query,
                department=department,
                max_tokens=1000
            )
            
            print(f"📊 Context chunks: {len(context_chunks)}")
            if context_chunks:
                print("✅ Context retrieval working!")
            else:
                print("❌ Context retrieval failed")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_department_search()
