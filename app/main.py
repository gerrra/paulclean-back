from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine
from app.models import Base
from app.api import auth, clients, orders, admin, public_pricing
from app.config import settings
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
# Base.metadata.create_all(bind=engine)  # Commented out to avoid index conflicts

# Create FastAPI app
app = FastAPI(
    title="Cleaning Service API",
    description="Backend API for cleaning service management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📥 {request.method} {request.url}")
    logger.info(f"📋 Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    logger.info(f"📤 Response status: {response.status_code}")
    return response

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(clients.router, prefix="/api", tags=["Client"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(public_pricing.router, prefix="/api", tags=["Public Pricing"])

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"❌ HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Cleaning Service API is running"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Cleaning Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
