"""Seed script to populate MongoDB with sample data for testing"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.mongodb import mongodb_manager
from app.core.config import settings
from app.services.auth_service import AuthService
from app.core.logging import logger

# Initialize auth service for password hashing
auth_service = AuthService()


async def seed_users():
    """Seed admin and regular users"""
    users_collection = mongodb_manager.get_collection("users")
    
    # Check if users already exist
    existing_count = await users_collection.count_documents({})
    if existing_count > 0:
        logger.info(f"Users collection already has {existing_count} documents. Skipping user seeding.")
        return
    
    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": auth_service.get_password_hash("admin123"),
            "full_name": "System Administrator",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "username": "operator1",
            "email": "operator1@example.com",
            "hashed_password": auth_service.get_password_hash("operator123"),
            "full_name": "Operator One",
            "role": "operator",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "username": "operator2",
            "email": "operator2@example.com",
            "hashed_password": auth_service.get_password_hash("operator123"),
            "full_name": "Operator Two",
            "role": "operator",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = await users_collection.insert_many(users)
    logger.info(f"Seeded {len(result.inserted_ids)} users")
    return result.inserted_ids


async def seed_identities():
    """Seed sample identities"""
    identities_collection = mongodb_manager.get_collection("identities")
    
    # Check if identities already exist
    existing_count = await identities_collection.count_documents({})
    if existing_count > 0:
        logger.info(f"Identities collection already has {existing_count} documents. Skipping identity seeding.")
        return []
    
    identities = []
    for i in range(1, 11):
        identity = {
            "unique_id": f"ID{i:06d}",
            "status": "active" if i <= 8 else "flagged",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            "updated_at": datetime.utcnow(),
            "metadata": {
                "source": "seed_script",
                "notes": f"Sample identity {i}"
            }
        }
        identities.append(identity)
    
    result = await identities_collection.insert_many(identities)
    logger.info(f"Seeded {len(result.inserted_ids)} identities")
    return result.inserted_ids


async def seed_applications(identity_ids):
    """Seed sample applications"""
    applications_collection = mongodb_manager.get_collection("applications")
    
    # Check if applications already exist
    existing_count = await applications_collection.count_documents({})
    if existing_count > 0:
        logger.info(f"Applications collection already has {existing_count} documents. Skipping application seeding.")
        return
    
    if not identity_ids:
        logger.warning("No identity IDs provided. Skipping application seeding.")
        return
    
    statuses = ["pending", "processing", "completed", "failed"]
    applications = []
    
    for i in range(1, 21):
        # Randomly assign to an identity (some identities will have multiple applications)
        identity_idx = random.randint(0, min(len(identity_ids) - 1, 7))
        status = random.choice(statuses)
        
        application = {
            "application_id": f"APP{i:08d}",
            "identity_id": f"ID{identity_idx + 1:06d}",
            "status": status,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 60)),
            "updated_at": datetime.utcnow(),
            "processing": {
                "status": status,
                "started_at": datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                "completed_at": datetime.utcnow() if status == "completed" else None,
                "error_message": "Sample error" if status == "failed" else None
            },
            "result": {
                "is_duplicate": random.choice([True, False]) if status == "completed" else None,
                "confidence_score": round(random.uniform(0.7, 0.99), 2) if status == "completed" else None,
                "identity_id": f"ID{identity_idx + 1:06d}" if status == "completed" else None,
                "match_details": {
                    "similarity_score": round(random.uniform(0.7, 0.99), 2) if status == "completed" else None,
                    "matched_application_id": f"APP{random.randint(1, i):08d}" if status == "completed" and random.choice([True, False]) else None
                } if status == "completed" else None
            },
            "metadata": {
                "source": "seed_script",
                "operator": random.choice(["operator1", "operator2"]),
                "notes": f"Sample application {i}"
            }
        }
        applications.append(application)
    
    result = await applications_collection.insert_many(applications)
    logger.info(f"Seeded {len(result.inserted_ids)} applications")


async def seed_audit_logs():
    """Seed sample audit logs"""
    audit_logs_collection = mongodb_manager.get_collection("audit_logs")
    
    # Check if audit logs already exist
    existing_count = await audit_logs_collection.count_documents({})
    if existing_count > 0:
        logger.info(f"Audit logs collection already has {existing_count} documents. Skipping audit log seeding.")
        return
    
    event_types = [
        "application.created",
        "application.processed",
        "identity.created",
        "identity.updated",
        "user.login",
        "user.logout"
    ]
    
    audit_logs = []
    for i in range(1, 51):
        event_type = random.choice(event_types)
        log = {
            "event_type": event_type,
            "actor_id": random.choice(["admin", "operator1", "operator2"]),
            "actor_type": "user",
            "resource_id": f"APP{random.randint(1, 20):08d}" if "application" in event_type else f"ID{random.randint(1, 10):06d}",
            "resource_type": "application" if "application" in event_type else "identity" if "identity" in event_type else "user",
            "action": event_type.split(".")[1],
            "timestamp": datetime.utcnow() - timedelta(hours=random.randint(1, 720)),
            "details": {
                "ip_address": f"192.168.1.{random.randint(1, 255)}",
                "user_agent": "Mozilla/5.0 (Sample User Agent)",
                "status": "success" if random.random() > 0.1 else "failure"
            },
            "metadata": {
                "source": "seed_script"
            }
        }
        audit_logs.append(log)
    
    result = await audit_logs_collection.insert_many(audit_logs)
    logger.info(f"Seeded {len(result.inserted_ids)} audit logs")


async def main():
    """Main seeding function"""
    try:
        logger.info("Starting database seeding...")
        logger.info(f"Connecting to MongoDB: {settings.MONGODB_DATABASE}")
        
        # Connect to MongoDB
        await mongodb_manager.connect()
        
        # Seed data in order
        logger.info("Seeding users...")
        await seed_users()
        
        logger.info("Seeding identities...")
        identity_ids = await seed_identities()
        
        logger.info("Seeding applications...")
        await seed_applications(identity_ids)
        
        logger.info("Seeding audit logs...")
        await seed_audit_logs()
        
        logger.info("Database seeding completed successfully!")
        
        # Print summary
        users_count = await mongodb_manager.get_collection("users").count_documents({})
        identities_count = await mongodb_manager.get_collection("identities").count_documents({})
        applications_count = await mongodb_manager.get_collection("applications").count_documents({})
        audit_logs_count = await mongodb_manager.get_collection("audit_logs").count_documents({})
        
        print("\n" + "="*50)
        print("DATABASE SEEDING SUMMARY")
        print("="*50)
        print(f"Users:        {users_count}")
        print(f"Identities:   {identities_count}")
        print(f"Applications: {applications_count}")
        print(f"Audit Logs:   {audit_logs_count}")
        print("="*50)
        print("\nTest Credentials:")
        print("-" * 50)
        print("Admin User:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nOperator Users:")
        print("  Username: operator1 / Password: operator123")
        print("  Username: operator2 / Password: operator123")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise
    finally:
        # Disconnect from MongoDB
        await mongodb_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
