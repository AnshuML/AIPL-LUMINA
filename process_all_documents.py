#!/usr/bin/env python3
"""
Process all unprocessed documents in the database
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def process_all_documents():
    """Process all unprocessed documents"""
    print("🔄 Processing all unprocessed documents...")
    
    try:
        from models import get_db, Document, DocumentChunk
        from utils.pdf_processor import process_pdfs
        from rag_pipeline import get_rag_pipeline
        from datetime import datetime
        
        db = next(get_db())
        try:
            # Get all unprocessed documents
            unprocessed_docs = db.query(Document).filter(Document.is_processed == False).all()
            print(f"📄 Found {len(unprocessed_docs)} unprocessed documents")
            
            if not unprocessed_docs:
                print("✅ No unprocessed documents found")
                return
            
            # Process each document
            rag_pipeline = get_rag_pipeline()
            processed_count = 0
            
            for doc in unprocessed_docs:
                print(f"📄 Processing: {doc.filename} (Department: {doc.department})")
                
                try:
                    # Check if file exists
                    if not os.path.exists(doc.file_path):
                        print(f"⚠️ File not found: {doc.file_path}")
                        continue
                    
                    # Process the PDF
                    processed_docs = process_pdfs([doc.file_path])
                    texts = [doc_data["content"] for doc_data in processed_docs]
                    
                    if not texts:
                        print(f"⚠️ No text extracted from: {doc.filename}")
                        continue
                    
                    # Create document chunks in database
                    for i, text in enumerate(texts):
                        chunk = DocumentChunk(
                            document_id=doc.id,
                            chunk_index=i,
                            content=text,
                            chunk_metadata={
                                "filename": doc.original_filename,
                                "department": doc.department,
                                "file_path": doc.file_path,
                                "upload_date": doc.upload_date.isoformat()
                            }
                        )
                        db.add(chunk)
                    
                    # Update document as processed
                    doc.is_processed = True
                    doc.chunk_count = len(texts)
                    doc.last_indexed = datetime.utcnow()
                    
                    # Add to RAG pipeline
                    rag_pipeline.add_documents(
                        texts=texts,
                        metadata=[{
                            "filename": doc.original_filename,
                            "department": doc.department,
                            "file_path": doc.file_path,
                            "upload_date": doc.upload_date.isoformat()
                        }] * len(texts)
                    )
                    
                    processed_count += 1
                    print(f"✅ Processed: {doc.filename} ({len(texts)} chunks)")
                    
                except Exception as e:
                    print(f"❌ Error processing {doc.filename}: {e}")
                    continue
            
            # Commit all changes
            db.commit()
            print(f"✅ Successfully processed {processed_count} documents")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_all_documents()
