# Use Python 3.11 slim image as base
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Fix bcrypt compatibility issue
RUN pip install --no-cache-dir bcrypt==4.0.1

# Copy application code
COPY . .

# Create non-root user (commented out to avoid permission issues with mounted volumes)
# RUN adduser --disabled-password --gecos '' appuser \
#     && chown -R appuser:appuser /app
# USER appuser

# Expose port
EXPOSE 8000

# Health check - disabled due to compatibility issues
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "📁 Creating data directory..."\n\
mkdir -p /app/data\n\
echo "🔄 Running database migrations..."\n\
alembic upgrade head\n\
echo "🚀 Starting FastAPI server..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]
