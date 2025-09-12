@echo off
REM AIPL Enterprise RAG Chatbot - Windows Startup Script

echo 🏢 AIPL Enterprise RAG Chatbot
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check environment variables
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from template...
    (
        echo # AIPL Enterprise RAG Chatbot - Environment Variables
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo SECRET_KEY=your_secret_key_here
        echo DATABASE_URL=sqlite:///hr_chatbot.db
    ) > .env
    echo 📝 Please edit .env file with your API keys before running the application.
    pause
    exit /b 1
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist "uploads" mkdir uploads
if not exist "uploads\HR" mkdir uploads\HR
if not exist "uploads\IT" mkdir uploads\IT
if not exist "uploads\SALES" mkdir uploads\SALES
if not exist "uploads\MARKETING" mkdir uploads\MARKETING
if not exist "uploads\ACCOUNTS" mkdir uploads\ACCOUNTS
if not exist "uploads\FACTORY" mkdir uploads\FACTORY
if not exist "uploads\CO-ORDINATION" mkdir uploads\CO-ORDINATION
if not exist "index" mkdir index
if not exist "static" mkdir static
if not exist "templates" mkdir templates
if not exist "logs" mkdir logs

REM Run the application
echo 🚀 Starting application...
python main.py both

pause
