"""Security utilities for data protection"""

import os
import stat
from pathlib import Path
from typing import Optional
from app.core.logging import logger


class SecurityManager:
    """Manager for security-related operations"""
    
    @staticmethod
    def set_secure_file_permissions(file_path: str) -> bool:
        """
        Set secure file permissions for stored files
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if permissions set successfully, False otherwise
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Set permissions to 600 (read/write for owner only)
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            
            logger.debug(f"Secure permissions set for file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting file permissions for {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def set_secure_directory_permissions(dir_path: str) -> bool:
        """
        Set secure directory permissions
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if permissions set successfully, False otherwise
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                logger.warning(f"Directory does not exist: {dir_path}")
                return False
            
            # Set permissions to 700 (read/write/execute for owner only)
            os.chmod(dir_path, stat.S_IRWXU)
            
            logger.debug(f"Secure permissions set for directory: {dir_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting directory permissions for {dir_path}: {str(e)}")
            return False
    
    @staticmethod
    def validate_environment_variables() -> bool:
        """
        Validate that required sensitive environment variables are set
        
        Returns:
            True if all required variables are set, False otherwise
        """
        required_vars = [
            "MONGODB_URI",
            "SECRET_KEY",
        ]
        
        missing_vars = []
        weak_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            
            if not value:
                missing_vars.append(var)
            elif var == "SECRET_KEY":
                # Check if SECRET_KEY is strong enough
                if len(value) < 32:
                    weak_vars.append(f"{var} (too short, minimum 32 characters)")
                elif value == "your-secret-key-change-in-production":
                    weak_vars.append(f"{var} (using default value)")
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        if weak_vars:
            logger.warning(f"Weak environment variables detected: {', '.join(weak_vars)}")
            # Don't fail, just warn
        
        logger.info("Environment variables validated successfully")
        return True
    
    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """
        Mask sensitive data for logging
        
        Args:
            data: Sensitive data to mask
            visible_chars: Number of characters to keep visible at the end
            
        Returns:
            Masked string
        """
        if not data or len(data) <= visible_chars:
            return "****"
        
        return "*" * (len(data) - visible_chars) + data[-visible_chars:]
    
    @staticmethod
    def initialize_storage_security(storage_path: str) -> bool:
        """
        Initialize secure permissions for storage directories
        
        Args:
            storage_path: Base storage path
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            storage_dir = Path(storage_path)
            
            # Create directory if it doesn't exist
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions on storage directory
            SecurityManager.set_secure_directory_permissions(str(storage_dir))
            
            # Set secure permissions on subdirectories
            for subdir in storage_dir.iterdir():
                if subdir.is_dir():
                    SecurityManager.set_secure_directory_permissions(str(subdir))
            
            logger.info(f"Storage security initialized for: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing storage security: {str(e)}")
            return False


# Global security manager instance
security_manager = SecurityManager()
