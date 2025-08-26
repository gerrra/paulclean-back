#!/usr/bin/env python3
"""
Startup script for Cleaning Service API
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting Cleaning Service API...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc Documentation: http://localhost:8000/redoc")
    print("🏥 Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
