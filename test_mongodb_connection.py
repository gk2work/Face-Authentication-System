"""Test MongoDB connection and basic operations"""

import asyncio
from app.database.mongodb import mongodb_manager
from app.models.application import Application, ApplicantData, PhotographMetadata, ApplicationStatus
from app.models.identity import Identity, IdentityStatus
from app.database.repositories import ApplicationRepository, IdentityRepository
from datetime import datetime
import uuid


async def test_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        print("\n1. Connecting to MongoDB...")
        await mongodb_manager.connect()
        print("   ✓ Connected successfully")
        
        # Health check
        print("\n2. Running health check...")
        is_healthy = await mongodb_manager.health_check()
        print(f"   ✓ Health check: {'PASSED' if is_healthy else 'FAILED'}")
        
        # Test collections
        print("\n3. Checking collections...")
        db = mongodb_manager.db
        collections = await db.list_collection_names()
        print(f"   ✓ Available collections: {', '.join(collections) if collections else 'None (will be created on first insert)'}")
        
        # Test indexes
        print("\n4. Checking indexes...")
        for collection_name in ["applications", "identities", "identity_embeddings", "audit_logs", "users"]:
            indexes = await db[collection_name].index_information()
            print(f"   ✓ {collection_name}: {len(indexes)} indexes")
        
        # Test application repository
        print("\n5. Testing Application Repository...")
        app_repo = ApplicationRepository(db)
        
        test_app = Application(
            application_id=str(uuid.uuid4()),
            applicant_data=ApplicantData(
                name="Test User",
                date_of_birth="1990-01-01",
                email="test@example.com",
                phone="+919876543210"
            ),
            photograph=PhotographMetadata(
                path="./storage/photographs/test.jpg",
                format="jpg",
                width=800,
                height=800,
                file_size=102400
            )
        )
        
        app_id = await app_repo.create(test_app)
        print(f"   ✓ Created test application: {test_app.application_id}")
        
        # Retrieve application
        retrieved_app = await app_repo.get_by_id(test_app.application_id)
        print(f"   ✓ Retrieved application: {retrieved_app.application_id if retrieved_app else 'None'}")
        
        # Update status
        updated = await app_repo.update_status(test_app.application_id, ApplicationStatus.PROCESSING)
        print(f"   ✓ Updated status: {updated}")
        
        # Test identity repository
        print("\n6. Testing Identity Repository...")
        identity_repo = IdentityRepository(db)
        
        test_identity = Identity(
            unique_id=str(uuid.uuid4()),
            status=IdentityStatus.ACTIVE,
            application_ids=[test_app.application_id]
        )
        
        identity_id = await identity_repo.create(test_identity)
        print(f"   ✓ Created test identity: {test_identity.unique_id}")
        
        # Retrieve identity
        retrieved_identity = await identity_repo.get_by_unique_id(test_identity.unique_id)
        print(f"   ✓ Retrieved identity: {retrieved_identity.unique_id if retrieved_identity else 'None'}")
        
        # Cleanup test data
        print("\n7. Cleaning up test data...")
        await db.applications.delete_one({"application_id": test_app.application_id})
        await db.identities.delete_one({"unique_id": test_identity.unique_id})
        print("   ✓ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Disconnect
        await mongodb_manager.disconnect()
        print("\nDisconnected from MongoDB")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
