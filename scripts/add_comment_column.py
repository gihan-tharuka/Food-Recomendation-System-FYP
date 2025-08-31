#!/usr/bin/env python3
"""
Migration script to add comment column to ratings table
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

def add_comment_column():
    """Add comment column to ratings table"""
    
    if not db_manager.connect():
        print("❌ Database connection failed")
        return False
    
    try:
        cursor = db_manager.connection.cursor()
        
        # Check if comment column already exists
        cursor.execute("DESCRIBE ratings")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'comment' in columns:
            print("✅ Comment column already exists in ratings table")
            return True
        
        # Add comment column
        print("Adding comment column to ratings table...")
        cursor.execute("ALTER TABLE ratings ADD COLUMN comment TEXT DEFAULT NULL")
        db_manager.connection.commit()
        
        # Verify the column was added
        cursor.execute("DESCRIBE ratings")
        updated_columns = [row[0] for row in cursor.fetchall()]
        
        if 'comment' in updated_columns:
            print("✅ Successfully added comment column to ratings table")
            print("\nUpdated ratings table structure:")
            cursor.execute("DESCRIBE ratings")
            for row in cursor.fetchall():
                print(f"  {row[0]} - {row[1]}")
            return True
        else:
            print("❌ Failed to add comment column")
            return False
            
    except Exception as e:
        print(f"❌ Error adding comment column: {e}")
        db_manager.connection.rollback()
        return False
    finally:
        cursor.close()
        db_manager.disconnect()

if __name__ == "__main__":
    print("🔄 Running migration: Add comment column to ratings table")
    success = add_comment_column()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)
