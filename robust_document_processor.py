#!/usr/bin/env python3
"""
Robust Document Processor for HR Chatbot
Automatically processes new documents and rebuilds indices
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_rag_pipeline import SimpleRAGPipeline
from simple_config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor(FileSystemEventHandler):
    """Handles document changes and automatically rebuilds indices"""
    
    def __init__(self):
        self.rag_pipeline = None
        self.last_processed = {}
        self.processing_delay = 5  # Wait 5 seconds before processing
        
    def initialize_rag_pipeline(self):
        """Initialize RAG pipeline"""
        try:
            self.rag_pipeline = SimpleRAGPipeline()
            logger.info("✅ RAG Pipeline initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG pipeline: {e}")
            return False
    
    def should_process_file(self, file_path):
        """Check if file should be processed"""
        if not file_path.endswith('.pdf'):
            return False
            
        # Check if file is in documents directory
        if 'documents' not in str(file_path):
            return False
            
        # Check if file was recently processed
        current_time = time.time()
        if file_path in self.last_processed:
            if current_time - self.last_processed[file_path] < 30:  # 30 seconds cooldown
                return False
                
        return True
    
    def process_document(self, file_path):
        """Process a single document"""
        try:
            logger.info(f"📄 Processing document: {file_path}")
            
            # Update last processed time
            self.last_processed[file_path] = time.time()
            
            # Rebuild indices
            if self.rag_pipeline:
                self.rag_pipeline.rebuild_indices()
                logger.info(f"✅ Successfully processed {file_path}")
            else:
                logger.error("❌ RAG pipeline not initialized")
                
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
    
    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info(f"📁 New file detected: {event.src_path}")
            time.sleep(self.processing_delay)  # Wait for file to be fully written
            self.process_document(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info(f"📝 File modified: {event.src_path}")
            time.sleep(self.processing_delay)
            self.process_document(event.src_path)
    
    def on_moved(self, event):
        """Handle file move"""
        if not event.is_directory and self.should_process_file(event.dest_path):
            logger.info(f"📦 File moved: {event.dest_path}")
            time.sleep(self.processing_delay)
            self.process_document(event.dest_path)

class RobustDocumentProcessor:
    """Main class for robust document processing"""
    
    def __init__(self):
        self.observer = None
        self.processor = DocumentProcessor()
        self.documents_path = Path("documents")
        
    def start_monitoring(self):
        """Start monitoring documents directory"""
        try:
            # Initialize RAG pipeline
            if not self.processor.initialize_rag_pipeline():
                logger.error("❌ Failed to initialize RAG pipeline")
                return False
            
            # Create documents directory if it doesn't exist
            self.documents_path.mkdir(exist_ok=True)
            
            # Start file monitoring
            self.observer = Observer()
            self.observer.schedule(self.processor, str(self.documents_path), recursive=True)
            self.observer.start()
            
            logger.info(f"🔍 Started monitoring: {self.documents_path}")
            logger.info("📄 Document processor is running...")
            logger.info("Press Ctrl+C to stop")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting document processor: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop monitoring documents directory"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 Document processor stopped")
    
    def process_all_documents(self):
        """Process all existing documents"""
        try:
            logger.info("🔄 Processing all existing documents...")
            
            if not self.processor.initialize_rag_pipeline():
                logger.error("❌ Failed to initialize RAG pipeline")
                return False
            
            # Get all documents
            documents = config.get_documents()
            logger.info(f"📄 Found {len(documents)} documents to process")
            
            # Rebuild indices
            self.processor.rag_pipeline.rebuild_indices()
            logger.info("✅ All documents processed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing all documents: {e}")
            return False

def main():
    """Main function"""
    print("🚀 Starting Robust Document Processor...")
    print("=" * 50)
    
    processor = RobustDocumentProcessor()
    
    try:
        # Process existing documents first
        processor.process_all_documents()
        
        # Start monitoring for new documents
        if processor.start_monitoring():
            # Keep running
            while True:
                time.sleep(1)
        else:
            logger.error("❌ Failed to start document processor")
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopping document processor...")
        processor.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        processor.stop_monitoring()

if __name__ == "__main__":
    main()
