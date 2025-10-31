"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging import logger
from app.core.security import security_manager
from app.database.mongodb import mongodb_manager
from app.api.v1 import applications, auth
from app.api.v1 import admin

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Face Authentication and De-duplication System",
    description="AI-powered face authentication system for large-scale public examinations",
    version="0.1.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

# CORS Configuration
# In production, replace with specific allowed origins
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Allow all origins in development, specific origins in production
if settings.ENVIRONMENT == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting Face Authentication System")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    
    # Validate environment variables
    if not security_manager.validate_environment_variables():
        logger.error("Environment validation failed")
        raise RuntimeError("Required environment variables are not properly configured")
    
    # Initialize storage security
    security_manager.initialize_storage_security(settings.STORAGE_PATH)
    security_manager.initialize_storage_security(settings.VECTOR_DB_PATH)
    
    # Connect to MongoDB
    try:
        await mongodb_manager.connect()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Face Authentication System")
    
    # Disconnect from MongoDB
    await mongodb_manager.disconnect()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Face Authentication and De-duplication System",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "face-auth-system"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    checks = {
        "database": "ok" if await mongodb_manager.health_check() else "failed",
        "cache": "ok",  # TODO: Add Redis health check
        "vector_db": "ok"  # TODO: Add FAISS health check
    }
    
    status = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"
    
    return {
        "status": status,
        "checks": checks
    }
