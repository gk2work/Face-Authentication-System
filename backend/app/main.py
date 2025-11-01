"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging import logger
from app.core.security import security_manager
from app.database.mongodb import mongodb_manager
from app.api.v1 import applications, auth, admin, monitoring, system, face_recognition, websocket, users, dashboard, identities, superadmin
from app.services.health_check_service import health_check_service
from datetime import datetime
import time

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Face Authentication and De-duplication System",
    description="""
    ## AI-powered Face Authentication System
    
    This system provides face authentication and de-duplication services for large-scale public examinations.
    
    ### Key Features:
    * **Face Recognition**: Detect and extract facial features from photographs
    * **De-duplication**: Identify duplicate applications using facial similarity
    * **Identity Management**: Assign and manage unique identity IDs
    * **Audit Logging**: Comprehensive audit trail for all operations
    * **Performance Optimized**: High-throughput processing with caching and batch operations
    
    ### API Endpoints:
    * **Applications**: Submit and track application processing
    * **Authentication**: Secure API access with JWT tokens
    * **Admin**: Administrative operations and overrides
    * **Monitoring**: System health and metrics
    * **System**: Health checks and readiness probes
    
    ### Security:
    * **JWT Authentication**: Bearer token authentication via Authorization header
    * **CSRF Protection**: Not required - JWT tokens in headers are immune to CSRF attacks
    * **Rate Limiting**: Most endpoints are rate-limited to prevent abuse
    * **Role-Based Access Control**: Granular permissions for different user roles
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Face Authentication System",
        "email": "support@faceauth.example.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and outgoing responses"""
    # Generate request ID
    request_id = f"{int(time.time() * 1000)}-{id(request)}"
    
    # Log request
    logger.info(
        f"Request started | ID: {request_id} | Method: {request.method} | "
        f"Path: {request.url.path} | Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request and measure time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed | ID: {request_id} | Status: {response.status_code} | "
            f"Duration: {process_time:.3f}s"
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed | ID: {request_id} | Error: {str(e)} | "
            f"Duration: {process_time:.3f}s"
        )
        raise


# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(identities.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(face_recognition.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(superadmin.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(system.health_router, prefix="/api/v1")  # Health endpoint without /system prefix

# CORS Configuration
# Configure allowed origins based on environment
if settings.ENVIRONMENT == "development":
    # In development, allow frontend dev server and localhost variations
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server default port
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",  # Vite dev server
        "http://127.0.0.1:8000",
    ]
    allow_credentials = True
    logger.info(f"CORS configured for development with origins: {allowed_origins}")
else:
    # In production, only allow same-origin requests
    # Frontend will be served from the same origin as the API
    allowed_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    allow_credentials = True
    logger.info(f"CORS configured for production with origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID", "X-Process-Time"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting Face Authentication System")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    
    # Validate environment variables
    if not security_manager.validate_environment_variables(
        mongodb_uri=settings.MONGODB_URI,
        secret_key=settings.SECRET_KEY
    ):
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
    
    # Start application processor for end-to-end workflow
    try:
        from app.services.application_processor import application_processor
        await application_processor.start()
        logger.info("Application processor started")
    except Exception as e:
        logger.error(f"Failed to start application processor: {str(e)}")
        # Don't raise - allow API to start even if processor fails


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Face Authentication System")
    
    # Stop application processor
    try:
        from app.services.application_processor import application_processor
        await application_processor.stop()
        logger.info("Application processor stopped")
    except Exception as e:
        logger.error(f"Error stopping application processor: {str(e)}")
    
    # Disconnect from MongoDB
    await mongodb_manager.disconnect()


# Static file serving for production frontend
# Check if frontend build directory exists
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_dist_path.exists() and frontend_dist_path.is_dir():
    # Mount static assets directory
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist_path / "assets")),
        name="static"
    )
    logger.info(f"Serving frontend static assets from {frontend_dist_path / 'assets'}")
    
    # Serve index.html for root and all non-API routes (SPA catch-all)
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend_root():
        """Serve frontend index.html for root path"""
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(content="<h1>Frontend not built</h1>", status_code=404)
    
    # Catch-all route for React Router (must be last)
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_frontend_spa(full_path: str):
        """
        Catch-all route to serve index.html for all non-API routes.
        This enables React Router to handle client-side routing.
        """
        # Don't intercept API routes, docs, or other backend routes
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "live", "ready", "dashboard")):
            return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)
        
        # Serve index.html for all other routes
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(content="<h1>Frontend not built</h1>", status_code=404)
    
    logger.info("Frontend serving configured - production mode")
else:
    # Development mode - frontend not built
    @app.get("/")
    async def root():
        """Root endpoint - development mode"""
        return {
            "service": "Face Authentication and De-duplication System",
            "version": "0.1.0",
            "status": "running",
            "mode": "development",
            "message": "Frontend should be run separately with 'npm run dev' in development mode"
        }
    logger.info("Frontend build not found - development mode (run frontend separately)")


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint for load balancers
    
    Returns basic health status:
    - 200: Service is healthy
    - 503: Service is unhealthy
    
    This endpoint is designed for load balancer health checks.
    It performs a quick database connectivity check.
    """
    from fastapi.responses import JSONResponse
    
    try:
        # Quick database check
        db_healthy = await mongodb_manager.health_check()
        
        if db_healthy:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "service": "face-auth-system",
                    "version": "1.0.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "face-auth-system",
                    "message": "Database connection failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "face-auth-system",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/live", tags=["System"])
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes
    
    Returns 200 if the application is running.
    This is a simple check that doesn't verify dependencies.
    
    Use this for Kubernetes liveness probes to detect if the
    application needs to be restarted.
    """
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "service": "face-auth-system",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/ready", tags=["System"])
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes and load balancers
    
    Returns comprehensive readiness status:
    - 200: Service is ready to accept traffic
    - 503: Service is not ready
    
    This endpoint performs comprehensive checks including:
    - Database connectivity
    - Service dependencies
    - System resources
    
    Use this for Kubernetes readiness probes and load balancer health checks
    that need detailed status information.
    """
    from fastapi.responses import JSONResponse
    
    try:
        health_status = await health_check_service.get_comprehensive_health(mongodb_manager)
        health_status["timestamp"] = datetime.utcnow().isoformat()
        health_status["version"] = "1.0.0"
        
        # Return 503 if unhealthy
        status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard():
    """Monitoring dashboard"""
    dashboard_path = Path(__file__).parent / "templates" / "dashboard.html"
    
    if dashboard_path.exists():
        return dashboard_path.read_text()
    else:
        return "<html><body><h1>Dashboard not found</h1></body></html>"
