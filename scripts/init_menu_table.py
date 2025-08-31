#!/usr/bin/env python3
"""
Initialize menu table in the database
This script creates the menu_items table if it doesn't exist
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

def create_menu_table():
    """Create the menu_items table in the database"""
    
    # SQL to drop existing table
    drop_table_sql = "DROP TABLE IF EXISTS menu_items"
    
    # SQL to create menu_items table (simplified schema)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS menu_items (
        item_id INT PRIMARY KEY,
        item_name VARCHAR(255) NOT NULL,
        price DECIMAL(10,2),
        cuisine VARCHAR(100),
        category VARCHAR(100),
        
        -- Context tags (only the requested ones)
        is_morning BOOLEAN DEFAULT FALSE,
        is_afternoon BOOLEAN DEFAULT FALSE,
        is_evening BOOLEAN DEFAULT FALSE,
        is_sunny BOOLEAN DEFAULT FALSE,
        is_rainy BOOLEAN DEFAULT FALSE,
        
        -- Indexes for better performance
        INDEX idx_item_name (item_name),
        INDEX idx_cuisine (cuisine),
        INDEX idx_category (category),
        INDEX idx_price (price)
    )
    """
    
    try:
        if not db_manager.connect():
            print("❌ Failed to connect to database")
            return False
        
        cursor = db_manager.connection.cursor()
        
        # Drop existing table first
        cursor.execute(drop_table_sql)
        db_manager.connection.commit()
        print("🗑️ Dropped existing menu_items table")
        
        # Create the table with new schema
        cursor.execute(create_table_sql)
        db_manager.connection.commit()
        print("✅ Created new menu_items table with simplified schema")
        
        print("✅ Menu table created successfully!")
        
        # Check if table was created
        cursor.execute("SHOW TABLES LIKE 'menu_items'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Table 'menu_items' exists in database")
            
            # Show table structure
            cursor.execute("DESCRIBE menu_items")
            columns = cursor.fetchall()
            print("\n📋 Table structure:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
        else:
            print("❌ Table creation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating menu table: {e}")
        return False
    finally:
        if db_manager.connection:
            cursor.close()
            db_manager.disconnect()

if __name__ == "__main__":
    print("🍽️ Initializing menu table in database...")
    success = create_menu_table()
    
    if success:
        print("\n✅ Menu table initialization completed successfully!")
        print("🔄 You can now run predictions to populate the table.")
    else:
        print("\n❌ Menu table initialization failed!")
        print("🔧 Please check your database connection and try again.")
