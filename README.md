# 🤖 AIPL Lumina HR Chatbot

A modern, intelligent HR chatbot with login system and admin panel for managing company policies and procedures.

## ✨ Features

- **🔐 Secure Login System** - Email and name-based authentication
- **💬 Intelligent Chat** - Context-aware responses based on company documents
- **🏢 Department Support** - HR, IT, Sales, Marketing, Accounts, Factory, Co-ordination
- **🌐 Multi-language** - Support for 11 languages
- **⚙️ Admin Panel** - Document management and analytics
- **📊 Comprehensive Logging** - User activity, queries, and performance metrics
- **🎨 Dark Theme** - Modern, professional interface

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r simple_requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your OpenAI API key
# Get your API key from: https://platform.openai.com/api-keys
```

**Or set environment variable directly:**
```bash
# Windows
$env:OPENAI_API_KEY="your-openai-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. Run the Application
```bash
# Run with login system
python simple_launcher.py chat

# Run both chat and admin
python simple_launcher.py both
```

### 3. Access the Application
- **Main App (with Login):** http://localhost:8501
- **Admin Panel:** http://localhost:8502

## 📁 Project Structure

```
hr-chatbot/
├── main_app.py              # Main app with login system
├── simple_app.py            # Chat interface
├── simple_admin.py          # Admin panel
├── simple_config.py         # Configuration
├── simple_rag_pipeline.py   # RAG pipeline
├── simple_launcher.py       # Application launcher
├── login.py                 # Login page
├── documents/               # PDF documents by department
├── logs/                    # User activity logs
├── index/                   # FAISS and BM25 indices
└── utils/                   # Utility functions
```

## 🔧 How to Use

### For Users:
1. **Login** - Enter your email and name
2. **Select Department** - Choose your department
3. **Select Language** - Choose your preferred language
4. **Start Chatting** - Ask questions about company policies

### For Admins:
1. **Access Admin Panel** - Go to http://localhost:8502
2. **Upload Documents** - Add PDF files for each department
3. **View Analytics** - Monitor user activity and queries
4. **Manage Logs** - View detailed user interactions

## 📊 Logging System

The system captures comprehensive information:
- **User Details** - Email, name, department, language
- **Query Information** - Question, answer, response time
- **Performance Metrics** - Confidence level, chunks used, sources
- **System Data** - Model used, timestamp, error logs

## 🎨 Features

### Login System:
- Email and name validation
- Department and language selection
- Session management
- User activity logging

### Chat Interface:
- Dark theme design
- Real-time responses
- Source citations
- Confidence indicators
- Multi-language support

### Admin Panel:
- Document management
- User analytics
- Query statistics
- System monitoring
- Log export

## 🔒 Security

- Session-based authentication
- User activity tracking
- Secure document storage
- No database dependencies

## 📈 Analytics

Track user engagement with:
- Query counts by department
- User activity patterns
- Response time metrics
- Document usage statistics
- Error monitoring

## 🌐 Deployment

The application is designed to work both locally and on cloud platforms like Streamlit Cloud.

## 📞 Support

For technical support or questions, contact the development team.
#python simple_launcher.py both

---

**Powered by AIPL Lumina | Your Intelligent HR Assistant** 🤖
