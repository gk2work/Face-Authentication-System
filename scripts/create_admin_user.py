"""Script to create an admin user for the Face Authentication System"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import User, UserRole
from app.services.auth_service import auth_service
from app.database.mongodb import mongodb_manager
from app.database.repositories import UserRepository
from app.core.logging import logger


async def create_admin_user():
    """Create an admin user interactively"""
    
    print("=" * 60)
    print("Face Authentication System - Admin User Creation")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        print("Connecting to MongoDB...")
        await mongodb_manager.connect()
        print("✓ Connected to MongoDB")
        print()
        
        # Get user input
        username = input("Enter admin username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            return
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("Error: Email cannot be empty")
            return
        
        full_name = input("Enter admin full name: ").strip()
        if not full_name:
            print("Error: Full name cannot be empty")
            return
        
        password = input("Enter admin password (min 8 characters): ").strip()
        if len(password) < 8:
            print("Error: Password must be at least 8 characters")
            return
        
        password_confirm = input("Confirm password: ").strip()
        if password != password_confirm:
            print("Error: Passwords do not match")
            return
        
        print()
        print("Creating admin user...")
        
        # Check if user already exists
        user_repo = UserRepository(mongodb_manager.db)
        existing_user = await user_repo.get_by_username(username)
        
        if existing_user:
            print(f"Error: User '{username}' already exists")
            return
        
        # Hash password
        hashed_password = auth_service.get_password_hash(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            roles=[UserRole.ADMIN],
            is_active=True
        )
        
        await user_repo.create(user)
        
        print()
        print("=" * 60)
        print("✓ Admin user created successfully!")
        print("=" * 60)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Full Name: {full_name}")
        print(f"Roles: {[role.value for role in user.roles]}")
        print()
        print("You can now login using these credentials.")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        logger.error(f"Error creating admin user: {str(e)}")
    
    finally:
        # Disconnect from database
        await mongodb_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
