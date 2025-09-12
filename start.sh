#!/bin/bash

# AIPL Enterprise RAG Chatbot - Startup Script

echo "🏢 AIPL Enterprise RAG Chatbot"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
# AIPL Enterprise RAG Chatbot - Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///hr_chatbot.db
EOF
    echo "📝 Please edit .env file with your API keys before running the application."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads/{HR,IT,SALES,MARKETING,ACCOUNTS,FACTORY,CO-ORDINATION}
mkdir -p index static templates logs

# Run the application
echo "🚀 Starting application..."
python main.py both
