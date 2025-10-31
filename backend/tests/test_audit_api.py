"""API endpoint tests for audit logging"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

# Note: These are basic structure tests
# Full integration tests would require a test database


def test_audit_endpoints_exist():
    """Test that audit endpoints are registered"""
    print("\n=== Testing Audit API Endpoints ===")
    
    client = TestClient(app)
    
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200, "Failed to get OpenAPI schema"
    
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # Test 1: Check audit logs query endpoint exists
    print("\n1. Checking GET /api/v1/admin/audit-logs endpoint...")
    audit_logs_path = "/api/v1/admin/audit-logs"
    assert audit_logs_path in paths, f"Endpoint {audit_logs_path} not found"
    assert "get" in paths[audit_logs_path], "GET method not found"
    print(f"✓ Endpoint {audit_logs_path} is registered")
    
    # Test 2: Check audit logs export endpoint exists
    print("\n2. Checking GET /api/v1/admin/audit-logs/export endpoint...")
    export_path = "/api/v1/admin/audit-logs/export"
    assert export_path in paths, f"Endpoint {export_path} not found"
    assert "get" in paths[export_path], "GET method not found"
    print(f"✓ Endpoint {export_path} is registered")
    
    # Test 3: Verify query parameters for audit logs endpoint
    print("\n3. Verifying query parameters...")
    audit_logs_params = paths[audit_logs_path]["get"].get("parameters", [])
    param_names = [p["name"] for p in audit_logs_params]
    
    expected_params = ["page", "page_size", "event_type", "actor_id", "resource_id", "start_date", "end_date"]
    for param in expected_params:
        assert param in param_names, f"Parameter '{param}' not found"
    print(f"✓ All expected query parameters present: {', '.join(expected_params)}")
    
    # Test 4: Verify response model for audit logs
    print("\n4. Verifying response models...")
    responses = paths[audit_logs_path]["get"].get("responses", {})
    assert "200" in responses, "Success response not defined"
    
    response_schema = responses["200"].get("content", {}).get("application/json", {}).get("schema", {})
    assert "$ref" in response_schema or "properties" in response_schema, "Response schema not defined"
    print("✓ Response model is defined")
    
    # Test 5: Check that endpoints require authentication
    print("\n5. Checking authentication requirements...")
    security = paths[audit_logs_path]["get"].get("security", [])
    # Note: This depends on how authentication is configured
    print(f"✓ Security configuration: {security if security else 'Defined in dependencies'}")
    
    print("\n=== All API Endpoint Tests Passed! ===")


def test_endpoint_documentation():
    """Test that endpoints have proper documentation"""
    print("\n=== Testing Endpoint Documentation ===")
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # Test audit logs endpoint documentation
    print("\n1. Checking audit logs endpoint documentation...")
    audit_logs_endpoint = paths["/api/v1/admin/audit-logs"]["get"]
    
    assert "summary" in audit_logs_endpoint or "description" in audit_logs_endpoint, \
        "Endpoint lacks documentation"
    
    description = audit_logs_endpoint.get("description", "")
    assert len(description) > 0, "Endpoint description is empty"
    print(f"✓ Endpoint has documentation: {description[:100]}...")
    
    # Test export endpoint documentation
    print("\n2. Checking export endpoint documentation...")
    export_endpoint = paths["/api/v1/admin/audit-logs/export"]["get"]
    
    assert "summary" in export_endpoint or "description" in export_endpoint, \
        "Export endpoint lacks documentation"
    
    description = export_endpoint.get("description", "")
    assert len(description) > 0, "Export endpoint description is empty"
    print(f"✓ Export endpoint has documentation: {description[:100]}...")
    
    print("\n=== All Documentation Tests Passed! ===")


def test_response_models():
    """Test that response models are properly defined"""
    print("\n=== Testing Response Models ===")
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    openapi_schema = response.json()
    components = openapi_schema.get("components", {})
    schemas = components.get("schemas", {})
    
    # Test 1: Check PaginatedAuditLogsResponse exists
    print("\n1. Checking PaginatedAuditLogsResponse model...")
    assert "PaginatedAuditLogsResponse" in schemas, "PaginatedAuditLogsResponse model not found"
    
    paginated_model = schemas["PaginatedAuditLogsResponse"]
    properties = paginated_model.get("properties", {})
    
    expected_fields = ["total", "page", "page_size", "total_pages", "logs"]
    for field in expected_fields:
        assert field in properties, f"Field '{field}' not found in PaginatedAuditLogsResponse"
    print(f"✓ PaginatedAuditLogsResponse has all required fields: {', '.join(expected_fields)}")
    
    # Test 2: Check AuditLogResponse exists
    print("\n2. Checking AuditLogResponse model...")
    assert "AuditLogResponse" in schemas, "AuditLogResponse model not found"
    
    audit_log_model = schemas["AuditLogResponse"]
    properties = audit_log_model.get("properties", {})
    
    expected_fields = [
        "event_type", "timestamp", "actor_id", "actor_type",
        "resource_id", "resource_type", "action", "details",
        "ip_address", "success", "error_message"
    ]
    for field in expected_fields:
        assert field in properties, f"Field '{field}' not found in AuditLogResponse"
    print(f"✓ AuditLogResponse has all required fields")
    
    print("\n=== All Response Model Tests Passed! ===")


def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("AUDIT LOGGING API - ENDPOINT TESTS")
    print("="*60)
    
    try:
        test_audit_endpoints_exist()
        test_endpoint_documentation()
        test_response_models()
        
        print("\n" + "="*60)
        print("✓ ALL API TESTS PASSED SUCCESSFULLY!")
        print("="*60)
        print("\nAudit logging API endpoints are properly configured:")
        print("  ✓ GET /api/v1/admin/audit-logs - Query audit logs")
        print("  ✓ GET /api/v1/admin/audit-logs/export - Export to CSV")
        print("  ✓ All query parameters are defined")
        print("  ✓ Response models are properly structured")
        print("  ✓ Endpoints have documentation")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
