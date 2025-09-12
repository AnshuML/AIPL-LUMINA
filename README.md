# 🏢 AIPL Enterprise RAG Chatbot

A world-class, enterprise-grade RAG (Retrieval-Augmented Generation) chatbot and admin panel built for Ajit Industries Pvt. Ltd. This system provides intelligent document-based assistance with department-specific knowledge, multilingual support, and comprehensive analytics.

## ✨ Features

### 🤖 Chat Application
- **Department Selection**: Force users to select from HR, IT, SALES, MARKETING, ACCOUNTS, FACTORY, CO-ORDINATION
- **Language Detection**: Auto-detect user language with manual override options
- **Hybrid RAG Pipeline**: Combines FAISS vector search with BM25 keyword search
- **Source Attribution**: Every answer includes proper source citations
- **Confidence Scoring**: High/Medium/Low confidence indicators
- **Streaming Responses**: Real-time token streaming for better UX
- **Support Tickets**: Automatic escalation for sensitive queries

### 🛠️ Admin Panel (Dark Theme)
- **Document Management**: Upload, process, and manage documents by department
- **Audit Logs**: Complete query history with filtering and export capabilities
- **Analytics Dashboard**: Interactive charts and metrics
- **User Management**: Role-based access control
- **System Configuration**: Configurable parameters and settings

### 🔐 Security & Compliance
- **Domain Restrictions**: Only @aiplabro.com and @ajitindustries.com emails allowed
- **JWT Authentication**: Secure token-based authentication
- **Audit Logging**: Complete audit trail for all actions
- **Data Encryption**: At rest and in transit
- **Rate Limiting**: Configurable API rate limits

### 🌍 Multilingual Support
- **Auto-Detection**: Automatic language detection from user input
- **11 Languages**: English, Hindi, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese
- **Consistent Formatting**: Proper answer formatting in user's preferred language

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hr-chatbot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   python main.py install
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   python main.py both
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here

# Optional
DATABASE_URL=sqlite:///hr_chatbot.db
GOOGLE_API_KEY=your_google_api_key_here
```

## 📖 Usage

### Starting the Application

```bash
# Run both chat and admin panel
python main.py both

# Run only chat application
python main.py chat

# Run only admin panel
python main.py admin

# Install dependencies only
python main.py install

# Setup directories and check environment
python main.py setup
```

### Access Points

- **Chat Application**: http://localhost:8501
- **Admin Panel**: http://localhost:8000

### First Time Setup

1. **Access Admin Panel**: Go to http://localhost:8000
2. **Upload Documents**: Use the Documents tab to upload PDFs by department
3. **Configure System**: Set up system parameters in Settings
4. **Test Chat**: Go to http://localhost:8501 to test the chat interface

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Streamlit (Chat Interface)
- HTML/CSS/JavaScript (Admin Panel)
- Bootstrap 5 (UI Framework)
- Chart.js & Plotly (Analytics)

**Backend:**
- FastAPI (Admin API)
- SQLAlchemy (ORM)
- PostgreSQL/SQLite (Database)

**RAG Pipeline:**
- FAISS (Vector Search)
- BM25 (Keyword Search)
- OpenAI Embeddings
- Cross-Encoder Re-ranking
- MMR (Maximal Marginal Relevance)

**ML/AI:**
- OpenAI GPT-4/3.5-turbo
- Sentence Transformers
- LangChain

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Database      │
│   Chat App      │◄──►│   Admin API     │◄──►│   (PostgreSQL)  │
│   (Port 8501)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Pipeline  │    │   File Storage  │    │   Vector Store  │
│   (Hybrid)      │    │   (Local/S3)    │    │   (FAISS)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Admin Panel Features

### Documents Tab
- Upload documents by department
- Process and index PDFs automatically
- View processing status and chunk counts
- Re-index documents
- Delete documents

### Logs Tab
- Complete query history
- Advanced filtering (date, department, user, confidence)
- Export to CSV/PDF
- Search functionality
- Pagination

### Analytics Tab
- Interactive charts and graphs
- Department-wise query distribution
- Response time analytics
- Confidence score distribution
- Language usage statistics
- Top queries analysis

## 🔧 Configuration

### RAG Pipeline Settings

```python
# In rag_pipeline.py
config = {
    "embedding_model": "text-embedding-3-large",
    "chunk_size": 400,
    "chunk_overlap": 80,
    "faiss_path": "index/faiss_index",
    "bm25_path": "index/bm25.pkl"
}
```

### System Configuration

Access the Settings tab in the admin panel to configure:
- Chunk size and overlap
- Search parameters (K_dense, K_sparse)
- Re-ranking settings
- MMR lambda parameter
- Model selection
- Rate limits

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   python main.py install
   ```

2. **Database Connection Issues**
   - Check DATABASE_URL in .env
   - Ensure database is running

3. **OpenAI API Errors**
   - Verify OPENAI_API_KEY is correct
   - Check API quota and billing

4. **Port Already in Use**
   ```bash
   # Kill processes on ports 8501 and 8000
   lsof -ti:8501 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

### Logs

Check application logs in the `logs/` directory for detailed error information.

## 🔒 Security Considerations

- All API endpoints require authentication
- Domain restrictions enforced at application level
- JWT tokens expire after 30 minutes
- All user actions are logged for audit
- Sensitive data is properly handled and redacted

## 📈 Performance

### Optimization Tips

1. **Vector Index**: Use FAISS with appropriate index type
2. **Caching**: Implement Redis for frequently accessed data
3. **Database**: Use connection pooling
4. **Chunking**: Optimize chunk size for your documents
5. **Re-ranking**: Adjust re-ranking parameters based on your data

### Monitoring

- Response time metrics
- Query success rates
- Error rates
- Resource usage
- User activity patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is proprietary software owned by Ajit Industries Pvt. Ltd.

## 📞 Support

For technical support or questions:
- Email: support@aiplabro.com
- Internal: Contact IT department
- Documentation: See admin panel help section

## 🔄 Updates

### Version 1.0.0
- Initial release
- Full RAG pipeline implementation
- Admin panel with all features
- Multilingual support
- Security and compliance features

---

**Built with ❤️ for Ajit Industries Pvt. Ltd.**
