# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p documents logs index

# Create department subdirectories
RUN mkdir -p documents/HR documents/IT documents/SALES documents/MARKETING documents/ACCOUNTS documents/FACTORY documents/CO-ORDINATION
RUN mkdir -p logs/HR logs/IT logs/SALES logs/MARKETING logs/ACCOUNTS logs/FACTORY logs/CO-ORDINATION
RUN mkdir -p index/HR index/IT index/SALES index/MARKETING index/ACCOUNTS index/FACTORY index/CO-ORDINATION

# Expose port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "simple_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
