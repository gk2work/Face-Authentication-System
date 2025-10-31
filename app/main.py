"""Main FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.database.mongodb import mongodb_manager
from app.api.v1 import applications

app = FastAPI(
    title="Face Authentication and De-duplication System",
    description="AI-powered face authentication system for large-scale public examinations",
    version="0.1.0",
)

# Include API routers
app.include_router(applications.router, prefix="/api/v1")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting Face Authentication System")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    
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
