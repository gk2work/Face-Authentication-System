"""Manual demonstration of audit logging system"""

import asyncio
from datetime import datetime, timedelta
from app.services.audit_service import audit_service
from app.models.audit import EventType, ActorType, ResourceType, AuditLog


class MockDB:
    """Mock database for demonstration"""
    pass


class MockAuditRepo:
    """Mock audit repository that stores logs in memory"""
    
    def __init__(self, db):
        self.logs = []
    
    async def create(self, audit_log: AuditLog) -> str:
        self.logs.append(audit_log)
        return f"log_{len(self.logs)}"
    
    async def query(self, filters: dict, limit: int = 100, skip: int = 0):
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


async def demonstrate_audit_logging():
    """Demonstrate the audit logging system"""
    
    print("\n" + "="*70)
    print("AUDIT LOGGING SYSTEM - LIVE DEMONSTRATION")
    print("="*70)
    
    # Setup mock database
    mock_db = MockDB()
    mock_repo = MockAuditRepo(mock_db)
    
    # Monkey patch audit service
    original_get_repo = audit_service._get_audit_repo
    audit_service._get_audit_repo = lambda db: mock_repo
    
    try:
        # Scenario 1: Application Submission
        print("\n" + "-"*70)
        print("SCENARIO 1: Application Submission")
        print("-"*70)
        
        print("\n📝 Applicant submits a new application...")
        await audit_service.log_application_submission(
            db=mock_db,
            application_id="APP-2025-001",
            applicant_email="john.doe@example.com",
            applicant_name="John Doe",
            ip_address="203.0.113.45"
        )
        
        print("✓ Audit log created:")
        log = mock_repo.logs[-1]
        print(f"  Event Type: {log.event_type}")
        print(f"  Timestamp: {log.timestamp.isoformat()}")
        print(f"  Actor: {log.actor_id} ({log.actor_type})")
        print(f"  Resource: {log.resource_id}")
        print(f"  Action: {log.action}")
        print(f"  Details: {log.details}")
        print(f"  IP Address: {log.ip_address}")
        
        # Scenario 2: Duplicate Detection
        print("\n" + "-"*70)
        print("SCENARIO 2: Duplicate Detection")
        print("-"*70)
        
        print("\n🔍 System detects a potential duplicate...")
        await audit_service.log_duplicate_detection(
            db=mock_db,
            application_id="APP-2025-001",
            matched_application_id="APP-2024-789",
            confidence_score=0.96,
            is_duplicate=True
        )
        
        print("✓ Audit log created:")
        log = mock_repo.logs[-1]
        print(f"  Event Type: {log.event_type}")
        print(f"  Timestamp: {log.timestamp.isoformat()}")
        print(f"  Actor: {log.actor_id} ({log.actor_type})")
        print(f"  Resource: {log.resource_id}")
        print(f"  Action: {log.action}")
        print(f"  Confidence Score: {log.details['confidence_score']}")
        print(f"  Matched Application: {log.details['matched_application_id']}")
        print(f"  Is Duplicate: {log.details['is_duplicate']}")
        
        # Scenario 3: Admin Override
        print("\n" + "-"*70)
        print("SCENARIO 3: Admin Override Decision")
        print("-"*70)
        
        print("\n👤 Admin reviews the case and makes an override decision...")
        await audit_service.log_override_decision(
            db=mock_db,
            application_id="APP-2025-001",
            admin_id="admin.smith",
            decision="reject_duplicate",
            justification="After careful review of both photographs, the facial features show clear differences. The similarity score was likely due to similar lighting conditions and camera angles. Applicants are different individuals.",
            previous_status="duplicate",
            new_status="verified",
            ip_address="10.0.1.100"
        )
        
        print("✓ Audit log created:")
        log = mock_repo.logs[-1]
        print(f"  Event Type: {log.event_type}")
        print(f"  Timestamp: {log.timestamp.isoformat()}")
        print(f"  Actor: {log.actor_id} ({log.actor_type})")
        print(f"  Resource: {log.resource_id}")
        print(f"  Action: {log.action}")
        print(f"  Decision: {log.details['decision']}")
        print(f"  Justification: {log.details['justification'][:80]}...")
        print(f"  Status Change: {log.details['previous_status']} → {log.details['new_status']}")
        print(f"  IP Address: {log.ip_address}")
        
        # Scenario 4: Identity Issuance
        print("\n" + "-"*70)
        print("SCENARIO 4: Identity ID Issuance")
        print("-"*70)
        
        print("\n🆔 System issues a unique identity ID...")
        await audit_service.log_identity_issued(
            db=mock_db,
            application_id="APP-2025-001",
            identity_id="ID-550e8400-e29b-41d4-a716-446655440000"
        )
        
        print("✓ Audit log created:")
        log = mock_repo.logs[-1]
        print(f"  Event Type: {log.event_type}")
        print(f"  Timestamp: {log.timestamp.isoformat()}")
        print(f"  Actor: {log.actor_id} ({log.actor_type})")
        print(f"  Resource: {log.resource_id} ({log.resource_type})")
        print(f"  Action: {log.action}")
        print(f"  Application ID: {log.details['application_id']}")
        print(f"  Identity ID: {log.details['identity_id']}")
        
        # Scenario 5: Query Audit Logs
        print("\n" + "-"*70)
        print("SCENARIO 5: Query Audit Logs")
        print("-"*70)
        
        print("\n📊 Querying all audit logs...")
        logs, total = await mock_repo.query({}, limit=100, skip=0)
        print(f"✓ Found {total} total audit log entries")
        
        print("\n📊 Querying logs by event type (DUPLICATE_OVERRIDE)...")
        logs, total = await mock_repo.query(
            {"event_type": EventType.DUPLICATE_OVERRIDE},
            limit=100,
            skip=0
        )
        print(f"✓ Found {total} override decision logs")
        
        print("\n📊 Querying logs by actor (admin.smith)...")
        logs, total = await mock_repo.query(
            {"actor_id": "admin.smith"},
            limit=100,
            skip=0
        )
        print(f"✓ Found {total} logs by admin.smith")
        
        # Scenario 6: Audit Trail Summary
        print("\n" + "-"*70)
        print("SCENARIO 6: Complete Audit Trail for Application")
        print("-"*70)
        
        print("\n📋 Complete audit trail for APP-2025-001:")
        print()
        
        for i, log in enumerate(mock_repo.logs, 1):
            print(f"{i}. [{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log.event_type}")
            print(f"   Actor: {log.actor_id} ({log.actor_type})")
            print(f"   Action: {log.action}")
            if log.ip_address:
                print(f"   IP: {log.ip_address}")
            print()
        
        # Scenario 7: CSV Export Preview
        print("\n" + "-"*70)
        print("SCENARIO 7: CSV Export Preview")
        print("-"*70)
        
        print("\n📄 CSV Export Format:")
        print()
        
        # Header
        headers = [
            "Timestamp", "Event Type", "Actor ID", "Actor Type",
            "Resource ID", "Resource Type", "Action", "Success",
            "IP Address", "Error Message", "Details"
        ]
        print(",".join(headers))
        
        # Sample rows
        for log in mock_repo.logs[:2]:
            row = [
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
                str(log.details)[:50] + "..." if log.details else ""
            ]
            print(",".join(str(x) for x in row))
        
        print(f"\n... ({len(mock_repo.logs) - 2} more rows)")
        
        # Summary
        print("\n" + "="*70)
        print("DEMONSTRATION COMPLETE")
        print("="*70)
        print("\n✅ Audit Logging System Features Demonstrated:")
        print("  ✓ Application submission logging")
        print("  ✓ Duplicate detection logging")
        print("  ✓ Admin override decision logging")
        print("  ✓ Identity issuance logging")
        print("  ✓ Automatic timestamp generation")
        print("  ✓ Comprehensive event details")
        print("  ✓ IP address tracking")
        print("  ✓ Query and filtering capabilities")
        print("  ✓ CSV export format")
        print("  ✓ Complete audit trail reconstruction")
        print()
        print(f"Total audit logs created: {len(mock_repo.logs)}")
        print()
        
    finally:
        # Restore original method
        audit_service._get_audit_repo = original_get_repo


if __name__ == "__main__":
    asyncio.run(demonstrate_audit_logging())
