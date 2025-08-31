#!/usr/bin/env python3
"""
Initialize Orders Tables in MySQL Database
Creates orders and order_items tables for the food recommendation system.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseManager

def initialize_orders_tables():
    """Initialize the orders tables in the database."""
    print("🛒 Initializing orders tables in database...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Read the schema file
        schema_file = project_root / "database" / "orders_schema.sql"
        if not schema_file.exists():
            print(f"❌ Schema file not found: {schema_file}")
            return False
            
        with open(schema_file, 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        
        # Split the schema into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        # Execute each statement
        for statement in statements:
            if statement:
                print(f"🔄 Executing: {statement[:50]}...")
                db_manager.execute_query(statement)
        
        print("✅ Orders tables created successfully!")
        
        # Verify tables exist
        tables_query = """
        SELECT table_name, table_comment 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name IN ('orders', 'order_items')
        ORDER BY table_name
        """
        
        tables = db_manager.fetch_all(tables_query)
        
        if tables:
            print("✅ Verified tables exist in database:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("❌ No orders tables found in database")
            return False
            
        # Check table structures
        print("\n📋 Orders table structure:")
        orders_structure = db_manager.fetch_all("DESCRIBE orders")
        for column in orders_structure:
            print(f"  - {column['Field']}: {column['Type']}")
            
        print("\n📋 Order items table structure:")
        order_items_structure = db_manager.fetch_all("DESCRIBE order_items")
        for column in order_items_structure:
            print(f"  - {column['Field']}: {column['Type']}")
        
        print("\n✅ Orders tables initialization completed successfully!")
        print("🛒 You can now process orders and store them in the database.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing orders tables: {e}")
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = initialize_orders_tables()
    sys.exit(0 if success else 1)
