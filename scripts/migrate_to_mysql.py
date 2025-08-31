#!/usr/bin/env python3
"""
Migration script to move from CSV to MySQL database
Run this script to set up the database and migrate existing data
"""

import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig, DatabaseManager
from config.settings import USERS_CSV_PATH, RATINGS_CSV_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_to_mysql():
    """Complete migration from CSV to MySQL"""
    
    logger.info("Starting migration to MySQL database...")
    
    # Step 1: Create database
    logger.info("Step 1: Creating database...")
    db_config = DatabaseConfig()
    if not db_config.create_database():
        logger.error("Failed to create database")
        return False
    
    # Step 2: Create tables
    logger.info("Step 2: Creating tables...")
    db_manager = DatabaseManager()
    if not db_manager.create_tables():
        logger.error("Failed to create tables")
        return False
    
    # Step 3: Migrate existing data
    logger.info("Step 3: Migrating existing CSV data...")
    if not db_manager.migrate_csv_data(USERS_CSV_PATH, RATINGS_CSV_PATH):
        logger.error("Failed to migrate data")
        return False
    
    logger.info("Migration completed successfully!")
    logger.info("You can now start using the database by ensuring USE_DATABASE=True in config/settings.py")
    
    return True

def test_database_connection():
    """Test if database connection works"""
    logger.info("Testing database connection...")
    
    try:
        from src.models.database_models import UserModel, RatingModel
        
        # Test user operations
        users = UserModel.get_all_users()
        logger.info(f"Found {len(users)} users in database")
        
        # Test ratings operations
        ratings_df = RatingModel.get_all_ratings_dataframe()
        logger.info(f"Found {len(ratings_df)} ratings in database")
        
        logger.info("Database connection test successful!")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def show_database_info():
    """Show information about the current database setup"""
    logger.info("Database Configuration:")
    db_config = DatabaseConfig()
    logger.info(f"  Host: {db_config.host}")
    logger.info(f"  Port: {db_config.port}")
    logger.info(f"  User: {db_config.user}")
    logger.info(f"  Database: {db_config.database}")
    
    # Show current data counts
    if USERS_CSV_PATH.exists():
        import pandas as pd
        users_df = pd.read_csv(USERS_CSV_PATH)
        logger.info(f"  Users in CSV: {len(users_df)}")
    
    if RATINGS_CSV_PATH.exists():
        import pandas as pd
        ratings_df = pd.read_csv(RATINGS_CSV_PATH)
        logger.info(f"  Ratings in CSV: {len(ratings_df)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Food Recommendation System - Database Migration")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            migrate_to_mysql()
        elif command == "test":
            test_database_connection()
        elif command == "info":
            show_database_info()
        else:
            print(f"Unknown command: {command}")
    else:
        print("\nAvailable commands:")
        print("  python migrate_to_mysql.py migrate  - Migrate CSV data to MySQL")
        print("  python migrate_to_mysql.py test     - Test database connection")
        print("  python migrate_to_mysql.py info     - Show database information")
        print("\nPrerequisites:")
        print("1. Install XAMPP and start MySQL service")
        print("2. Install required Python packages: mysql-connector-python")
        print("3. Ensure config/settings.py has correct database settings")
        print("\nTo migrate:")
        print("1. python migrate_to_mysql.py info")
        print("2. python migrate_to_mysql.py migrate")  
        print("3. python migrate_to_mysql.py test")
        print("4. Set USE_DATABASE=True in config/settings.py")
