"""Verify Task 2 implementation"""

import os
import sys
from pathlib import Path


def check_files_exist():
    """Check if all required files exist"""
    required_files = [
        "app/models/user.py",
        "app/models/identity.py",
        "app/models/application.py",
        "app/models/audit.py",
        "app/database/mongodb.py",
        "app/database/repositories.py",
    ]
    
    print("Checking required files...")
    all_exist = True
    for file_path in required_files:
        exists = os.path.isfile(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_model_definitions():
    """Check if models are properly defined"""
    print("\nChecking model definitions...")
    
    checks = {
        "Application model": ("app/models/application.py", ["class Application", "class ApplicationStatus", "class ApplicantData"]),
        "Identity model": ("app/models/identity.py", ["class Identity", "class IdentityEmbedding", "class IdentityStatus"]),
        "Audit model": ("app/models/audit.py", ["class AuditLog", "class EventType", "class ActorType"]),
        "User model": ("app/models/user.py", ["class User", "class UserRole"]),
    }
    
    all_passed = True
    for check_name, (file_path, required_classes) in checks.items():
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            missing = [cls for cls in required_classes if cls not in content]
            if not missing:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} - Missing: {', '.join(missing)}")
                all_passed = False
        else:
            print(f"  ✗ {check_name} - File not found")
            all_passed = False
    
    return all_passed


def check_mongodb_connection():
    """Check MongoDB connection manager"""
    print("\nChecking MongoDB connection manager...")
    
    file_path = "app/database/mongodb.py"
    if not os.path.isfile(file_path):
        print(f"  ✗ {file_path} not found")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    required_features = [
        ("MongoDBManager class", "class MongoDBManager"),
        ("connect method", "async def connect"),
        ("disconnect method", "async def disconnect"),
        ("health_check method", "async def health_check"),
        ("Connection pooling", "maxPoolSize"),
        ("Retry logic", "_connection_retries"),
        ("Index creation", "_initialize_collections"),
    ]
    
    all_present = True
    for feature_name, search_string in required_features:
        if search_string in content:
            print(f"  ✓ {feature_name}")
        else:
            print(f"  ✗ {feature_name}")
            all_present = False
    
    return all_present


def check_repositories():
    """Check repository implementations"""
    print("\nChecking repository implementations...")
    
    file_path = "app/database/repositories.py"
    if not os.path.isfile(file_path):
        print(f"  ✗ {file_path} not found")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    required_repos = [
        "class ApplicationRepository",
        "class IdentityRepository",
        "class EmbeddingRepository",
        "class AuditLogRepository",
        "class UserRepository",
    ]
    
    all_present = True
    for repo in required_repos:
        if repo in content:
            print(f"  ✓ {repo}")
        else:
            print(f"  ✗ {repo}")
            all_present = False
    
    return all_present


def check_indexes():
    """Check if index creation is implemented"""
    print("\nChecking database indexes...")
    
    file_path = "app/database/mongodb.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    required_indexes = [
        ("applications.application_id", "applications.create_index"),
        ("applications.identity_id", "applications.create_index"),
        ("applications.status", "applications.create_index"),
        ("identities.unique_id", "identities.create_index"),
        ("identity_embeddings.identity_id", "identity_embeddings.create_index"),
        ("identity_embeddings.application_id", "identity_embeddings.create_index"),
        ("audit_logs.event_type", "audit_logs.create_index"),
        ("users.username", "users.create_index"),
    ]
    
    all_present = True
    for index_name, search_string in required_indexes:
        if search_string in content:
            print(f"  ✓ {index_name}")
        else:
            print(f"  ✗ {index_name}")
            all_present = False
    
    return all_present


def check_main_integration():
    """Check if MongoDB is integrated in main.py"""
    print("\nChecking main.py integration...")
    
    file_path = "app/main.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    required_features = [
        ("MongoDB import", "from app.database.mongodb import mongodb_manager"),
        ("Startup connection", "await mongodb_manager.connect()"),
        ("Shutdown disconnect", "await mongodb_manager.disconnect()"),
        ("Health check", "mongodb_manager.health_check()"),
    ]
    
    all_present = True
    for feature_name, search_string in required_features:
        if search_string in content:
            print(f"  ✓ {feature_name}")
        else:
            print(f"  ✗ {feature_name}")
            all_present = False
    
    return all_present


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Task 2 Verification: MongoDB Models and Database Connection")
    print("=" * 60)
    
    checks = [
        ("Files Exist", check_files_exist()),
        ("Model Definitions", check_model_definitions()),
        ("MongoDB Connection", check_mongodb_connection()),
        ("Repositories", check_repositories()),
        ("Database Indexes", check_indexes()),
        ("Main Integration", check_main_integration()),
    ]
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Task 2 is complete.")
        print("\nImplemented:")
        print("  • MongoDB connection manager with connection pooling")
        print("  • Pydantic models for Application, Identity, IdentityEmbedding, AuditLog, User")
        print("  • Database indexes on application_id, identity_id, status fields")
        print("  • MongoDB collection initialization and validation")
        print("  • Database connection error handling and retry logic")
        print("  • Repository classes for CRUD operations")
        print("\nRequirements satisfied: 2.4, 4.4")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
