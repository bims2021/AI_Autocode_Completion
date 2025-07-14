
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import uuid
import time
import logging

from .routes.completion import completion_router
from .utils.logger import setup_logger
from .utils.config import get_settings
from .models.response_models import ErrorResponse

# Setup logging
logger = setup_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AI Code Completion API",
    description="Backend API for AI-powered code completion",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)
# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return ErrorResponse(
        error="validation_error",
        message=str(exc),
        status_code=400
    )
    
@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return ErrorResponse(
        error="internal_error",
        message="An unexpected error occurred",
        status_code=500
    )    

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    processing_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time"] = str(processing_time)
    
    return response



@app.get("/")
async def read_root():
    """Root endpoint for the API."""
    return {"message": "Welcome to the AI Code Completion API!"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }
    
# Include routers
app.include_router(completion_router, prefix="/api/v1")    

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )