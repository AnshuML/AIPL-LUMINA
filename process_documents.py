#!/usr/bin/env python3
"""
Script to process existing documents and add them to the RAG pipeline
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from models import get_db, Document
from rag_pipeline import get_rag_pipeline
from utils.pdf_processor import process_pdfs

def process_existing_documents():
    """Process all unprocessed documents in the database"""
    print("🔄 Starting document processing...")
    
    try:
        # Get database connection
        db = next(get_db())
        
        try:
            # Get all unprocessed documents
            unprocessed_docs = db.query(Document).filter(Document.is_processed == False).all()
            
            if not unprocessed_docs:
                print("✅ No unprocessed documents found")
                return
            
            print(f"📄 Found {len(unprocessed_docs)} unprocessed documents")
            
            # Get RAG pipeline
            rag_pipeline = get_rag_pipeline()
            
            processed_count = 0
            failed_count = 0
            
            for doc in unprocessed_docs:
                try:
                    print(f"🔄 Processing: {doc.original_filename}")
                    
                    # Check if file exists
                    if not os.path.exists(doc.file_path):
                        print(f"⚠️ File not found: {doc.file_path}")
                        failed_count += 1
                        continue
                    
                    # Process the PDF
                    processed_docs = process_pdfs([doc.file_path])
                    
                    if not processed_docs:
                        print(f"⚠️ No text extracted from: {doc.original_filename}")
                        failed_count += 1
                        continue
                    
                    # Extract texts and create metadata
                    texts = [doc_data["content"] for doc_data in processed_docs]
                    metadata = [{
                        "filename": doc.original_filename,
                        "department": doc.department,
                        "file_path": doc.file_path,
                        "upload_date": doc.upload_date.isoformat(),
                        "policy_type": doc_data["metadata"].get("policy_type", "unknown")
                    } for doc_data in processed_docs]
                    
                    # Add to RAG pipeline
                    rag_pipeline.add_documents(texts, metadata)
                    
                    # Update document as processed
                    doc.is_processed = True
                    doc.chunk_count = len(texts)
                    doc.last_indexed = datetime.now()
                    
                    processed_count += 1
                    print(f"✅ Processed: {doc.original_filename} ({len(texts)} chunks)")
                    
                except Exception as e:
                    print(f"❌ Failed to process {doc.original_filename}: {str(e)}")
                    failed_count += 1
            
            # Commit all changes
            db.commit()
            
            print(f"\n🎉 Processing complete!")
            print(f"✅ Successfully processed: {processed_count} documents")
            print(f"❌ Failed: {failed_count} documents")
            
            if processed_count > 0:
                print("🚀 Documents are now searchable in the chatbot!")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_existing_documents()
