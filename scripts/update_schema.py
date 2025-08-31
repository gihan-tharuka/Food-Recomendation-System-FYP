#!/usr/bin/env python3
"""
Database schema update script to add password field to existing users table
Run this script to add password support to existing users
"""

import sys
from pathlib import Path
import logging
import bcrypt

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseManager
from config.settings import USE_DATABASE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_password_field():
    """Add password_hash field to existing users table"""
    
    logger.info("Adding password field to users table...")
    
    db_manager = DatabaseManager()
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return False
    
    try:
        cursor = db_manager.connection.cursor()
        
        # Check if password_hash column already exists
        check_column = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = 'food_recommendation_db' 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'password_hash'
        """
        cursor.execute(check_column)
        
        if cursor.fetchone():
            logger.info("Password field already exists")
            return True
        
        # Add password_hash column
        add_column = """
        ALTER TABLE users 
        ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''
        """
        cursor.execute(add_column)
        
        # Set default password for existing users (you should prompt users to change this)
        default_password = "defaultpass123"
        salt = bcrypt.gensalt()
        default_hash = bcrypt.hashpw(default_password.encode('utf-8'), salt).decode('utf-8')
        
        update_existing = """
        UPDATE users 
        SET password_hash = %s 
        WHERE password_hash = ''
        """
        cursor.execute(update_existing, (default_hash,))
        
        db_manager.connection.commit()
        
        affected_rows = cursor.rowcount
        logger.info(f"Password field added successfully. Updated {affected_rows} existing users with default password.")
        logger.warning("IMPORTANT: Existing users should change their password from the default 'defaultpass123'")
        
        return True
        
    except Exception as e:
        db_manager.connection.rollback()
        logger.error(f"Error adding password field: {e}")
        return False
    finally:
        cursor.close()
        db_manager.disconnect()

def test_password_authentication():
    """Test password authentication with a sample user"""
    logger.info("Testing password authentication...")
    
    try:
        from src.models.database_models import UserModel
        
        # Test authentication with default password
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return False
        
        cursor = db_manager.connection.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users LIMIT 1")
        user = cursor.fetchone()
        
        if user:
            test_email = user['email']
            # Test with default password
            auth_result = UserModel.authenticate_user(test_email, "defaultpass123")
            if auth_result:
                logger.info(f"Password authentication working! Test user: {auth_result['email']}")
                return True
            else:
                logger.warning("Password authentication failed for test user")
                return False
        else:
            logger.info("No users found to test authentication")
            return True
            
    except Exception as e:
        logger.error(f"Error testing authentication: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_manager' in locals():
            db_manager.disconnect()

if __name__ == "__main__":
    print("=" * 60)
    print("Food Recommendation System - Password Field Update")
    print("=" * 60)
    
    if not USE_DATABASE:
        print("Database mode is not enabled. Set USE_DATABASE=True in config/settings.py")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "update":
            if add_password_field():
                test_password_authentication()
        elif command == "test":
            test_password_authentication()
        else:
            print(f"Unknown command: {command}")
    else:
        print("\nAvailable commands:")
        print("  python update_schema.py update  - Add password field to users table")
        print("  python update_schema.py test    - Test password authentication")
        print("\nNote: Existing users will get default password 'defaultpass123'")
        print("They should change their password after the update.")
