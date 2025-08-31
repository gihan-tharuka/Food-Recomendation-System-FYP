# Database configuration for MySQL
import mysql.connector
from mysql.connector import Error
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        # XAMPP MySQL default configuration
        self.host = 'localhost'
        self.port = 3306
        self.user = 'root'
        self.password = ''  # Default XAMPP MySQL password is empty
        self.database = 'food_recommendation_db'
        
    def create_connection(self):
        """Create and return database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return None
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect without specifying database
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' created or already exists")
            
            cursor.close()
            connection.close()
            return True
        except Error as e:
            logger.error(f"Error creating database: {e}")
            return False

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        self.connection = self.config.create_connection()
        return self.connection is not None
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a query (INSERT, UPDATE, DELETE)"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                raise Exception("Could not connect to database")
        
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.rowcount
        except Error as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def fetch_all(self, query, params=None):
        """Fetch all results from a SELECT query"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                raise Exception("Could not connect to database")
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            raise e
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        """Fetch one result from a SELECT query"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                raise Exception("Could not connect to database")
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            raise e
        finally:
            cursor.close()
    
    def close(self):
        """Alias for disconnect method"""
        self.disconnect()
    
    def create_tables(self):
        """Create all required tables"""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # Create ratings table
            create_ratings_table = """
            CREATE TABLE IF NOT EXISTS ratings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                item_id INT NOT NULL,
                rating DECIMAL(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_item (user_id, item_id)
            )
            """
            
            cursor.execute(create_users_table)
            cursor.execute(create_ratings_table)
            
            self.connection.commit()
            logger.info("Tables created successfully")
            return True
            
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            return False
        finally:
            cursor.close()
            self.disconnect()
    
    def migrate_csv_data(self, users_csv_path, ratings_csv_path):
        """Migrate existing CSV data to MySQL"""
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Migrate users data
            if Path(users_csv_path).exists():
                users_df = pd.read_csv(users_csv_path)
                logger.info(f"Migrating {len(users_df)} users...")
                
                for _, user in users_df.iterrows():
                    # Clean email field (remove 'mailto:' prefix if present)
                    email = user['email']
                    if email.startswith('mailto:'):
                        email = email[7:]  # Remove 'mailto:' prefix
                    
                    insert_user = """
                    INSERT IGNORE INTO users (user_id, name, email) 
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_user, (user['user_id'], user['name'], email))
            
            # Migrate ratings data
            if Path(ratings_csv_path).exists():
                ratings_df = pd.read_csv(ratings_csv_path)
                logger.info(f"Migrating {len(ratings_df)} ratings...")
                
                for _, rating in ratings_df.iterrows():
                    # Parse date field
                    date_str = rating['date']
                    if isinstance(date_str, str):
                        try:
                            # Try different date formats
                            if '/' in date_str:
                                date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
                            else:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            date_obj = datetime.now().date()
                    else:
                        date_obj = datetime.now().date()
                    
                    insert_rating = """
                    INSERT IGNORE INTO ratings (user_id, item_id, rating, date) 
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_rating, (
                        rating['user_id'], 
                        rating['item_id'], 
                        rating['rating'], 
                        date_obj
                    ))
            
            self.connection.commit()
            logger.info("Data migration completed successfully")
            return True
            
        except Error as e:
            logger.error(f"Error migrating data: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
            self.disconnect()

# Global database manager instance
db_manager = DatabaseManager()
