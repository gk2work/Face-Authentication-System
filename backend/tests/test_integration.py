"""Integration tests for frontend-backend integration"""

import pytest
from pathlib import Path


def test_frontend_build_exists():
    """Test that frontend build directory exists"""
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    assert frontend_dist.exists(), "Frontend dist directory should exist"
    assert frontend_dist.is_dir(), "Frontend dist should be a directory"


def test_frontend_index_exists():
    """Test that frontend index.html exists"""
    frontend_index = Path(__file__).parent.parent.parent / "frontend" / "dist" / "index.html"
    assert frontend_index.exists(), "Frontend index.html should exist"
    assert frontend_index.is_file(), "Frontend index.html should be a file"


def test_frontend_assets_exist():
    """Test that frontend assets directory exists"""
    frontend_assets = Path(__file__).parent.parent.parent / "frontend" / "dist" / "assets"
    assert frontend_assets.exists(), "Frontend assets directory should exist"
    assert frontend_assets.is_dir(), "Frontend assets should be a directory"
    
    # Check that there are some assets
    assets = list(frontend_assets.glob("*"))
    assert len(assets) > 0, "Frontend assets directory should contain files"


def test_cors_configuration():
    """Test that CORS is properly configured"""
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware
    
    # Check that CORS middleware is added
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls == CORSMiddleware:
            cors_middleware = middleware
            break
    
    assert cors_middleware is not None, "CORS middleware should be configured"


def test_static_file_routes():
    """Test that static file serving routes are configured"""
    from app.main import app
    
    # Check that routes are configured
    routes = [route.path for route in app.routes]
    
    # In production mode (when frontend is built), we should have catch-all route
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        # Check for root route
        assert "/" in routes, "Root route should be configured"
        # Check for catch-all route
        assert "/{full_path:path}" in routes, "Catch-all route should be configured"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
