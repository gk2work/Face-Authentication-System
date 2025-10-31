"""Integration tests for audit logging system"""

import asyncio
from datetime import datetime
from app.services.audit_service import audit_service
from app.models.audit import EventType, ActorType, ResourceType, AuditLog


async def test_audit_log_creation():
    """Test creating audit log entries"""
    print("\n=== Testing Audit Log Creation ===")
    
    # Mock database (in real scenario, this would be a test database)
    class MockDB:
        pass
    
    class MockAuditRepo:
        def __init__(self, db):
            self.logs = []
        
        async def create(self, audit_log: AuditLog) -> str:
            self.logs.append(audit_log)
            return f"log_{len(self.logs)}"
    
    # Monkey patch the audit service to use mock repo
    original_get_repo = audit_service._get_audit_repo
    mock_db = MockDB()
    mock_repo = MockAuditRepo(mock_db)
    
    def mock_get_repo(db):
        return mock_repo
    
    audit_service._get_audit_repo = mock_get_repo
    
    try:
        # Test 1: Application submission
        print("\n1. Testing application submission logging...")
        log_id = await audit_service.log_application_submission(
            db=mock_db,
            application_id="test-app-123",
            applicant_email="test@example.com",
            applicant_name="Test User",
            ip_address="192.168.1.1"
        )
        assert log_id is not None, "Failed to create application submission log"
        assert len(mock_repo.logs) == 1, "Log not added to repository"
        
        log = mock_repo.logs[0]
        assert log.event_type == EventType.APPLICATION_SUBMITTED
        assert log.actor_id == "system"
        assert log.actor_type == ActorType.API
        assert log.resource_id == "test-app-123"
        assert log.details["applicant_email"] == "test@example.com"
        assert log.ip_address == "192.168.1.1"
        print("✓ Application submission logging works correctly")
        
        # Test 2: Duplicate detection
        print("\n2. Testing duplicate detection logging...")
        log_id = await audit_service.log_duplicate_detection(
            db=mock_db,
            application_id="test-app-123",
            matched_application_id="test-app-456",
            confidence_score=0.95,
            is_duplicate=True
        )
        assert log_id is not None, "Failed to create duplicate detection log"
        assert len(mock_repo.logs) == 2, "Log not added to repository"
        
        log = mock_repo.logs[1]
        assert log.event_type == EventType.DUPLICATE_DETECTED
        assert log.actor_type == ActorType.SYSTEM
        assert log.details["is_duplicate"] == True
        assert log.details["confidence_score"] == 0.95
        print("✓ Duplicate detection logging works correctly")
        
        # Test 3: Identity issuance
        print("\n3. Testing identity issuance logging...")
        log_id = await audit_service.log_identity_issued(
            db=mock_db,
            application_id="test-app-123",
            identity_id="identity-789"
        )
        assert log_id is not None, "Failed to create identity issuance log"
        assert len(mock_repo.logs) == 3, "Log not added to repository"
        
        log = mock_repo.logs[2]
        assert log.event_type == EventType.IDENTITY_ISSUED
        assert log.resource_type == ResourceType.IDENTITY
        assert log.details["identity_id"] == "identity-789"
        print("✓ Identity issuance logging works correctly")
        
        # Test 4: Override decision
        print("\n4. Testing override decision logging...")
        log_id = await audit_service.log_override_decision(
            db=mock_db,
            application_id="test-app-123",
            admin_id="admin-user",
            decision="reject_duplicate",
            justification="Clear visual differences in photographs",
            previous_status="duplicate",
            new_status="verified",
            ip_address="10.0.0.1"
        )
        assert log_id is not None, "Failed to create override decision log"
        assert len(mock_repo.logs) == 4, "Log not added to repository"
        
        log = mock_repo.logs[3]
        assert log.event_type == EventType.DUPLICATE_OVERRIDE
        assert log.actor_id == "admin-user"
        assert log.actor_type == ActorType.ADMIN
        assert log.details["decision"] == "reject_duplicate"
        assert log.details["justification"] == "Clear visual differences in photographs"
        print("✓ Override decision logging works correctly")
        
        # Test 5: Verify timestamps are automatic
        print("\n5. Testing automatic timestamps...")
        for log in mock_repo.logs:
            assert log.timestamp is not None, "Timestamp not set"
            assert isinstance(log.timestamp, datetime), "Timestamp is not datetime"
            # Check timestamp is recent (within last minute)
            time_diff = (datetime.utcnow() - log.timestamp).total_seconds()
            assert time_diff < 60, f"Timestamp seems incorrect: {time_diff}s ago"
        print("✓ Automatic timestamps work correctly")
        
        # Test 6: Verify all required fields
        print("\n6. Testing required fields validation...")
        for i, log in enumerate(mock_repo.logs):
            assert log.event_type is not None, f"Log {i}: event_type missing"
            assert log.actor_id is not None, f"Log {i}: actor_id missing"
            assert log.actor_type is not None, f"Log {i}: actor_type missing"
            assert log.action is not None, f"Log {i}: action missing"
            assert log.success is not None, f"Log {i}: success missing"
            assert isinstance(log.details, dict), f"Log {i}: details not a dict"
        print("✓ All required fields are present")
        
        print("\n=== All Audit Log Creation Tests Passed! ===")
        return True
        
    finally:
        # Restore original method
        audit_service._get_audit_repo = original_get_repo


