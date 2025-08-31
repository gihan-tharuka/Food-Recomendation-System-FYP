# Configuration settings for Food Recommendation System
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
PRE_DATA_DIR = DATA_DIR / "Pre"
POST_DATA_DIR = DATA_DIR / "Post"
DB_DATA_DIR = DATA_DIR / "DB"

# Model paths
MODELS_DIR = BASE_DIR / "models"
CUISINE_MODEL_PATH = MODELS_DIR / "cuisine_model.joblib"
CATEGORY_MODEL_PATH = MODELS_DIR / "category_model.joblib"
TAGS_MODEL_PATH = MODELS_DIR / "tags_model.joblib"

# Data file paths
LABELED_MENU_PATH = PRE_DATA_DIR / "labeled_menu.csv"
MENU_DATA_PRE_PATH = PRE_DATA_DIR / "menu_data_pre.csv"
TRAINING_DATA_PATH = PRE_DATA_DIR / "singlefile-nodup.csv"
MENU_DATA_PREDICTED_PATH = POST_DATA_DIR / "menu_data_predicted_simplified.csv"

# Legacy CSV paths (for backup/migration purposes)
RATINGS_CSV_PATH = DB_DATA_DIR / "ratings.csv"
USERS_CSV_PATH = DB_DATA_DIR / "users.csv"

# Database configuration - Using MySQL instead of CSV
USE_DATABASE = True  # Set to False to use CSV files
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # XAMPP default
    'database': 'food_recommendation_db'
}

# Model configuration
MODEL_CONFIG = {
    'max_iter': 1000,
    'random_state': 42
}

# Feature configuration
TAG_COLUMNS = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
FEATURE_COLUMNS = ['item_name', 'price']
TARGET_COLUMNS = {
    'cuisine': 'cuisine',
    'category': 'category',
    'tags': TAG_COLUMNS
}
