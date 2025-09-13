# 🤖 HR Chatbot - Simple Version

**No Database Required!** This simplified version uses file-based storage instead of a database, making it much more reliable and easier to deploy.

## ✨ Features

- **📄 File-based document storage** - No database needed
- **🔍 Advanced RAG pipeline** - FAISS + BM25 + CrossEncoder
- **🌐 Streamlit Cloud ready** - Works perfectly on cloud
- **📊 Simple admin panel** - Upload and manage documents
- **📝 JSON-based logging** - All activities logged to files
- **🚀 Easy deployment** - Just upload and run

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r simple_requirements.txt
```

### 2. Setup Environment
```bash
python simple_launcher.py setup
```

### 3. Run Applications
```bash
# Run both chat and admin
python simple_launcher.py both

# Or run separately
python simple_launcher.py chat    # Chat app on port 8501
python simple_launcher.py admin   # Admin panel on port 8502
```

## 📁 File Structure

```
hr-chatbot/
├── simple_app.py              # Main chat application
├── simple_admin.py            # Admin panel
├── simple_config.py           # Configuration
├── simple_rag_pipeline.py     # RAG pipeline
├── simple_launcher.py         # Launcher script
├── simple_requirements.txt    # Dependencies
├── documents/                 # Document storage
│   ├── HR/                   # HR documents
│   ├── IT/                   # IT documents
│   └── ...                   # Other departments
├── logs/                     # Activity logs
│   ├── queries.json          # Query logs
│   ├── uploads.json          # Upload logs
│   └── errors.json           # Error logs
└── index/                    # RAG indices
    ├── faiss_index           # FAISS vector index
    └── bm25.pkl              # BM25 keyword index
```

## 🔧 How It Works

### 1. Document Management
- **Upload PDFs** via admin panel
- **Organized by department** in folders
- **Automatic processing** into chunks
- **No database required**

### 2. RAG Pipeline
- **FAISS** for semantic search
- **BM25** for keyword search
- **CrossEncoder** for re-ranking
- **MMR** for diversity

### 3. Logging
- **JSON files** for all activities
- **Query logs** with responses
- **Upload logs** with metadata
- **Error logs** for debugging

## 🌐 Streamlit Cloud Deployment

### 1. Upload Files
Upload these files to your Streamlit Cloud repository:
- `simple_app.py`
- `simple_admin.py`
- `simple_config.py`
- `simple_rag_pipeline.py`
- `simple_requirements.txt`

### 2. Deploy Chat App
- **Main file:** `simple_app.py`
- **Port:** 8501
- **URL:** `https://your-app-name.streamlit.app/`

### 3. Deploy Admin Panel
- **Main file:** `simple_admin.py`
- **Port:** 8502
- **URL:** `https://your-app-name.streamlit.app/admin`

## 📊 Admin Panel Features

### Document Management
- **Upload PDFs** by department
- **View document list** with metadata
- **Delete documents** if needed
- **Real-time status** updates

### Analytics
- **Query statistics** by department
- **Upload statistics** tracking
- **Recent activity** monitoring
- **System status** overview

### System Management
- **RAG pipeline status** monitoring
- **Refresh indices** when needed
- **Clear logs** for maintenance
- **Export logs** for analysis

## 🔍 Troubleshooting

### Common Issues

1. **No documents found**
   - Upload documents via admin panel
   - Check department selection
   - Verify file permissions

2. **RAG pipeline not working**
   - Check OpenAI API key
   - Verify document processing
   - Refresh pipeline in admin panel

3. **Logs not appearing**
   - Check file permissions
   - Verify directory structure
   - Look for error messages

### Debug Mode
Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🆚 Simple vs Database Version

| Feature | Simple Version | Database Version |
|---------|----------------|------------------|
| **Setup** | ✅ Easy | ❌ Complex |
| **Deployment** | ✅ Reliable | ❌ Prone to errors |
| **Maintenance** | ✅ Simple | ❌ Complex |
| **File Storage** | ✅ Direct | ❌ Database required |
| **Logging** | ✅ JSON files | ❌ Database tables |
| **Cloud Ready** | ✅ Perfect | ❌ Connection issues |

## 🎯 Why Simple Version is Better

1. **No Database Issues** - No connection problems
2. **File-based Storage** - Documents stored as files
3. **JSON Logging** - Easy to read and analyze
4. **Cloud Ready** - Works perfectly on Streamlit Cloud
5. **Easy Maintenance** - Just manage files
6. **Reliable** - No database sync issues

## 📞 Support

If you encounter any issues:
1. Check the logs in `logs/` directory
2. Verify file permissions
3. Check OpenAI API key
4. Ensure documents are uploaded

**This simple version is much more reliable and easier to maintain!** 🎉
