"""Verify project setup and structure"""

import os
import sys
from pathlib import Path

def check_directory_structure():
    """Verify all required directories exist"""
    required_dirs = [
        "app",
        "app/api",
        "app/api/v1",
        "app/core",
        "app/database",
        "app/models",
        "app/services",
        "app/utils",
        "storage",
        "storage/photographs",
        "storage/vectors",
        "logs",
        "tests",
    ]
    
    print("Checking directory structure...")
    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_required_files():
    """Verify all required files exist"""
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/logging.py",
        "requirements.txt",
        "docker-compose.yml",
        ".env",
        ".env.example",
        ".gitignore",
        "README.md",
        "run.py",
    ]
    
    print("\nChecking required files...")
    all_exist = True
    for file_path in required_files:
        exists = os.path.isfile(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_env_variables():
    """Check if .env file has required variables"""
    print("\nChecking environment variables...")
    
    if not os.path.isfile(".env"):
        print("  ✗ .env file not found")
        return False
    
    required_vars = [
        "MONGODB_URI",
        "REDIS_URL",
        "SECRET_KEY",
        "STORAGE_PATH",
        "VECTOR_DB_PATH",
    ]
    
    with open(".env", "r") as f:
        env_content = f.read()
    
    all_present = True
    for var in required_vars:
        present = var in env_content
        status = "✓" if present else "✗"
        print(f"  {status} {var}")
        if not present:
            all_present = False
    
    return all_present


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Face Authentication System - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure()),
        ("Required Files", check_required_files()),
        ("Environment Variables", check_env_variables()),
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
        print("\n✓ All checks passed! Project setup is complete.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start Redis: docker-compose up -d")
        print("  3. Run the application: python run.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
