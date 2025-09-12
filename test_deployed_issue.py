#!/usr/bin/env python3
"""
Test what might be causing the deployed issue
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_deployed_issue():
    """Test what might be causing the deployed issue"""
    print("🔍 Testing deployed issue...")
    
    try:
        from rag_pipeline import get_rag_pipeline
        
        # Get RAG pipeline
        rag = get_rag_pipeline()
        
        # Test the exact same query that would be used in the app
        query = "leave policy"
        department = "HR"
        
        print(f"🔍 Testing query: '{query}' in department: '{department}'")
        
        # Test search
        results = rag.search(query, department, 3)
        print(f"📊 Search results: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. Score: {result['score']:.3f} - {result['text'][:80]}...")
                print(f"      Department: {result['metadata'].get('department', 'N/A')}")
        
        # Test context retrieval (this is what the app uses)
        print(f"\n🔍 Testing context retrieval:")
        context_chunks, context_text = rag.get_context_for_llm(
            query=query,
            department=department,
            max_tokens=4000
        )
        
        print(f"📊 Context chunks: {len(context_chunks)}")
        print(f"📊 Context text length: {len(context_text)}")
        
        if context_chunks:
            print("✅ Context chunks found - app should work")
            print(f"First chunk: {context_chunks[0]['text'][:100]}...")
        else:
            print("❌ No context chunks - this is why app shows 'no information'")
            
        # Test with different queries that might be used
        test_queries = [
            "metro city mai kauon kauon se town aate hain",
            "metro city",
            "town",
            "metro"
        ]
        
        print(f"\n🔍 Testing queries that might cause issues:")
        for test_query in test_queries:
            test_results = rag.search(test_query, department, 3)
            test_context_chunks, _ = rag.get_context_for_llm(
                query=test_query,
                department=department,
                max_tokens=1000
            )
            print(f"  '{test_query}': {len(test_results)} results, {len(test_context_chunks)} context chunks")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deployed_issue()