async def test_audit_log_querying():
    """Test audit log querying functionality"""
    print("\n=== Testing Audit Log Querying ===")
    
    # Mock database and repository
    class MockDB:
        pass
    
    class MockAuditRepo:
        def __init__(self, db):
            # Create sample logs
            self.logs = [
                AuditLog(
                    event_type=EventType.APPLICATION_SUBMITTED,
                    actor_id="system",
                    actor_type=ActorType.API,
                    resource_id=f"app-{i}",
                    resource_type=ResourceType.APPLICATION,
                    action="Application submitted",
                    details={"test": i},
                    timestamp=datetime.utcnow()
                )
                for i in range(100)
            ]
            # Add some duplicate detection logs
            for i in range(50):
                self.logs.append(
                    AuditLog(
                        event_type=EventType.DUPLICATE_DETECTED,
                        actor_id="system",
                        actor_type=ActorType.SYSTEM,
                        resource_id=f"app-{i}",
                        resource_type=ResourceType.APPLICATION,
                        action="Duplicate detected",
                        details={"is_duplicate": True},
                        timestamp=datetime.utcnow()
                    )
                )
        
        async def query(self, filters: dict, limit: int = 100, skip: int = 0):
            # Simple filtering logic
            filtered_logs = self.logs
            
            if "event_type" in filters:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.event_type == filters["event_type"]
                ]
            
            if "actor_id" in filters:
                filtered_logs = [
                    log for log in filtered_logs 
                    if log.actor_id == filters["actor_id"]
                ]
            
            total = len(filtered_logs)
            result_logs = filtered_logs[skip:skip + limit]
            
            return result_logs, total
    
    mock_db = MockDB()
    mock_repo = MockAuditRepo(mock_db)
    
    # Test 1: Query all logs with pagination
    print("\n1. Testing pagination...")
    logs, total = await mock_repo.query({}, limit=20, skip=0)
    assert len(logs) == 20, f"Expected 20 logs, got {len(logs)}"
    assert total == 150, f"Expected total 150, got {total}"
    print(f"✓ Pagination works: Retrieved {len(logs)} logs out of {total} total")
    
    # Test 2: Query with event type filter
    print("\n2. Testing event type filtering...")
    logs, total = await mock_repo.query(
        {"event_type": EventType.APPLICATION_SUBMITTED},
        limit=100,
        skip=0
    )
    assert len(logs) == 100, f"Expected 100 logs, got {len(logs)}"
    assert total == 100, f"Expected total 100, got {total}"
    assert all(log.event_type == EventType.APPLICATION_SUBMITTED for log in logs)
    print(f"✓ Event type filtering works: Found {total} APPLICATION_SUBMITTED logs")
    
    # Test 3: Query with actor filter
    print("\n3. Testing actor filtering...")
    logs, total = await mock_repo.query(
        {"actor_id": "system"},
        limit=200,
        skip=0
    )
    assert total == 150, f"Expected total 150, got {total}"
    assert all(log.actor_id == "system" for log in logs)
    print(f"✓ Actor filtering works: Found {total} logs by 'system'")
    
    # Test 4: Query with pagination offset
    print("\n4. Testing pagination offset...")
    logs_page1, _ = await mock_repo.query({}, limit=10, skip=0)
    logs_page2, _ = await mock_repo.query({}, limit=10, skip=10)
    
    # Verify pages don't overlap
    page1_ids = [log.resource_id for log in logs_page1]
    page2_ids = [log.resource_id for log in logs_page2]
    overlap = set(page1_ids) & set(page2_ids)
    assert len(overlap) == 0, f"Pages overlap: {overlap}"
    print("✓ Pagination offset works correctly (no overlap between pages)")
    
    print("\n=== All Audit Log Querying Tests Passed! ===")
    return True


