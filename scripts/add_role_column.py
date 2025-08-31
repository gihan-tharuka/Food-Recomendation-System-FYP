#!/usr/bin/env python3
"""
Script to add role column to users table
"""

import sys
from pathlib import Path
import mysql.connector

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def add_role_column():
    """Add role column to users table"""
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='food_recommendation_db'
        )
        cursor = connection.cursor()
        
        # Check if role column already exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        result = cursor.fetchone()
        
        if result:
            print("Role column already exists")
        else:
            # Add role column
            cursor.execute('ALTER TABLE users ADD COLUMN role ENUM("customer", "staff") DEFAULT "customer"')
            print("Role column added successfully")
        
        # Create index if it doesn't exist
        try:
            cursor.execute('CREATE INDEX idx_role ON users(role)')
            print("Role index created successfully")
        except mysql.connector.Error as e:
            if "Duplicate key name" in str(e):
                print("Role index already exists")
            else:
                print(f"Index creation error: {e}")
        
        # Update existing users to have customer role
        cursor.execute('UPDATE users SET role = "customer" WHERE role IS NULL')
        affected_rows = cursor.rowcount
        print(f"Updated {affected_rows} users to customer role")
        
        # Commit changes
        connection.commit()
        
        # Show table structure
        cursor.execute('DESCRIBE users')
        columns = cursor.fetchall()
        print("\nUpdated table structure:")
        for column in columns:
            print(f"  {column[0]}: {column[1]}")
        
        cursor.close()
        connection.close()
        print("\nRole column setup completed successfully!")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_role_column()
