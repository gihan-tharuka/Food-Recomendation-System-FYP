# Data loading and preprocessing utilities
import pandas as pd
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import *

class DataLoader:
    """Handles loading and preprocessing of data files"""
    
    @staticmethod
    def load_menu_data():
        """Load menu data for training"""
        if not LABELED_MENU_PATH.exists():
            raise FileNotFoundError(f"Menu data not found at {LABELED_MENU_PATH}")
        return pd.read_csv(LABELED_MENU_PATH)
    
    @staticmethod
    def load_raw_menu_data():
        """Load raw menu data for prediction"""
        if not MENU_DATA_PRE_PATH.exists():
            raise FileNotFoundError(f"Raw menu data not found at {MENU_DATA_PRE_PATH}")
        return pd.read_csv(MENU_DATA_PRE_PATH)
    
    @staticmethod
    def load_users_data():
        """Load users data - Database or CSV fallback"""
        if USE_DATABASE:
            try:
                from src.models.database_models import UserModel
                users = UserModel.get_all_users()
                # Convert to DataFrame format
                return pd.DataFrame(users)
            except Exception as e:
                print(f"Database error, falling back to CSV: {e}")
                # Fallback to CSV
                if USERS_CSV_PATH.exists():
                    return pd.read_csv(USERS_CSV_PATH)
                else:
                    return pd.DataFrame(columns=['user_id', 'name', 'email'])
        else:
            # Use CSV files
            if USERS_CSV_PATH.exists():
                return pd.read_csv(USERS_CSV_PATH)
            else:
                return pd.DataFrame(columns=['user_id', 'name', 'email'])
    
    @staticmethod
    def load_ratings_data():
        """Load ratings data - Database or CSV fallback"""
        if USE_DATABASE:
            try:
                from src.models.database_models import RatingModel
                return RatingModel.get_all_ratings_dataframe()
            except Exception as e:
                print(f"Database error, falling back to CSV: {e}")
                # Fallback to CSV
                if RATINGS_CSV_PATH.exists():
                    return pd.read_csv(RATINGS_CSV_PATH)
                else:
                    return pd.DataFrame(columns=['user_id', 'item_id', 'rating', 'date'])
        else:
            # Use CSV files
            if RATINGS_CSV_PATH.exists():
                return pd.read_csv(RATINGS_CSV_PATH)
            else:
                return pd.DataFrame(columns=['user_id', 'item_id', 'rating', 'date'])
    
    @staticmethod
    def save_users_data(users_df):
        """Save users data - Database or CSV"""
        if USE_DATABASE:
            try:
                from src.models.database_models import UserModel
                # Note: This is mainly for migration purposes
                # Normal operations should use UserModel.create_user()
                print("Warning: Use UserModel.create_user() for adding new users to database")
                return True
            except Exception as e:
                print(f"Database error, saving to CSV: {e}")
                users_df.to_csv(USERS_CSV_PATH, index=False)
        else:
            users_df.to_csv(USERS_CSV_PATH, index=False)
    
    @staticmethod
    def save_ratings_data(ratings_df):
        """Save ratings data - Database or CSV"""
        if USE_DATABASE:
            try:
                from src.models.database_models import RatingModel
                # Note: This is mainly for migration purposes
                # Normal operations should use RatingModel.add_rating()
                print("Warning: Use RatingModel.add_rating() for adding ratings to database")
                return True
            except Exception as e:
                print(f"Database error, saving to CSV: {e}")
                ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
        else:
            ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
        
    @staticmethod
    def save_predicted_menu(menu_df):
        """Save menu with predictions to both CSV and database"""
        # Always save to CSV
        POST_DATA_DIR.mkdir(exist_ok=True)
        menu_df.to_csv(MENU_DATA_PREDICTED_PATH, index=False)
        print(f"Menu data saved to CSV: {MENU_DATA_PREDICTED_PATH}")
        
        # Also save to database if enabled
        if USE_DATABASE:
            try:
                from src.models.database_models import MenuModel
                count = MenuModel.bulk_insert_menu_items(menu_df)
                print(f"Menu data saved to database: {count} items inserted/updated")
                return True
            except Exception as e:
                print(f"Database error while saving menu, CSV saved successfully: {e}")
                return False
        else:
            print("Database not enabled, only CSV saved")
            return True
    
    @staticmethod
    def load_menu_for_recommendations():
        """Load menu data for recommendations - Database first, then CSV fallback"""
        if USE_DATABASE:
            try:
                from src.models.database_models import MenuModel
                menu_df = MenuModel.get_all_menu_items()
                if not menu_df.empty:
                    print("Menu data loaded from database for recommendations")
                    return menu_df
                else:
                    print("No menu data in database, falling back to CSV")
            except Exception as e:
                print(f"Database error, falling back to CSV: {e}")
        
        # Fallback to CSV
        if MENU_DATA_PREDICTED_PATH.exists():
            print(f"Menu data loaded from CSV: {MENU_DATA_PREDICTED_PATH}")
            return pd.read_csv(MENU_DATA_PREDICTED_PATH)
        elif LABELED_MENU_PATH.exists():
            print(f"Predicted menu not found, using labeled menu: {LABELED_MENU_PATH}")
            return pd.read_csv(LABELED_MENU_PATH)
        else:
            raise FileNotFoundError("No menu data available - neither in database nor CSV files")
