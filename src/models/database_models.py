# Database models for user and rating management
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime
from uuid import uuid4
import logging
import bcrypt
from config.database import db_manager

logger = logging.getLogger(__name__)

class UserModel:
    """User model for database operations"""
    
    @staticmethod
    def _hash_password(password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def _verify_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def create_user(name, email, password, role='customer'):
        """Create a new user with password and role"""
        user_id = str(uuid4())
        password_hash = UserModel._hash_password(password)
        
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Check if email already exists
            check_email = "SELECT user_id FROM users WHERE email = %s"
            cursor.execute(check_email, (email,))
            if cursor.fetchone():
                raise ValueError("Email already exists")
            
            # Insert new user
            insert_user = """
            INSERT INTO users (user_id, name, email, password_hash, role) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_user, (user_id, name, email, password_hash, role))
            db_manager.connection.commit()
            
            logger.info(f"User created successfully: {user_id} with role: {role}")
            return {
                'user_id': user_id,
                'name': name,
                'email': email,
                'role': role
            }
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error creating user: {e}")
            raise Exception(f"Failed to create user: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user with email and password"""
        if not db_manager.connect():
            return None
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_user = "SELECT user_id, name, email, password_hash, role FROM users WHERE email = %s"
            cursor.execute(select_user, (email,))
            user = cursor.fetchone()
            
            if user and UserModel._verify_password(password, user['password_hash']):
                # Return user data without password hash
                return {
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role']
                }
            return None
            
        except Error as e:
            logger.error(f"Error authenticating user: {e}")
            return None
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by user_id"""
        if not db_manager.connect():
            return None
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_user = "SELECT user_id, name, email, role FROM users WHERE user_id = %s"
            cursor.execute(select_user, (user_id,))
            user = cursor.fetchone()
            
            return user
            
        except Error as e:
            logger.error(f"Error fetching user: {e}")
            return None
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        if not db_manager.connect():
            return None
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_user = "SELECT user_id, name, email FROM users WHERE email = %s"
            cursor.execute(select_user, (email,))
            user = cursor.fetchone()
            
            return user
            
        except Error as e:
            logger.error(f"Error fetching user by email: {e}")
            return None
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def user_exists(user_id):
        """Check if user exists"""
        user = UserModel.get_user_by_id(user_id)
        return user is not None
    
    @staticmethod
    def email_exists(email):
        """Check if email exists"""
        user = UserModel.get_user_by_email(email)
        return user is not None
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        if not db_manager.connect():
            return []
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_users = "SELECT user_id, name, email, role, created_at FROM users ORDER BY created_at DESC"
            cursor.execute(select_users)
            users = cursor.fetchall()
            
            return users
            
        except Error as e:
            logger.error(f"Error fetching all users: {e}")
            return []
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def update_user(user_id, name=None, email=None, password=None, role=None):
        """Update user information including role"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            if name is not None:
                update_fields.append("name = %s")
                values.append(name)
            
            if email is not None:
                update_fields.append("email = %s")
                values.append(email)
                
            if password is not None:
                update_fields.append("password_hash = %s")
                values.append(UserModel._hash_password(password))
                
            if role is not None:
                update_fields.append("role = %s")
                values.append(role)
            
            if not update_fields:
                return False
            
            values.append(user_id)
            
            update_user = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE user_id = %s
            """
            
            cursor.execute(update_user, values)
            db_manager.connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error updating user: {e}")
            raise Exception(f"Failed to update user: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Delete user
            delete_user = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(delete_user, (user_id,))
            db_manager.connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error deleting user: {e}")
            raise Exception(f"Failed to delete user: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()

class RatingModel:
    """Rating model for database operations"""
    
    @staticmethod
    def add_rating(user_id, item_id, rating, date=None):
        """Add or update a rating"""
        if date is None:
            date = datetime.now().date()
        
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert operation
            upsert_rating = """
            INSERT INTO ratings (user_id, item_id, rating, date) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            rating = VALUES(rating), date = VALUES(date)
            """
            
            cursor.execute(upsert_rating, (user_id, item_id, rating, date))
            db_manager.connection.commit()
            
            logger.info(f"Rating added/updated: user={user_id}, item={item_id}, rating={rating}")
            return True
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error adding rating: {e}")
            raise Exception(f"Failed to add rating: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_user_ratings(user_id):
        """Get all ratings for a user with full details including food names"""
        if not db_manager.connect():
            return []
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_ratings = """
            SELECT r.user_id, r.item_id, r.rating, r.date, r.created_at, r.comment,
                   m.item_name, m.cuisine, m.category, m.price
            FROM ratings r
            LEFT JOIN menu_items m ON r.item_id = m.item_id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
            """
            cursor.execute(select_ratings, (user_id,))
            ratings = cursor.fetchall()
            
            return ratings
            
        except Error as e:
            logger.error(f"Error fetching user ratings: {e}")
            return []
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_user_ratings_dataframe(user_id):
        """Get user ratings as DataFrame"""
        if not db_manager.connect():
            return pd.DataFrame()
        
        try:
            query = """
            SELECT user_id, item_id, rating, date, created_at 
            FROM ratings 
            WHERE user_id = %s
            ORDER BY date DESC
            """
            
            df = pd.read_sql(query, db_manager.connection, params=(user_id,))
            return df
            
        except Error as e:
            logger.error(f"Error fetching user ratings dataframe: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def get_all_ratings_dataframe():
        """Get all ratings as DataFrame"""
        if not db_manager.connect():
            return pd.DataFrame()
        
        try:
            query = """
            SELECT user_id, item_id, rating, date, created_at 
            FROM ratings 
            ORDER BY created_at DESC
            """
            
            df = pd.read_sql(query, db_manager.connection)
            return df
            
        except Error as e:
            logger.error(f"Error fetching all ratings dataframe: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def delete_rating(user_id, item_id):
        """Delete a specific rating"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            delete_rating = "DELETE FROM ratings WHERE user_id = %s AND item_id = %s"
            cursor.execute(delete_rating, (user_id, item_id))
            db_manager.connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error deleting rating: {e}")
            raise Exception(f"Failed to delete rating: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def delete_user_ratings(user_id):
        """Delete all ratings for a specific user"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            delete_ratings = "DELETE FROM ratings WHERE user_id = %s"
            cursor.execute(delete_ratings, (user_id,))
            db_manager.connection.commit()
            
            return cursor.rowcount >= 0  # Returns true even if no ratings to delete
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error deleting user ratings: {e}")
            raise Exception(f"Failed to delete user ratings: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()

    @staticmethod
    def get_user_item_rating(user_id, item_id):
        """Get a specific rating for a user and item"""
        if not db_manager.connect():
            return None
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            
            select_rating = """
            SELECT * FROM ratings 
            WHERE user_id = %s AND item_id = %s
            """
            
            cursor.execute(select_rating, (user_id, item_id))
            rating = cursor.fetchone()
            
            return rating
            
        except Error as e:
            logger.error(f"Error fetching user item rating: {e}")
            return None
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def create_rating(user_id, item_id, rating, comment=None):
        """Create a new rating"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            insert_rating = """
            INSERT INTO ratings (user_id, item_id, rating, comment, date) 
            VALUES (%s, %s, %s, %s, CURDATE())
            """
            
            cursor.execute(insert_rating, (user_id, item_id, rating, comment))
            db_manager.connection.commit()
            
            logger.info(f"Rating created: user={user_id}, item={item_id}, rating={rating}")
            return True
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error creating rating: {e}")
            return False
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def update_rating(user_id, item_id, rating, comment=None):
        """Update an existing rating"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            update_rating = """
            UPDATE ratings 
            SET rating = %s, comment = %s, date = CURDATE()
            WHERE user_id = %s AND item_id = %s
            """
            
            cursor.execute(update_rating, (rating, comment, user_id, item_id))
            db_manager.connection.commit()
            
            logger.info(f"Rating updated: user={user_id}, item={item_id}, rating={rating}")
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error updating rating: {e}")
            return False
        finally:
            cursor.close()
            db_manager.disconnect()


class MenuModel:
    """Menu model for database operations"""
    
    @staticmethod
    def add_menu_item(item_id, item_name, price, cuisine, category, image_url=None, **tags):
        """Add or update a menu item with predictions and image"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Build the tag columns (only the simplified ones)
            tag_columns = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
            
            # Prepare values for all columns including image_url
            all_columns = ['item_id', 'item_name', 'price', 'cuisine', 'category', 'image_url'] + tag_columns
            values = [item_id, item_name, price, cuisine, category, image_url]
            
            # Add tag values (default to False if not provided)
            for tag in tag_columns:
                values.append(tags.get(tag, False))
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert operation
            placeholders = ', '.join(['%s'] * len(all_columns))
            update_assignments = ', '.join([f"{col} = VALUES({col})" for col in all_columns[1:]])  # Skip item_id
            
            upsert_menu = f"""
            INSERT INTO menu_items ({', '.join(all_columns)}) 
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE 
            {update_assignments}
            """
            
            cursor.execute(upsert_menu, values)
            db_manager.connection.commit()
            
            logger.info(f"Menu item added/updated: {item_id} - {item_name}")
            return True
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error adding menu item: {e}")
            raise Exception(f"Failed to add menu item: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def bulk_insert_menu_items(menu_df):
        """Bulk insert menu items from DataFrame"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Tag columns (only the simplified ones)
            tag_columns = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
            
            all_columns = ['item_id', 'item_name', 'price', 'cuisine', 'category'] + tag_columns
            
            # Clear existing data
            cursor.execute("DELETE FROM menu_items")
            
            # Prepare bulk insert
            placeholders = ', '.join(['%s'] * len(all_columns))
            insert_menu = f"INSERT INTO menu_items ({', '.join(all_columns)}) VALUES ({placeholders})"
            
            # Convert DataFrame to list of tuples
            values_list = []
            for _, row in menu_df.iterrows():
                values = [
                    int(row['item_id']),
                    str(row['item_name']),
                    float(row['price']) if pd.notna(row['price']) else 0.0,
                    str(row.get('cuisine', '')),
                    str(row.get('category', ''))
                ]
                
                # Add tag values
                for tag in tag_columns:
                    values.append(bool(row.get(tag, False)))
                
                values_list.append(tuple(values))
            
            # Execute bulk insert
            cursor.executemany(insert_menu, values_list)
            db_manager.connection.commit()
            
            logger.info(f"Bulk inserted {len(values_list)} menu items")
            return len(values_list)
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error bulk inserting menu items: {e}")
            raise Exception(f"Failed to bulk insert menu items: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def import_predicted_data(csv_file_path):
        """Import predicted menu data from CSV file, clearing existing data first"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            # Read the predicted CSV file
            df = pd.read_csv(csv_file_path)
            
            cursor = db_manager.connection.cursor()
            
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Clear existing menu items
            cursor.execute("DELETE FROM menu_items")
            logger.info("Cleared existing menu items")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # Prepare data for insertion
            tag_columns = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
            
            # Map predicted columns to database columns
            column_mapping = {
                'pred_cuisine': 'cuisine',
                'pred_category': 'category',
                'pred_is_morning': 'is_morning',
                'pred_is_evening': 'is_evening',
                'pred_is_sunny': 'is_sunny',
                'pred_is_rainy': 'is_rainy'
            }
            
            # Prepare data for insertion
            all_columns = ['item_id', 'item_name', 'price', 'cuisine', 'category'] + tag_columns
            placeholders = ', '.join(['%s'] * len(all_columns))
            insert_query = f"INSERT INTO menu_items ({', '.join(all_columns)}) VALUES ({placeholders})"
            
            values_list = []
            for _, row in df.iterrows():
                values = [
                    int(row['item_id']),
                    str(row['item_name']),
                    float(row['price']) if pd.notna(row['price']) else 0.0,
                    str(row.get('pred_cuisine', '')),
                    str(row.get('pred_category', ''))
                ]
                
                # Add tag values (convert 1/0 to True/False, default False for missing)
                values.append(bool(row.get('pred_is_morning', 0)))  # is_morning
                values.append(False)  # is_afternoon (not predicted, default False)
                values.append(bool(row.get('pred_is_evening', 0)))  # is_evening
                values.append(bool(row.get('pred_is_sunny', 0)))    # is_sunny
                values.append(bool(row.get('pred_is_rainy', 0)))    # is_rainy
                
                values_list.append(tuple(values))
            
            # Execute bulk insert
            cursor.executemany(insert_query, values_list)
            db_manager.connection.commit()
            
            logger.info(f"Successfully imported {len(values_list)} menu items from {csv_file_path}")
            return len(values_list)
            
        except Exception as e:
            db_manager.connection.rollback()
            logger.error(f"Error importing predicted data: {e}")
            raise Exception(f"Failed to import predicted data: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_all_menu_items():
        """Get all menu items as DataFrame"""
        if not db_manager.connect():
            return pd.DataFrame()
        
        try:
            query = """
            SELECT * FROM menu_items 
            ORDER BY item_id
            """
            
            df = pd.read_sql(query, db_manager.connection)
            return df
            
        except Error as e:
            logger.error(f"Error fetching menu items: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def get_menu_item_by_id(item_id):
        """Get a single menu item by ID"""
        if not db_manager.connect():
            return None
        
        try:
            cursor = db_manager.connection.cursor(dictionary=True)
            query = "SELECT * FROM menu_items WHERE item_id = %s"
            cursor.execute(query, (item_id,))
            result = cursor.fetchone()
            return result
            
        except Error as e:
            logger.error(f"Error fetching menu item {item_id}: {e}")
            return None
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_menu_by_filters(cuisine=None, category=None, tags=None):
        """Get menu items filtered by cuisine, category, and tags"""
        if not db_manager.connect():
            return pd.DataFrame()
        
        try:
            where_clauses = []
            params = []
            
            if cuisine:
                where_clauses.append("cuisine = %s")
                params.append(cuisine)
            
            if category:
                where_clauses.append("category = %s")
                params.append(category)
            
            if tags:
                for tag in tags:
                    where_clauses.append(f"{tag} = TRUE")
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
            SELECT * FROM menu_items 
            WHERE {where_clause}
            ORDER BY item_id
            """
            
            df = pd.read_sql(query, db_manager.connection, params=params)
            return df
            
        except Error as e:
            logger.error(f"Error fetching filtered menu items: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def delete_menu_item(item_id):
        """Delete a menu item"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            delete_item = "DELETE FROM menu_items WHERE item_id = %s"
            cursor.execute(delete_item, (item_id,))
            db_manager.connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error deleting menu item: {e}")
            raise Exception(f"Failed to delete menu item: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()


class OrderModel:
    """Order model for database operations"""
    
    @staticmethod
    def create_order(user_id, customer_name, customer_email, cart_items, total_amount, payment_method='cash', notes=''):
        """Create a new order with items"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            # Insert order
            insert_order = """
            INSERT INTO orders (user_id, customer_name, customer_email, total_amount, payment_method, notes) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_order, (user_id, customer_name, customer_email, total_amount, payment_method, notes))
            order_id = cursor.lastrowid
            
            # Insert order items
            insert_item = """
            INSERT INTO order_items (order_id, item_id, item_name, item_price, quantity, subtotal, special_instructions) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            for item in cart_items:
                item_id = item.get('item_id')
                item_name = item.get('item_name')
                item_price = float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                subtotal = item_price * quantity
                special_instructions = item.get('special_instructions', '')
                
                cursor.execute(insert_item, (order_id, item_id, item_name, item_price, quantity, subtotal, special_instructions))
            
            db_manager.connection.commit()
            logger.info(f"Order {order_id} created successfully for user {user_id}")
            
            return order_id
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error creating order: {e}")
            raise Exception(f"Failed to create order: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_order_by_id(order_id):
        """Get order details by order ID"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            # Get order details with items
            query = """
            SELECT 
                o.order_id, o.user_id, o.customer_name, o.customer_email,
                o.order_date, o.total_amount, o.order_status, o.payment_method, o.notes,
                oi.order_item_id, oi.item_id, oi.item_name, oi.item_price,
                oi.quantity, oi.subtotal, oi.special_instructions,
                m.cuisine, m.category
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN menu_items m ON oi.item_id = m.item_id
            WHERE o.order_id = %s
            ORDER BY oi.order_item_id
            """
            
            df = pd.read_sql(query, db_manager.connection, params=[order_id])
            return df
            
        except Error as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def get_user_orders(user_id, limit=20):
        """Get orders for a specific user"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            query = """
            SELECT 
                o.order_id, o.customer_name, o.order_date, o.total_amount, 
                o.order_status, o.payment_method,
                COUNT(oi.order_item_id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.user_id = %s
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, db_manager.connection, params=[user_id, limit])
            return df
            
        except Error as e:
            logger.error(f"Error fetching user orders: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
    
    @staticmethod
    def get_all_orders(limit=100):
        """Get all orders (for staff)"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            query = """
            SELECT 
                o.order_id, o.user_id, o.customer_name, o.customer_email, o.order_date, 
                o.total_amount, o.order_status, o.payment_method, o.notes,
                COUNT(oi.order_item_id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, db_manager.connection, params=[limit])
            return df
            
        except Error as e:
            logger.error(f"Error fetching all orders: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()

    @staticmethod
    def update_order_status(order_id, status):
        """Update order status"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            cursor = db_manager.connection.cursor()
            
            update_status = "UPDATE orders SET order_status = %s, updated_at = CURRENT_TIMESTAMP WHERE order_id = %s"
            cursor.execute(update_status, (status, order_id))
            db_manager.connection.commit()
            
            return cursor.rowcount > 0
            
        except Error as e:
            db_manager.connection.rollback()
            logger.error(f"Error updating order status: {e}")
            raise Exception(f"Failed to update order status: {e}")
        finally:
            cursor.close()
            db_manager.disconnect()
    
    @staticmethod
    def get_all_orders(limit=50):
        """Get all orders for staff dashboard"""
        if not db_manager.connect():
            raise Exception("Database connection failed")
        
        try:
            query = """
            SELECT 
                o.order_id, o.user_id, o.customer_name, o.customer_email,
                o.order_date, o.total_amount, o.order_status, o.payment_method,
                COUNT(oi.order_item_id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id
            ORDER BY o.order_date DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, db_manager.connection, params=[limit])
            return df
            
        except Error as e:
            logger.error(f"Error fetching all orders: {e}")
            return pd.DataFrame()
        finally:
            db_manager.disconnect()