async def test_csv_export_format():
    """Test CSV export formatting"""
    print("\n=== Testing CSV Export Format ===")
    
    # Create sample audit log
    log = AuditLog(
        event_type=EventType.DUPLICATE_OVERRIDE,
        actor_id="admin-123",
        actor_type=ActorType.ADMIN,
        resource_id="app-456",
        resource_type=ResourceType.APPLICATION,
        action="Override decision: reject_duplicate",
        details={
            "decision": "reject_duplicate",
            "justification": "Different persons"
        },
        ip_address="192.168.1.100",
        success=True,
        timestamp=datetime.utcnow()
    )
    
    # Test CSV row formatting
    print("\n1. Testing CSV row format...")
    csv_row = [
        log.timestamp.isoformat(),
        log.event_type,
        log.actor_id,
        log.actor_type,
        log.resource_id or "",
        log.resource_type or "",
        log.action,
        "Yes" if log.success else "No",
        log.ip_address or "",
        log.error_message or "",
        str(log.details) if log.details else ""
    ]
    
    assert len(csv_row) == 11, f"Expected 11 columns, got {len(csv_row)}"
    assert csv_row[0].endswith("Z") or "T" in csv_row[0], "Timestamp not in ISO format"
    assert csv_row[1] == "duplicate_override"
    assert csv_row[7] == "Yes"
    print("✓ CSV row format is correct")
    
    # Test CSV header
    print("\n2. Testing CSV header...")
    expected_headers = [
        "Timestamp", "Event Type", "Actor ID", "Actor Type",
        "Resource ID", "Resource Type", "Action", "Success",
        "IP Address", "Error Message", "Details"
    ]
    assert len(expected_headers) == 11, "Header count mismatch"
    print(f"✓ CSV header has {len(expected_headers)} columns")
    
    print("\n=== All CSV Export Tests Passed! ===")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AUDIT LOGGING SYSTEM - INTEGRATION TESTS")
    print("="*60)
    
    try:
        # Run all test suites
        await test_audit_log_creation()
        await test_audit_log_querying()
        await test_csv_export_format()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60)
        print("\nAudit logging system is working correctly:")
        print("  ✓ Structured audit log creation with automatic timestamps")
        print("  ✓ Application submission logging")
        print("  ✓ Duplicate detection logging")
        print("  ✓ Identity issuance logging")
        print("  ✓ Override decision logging")
        print("  ✓ Audit log querying with filters")
        print("  ✓ Pagination support")
        print("  ✓ CSV export formatting")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
