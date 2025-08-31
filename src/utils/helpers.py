# Utility functions
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def validate_data_files():
    """Validate that all required data files exist"""
    from config.settings import LABELED_MENU_PATH, MENU_DATA_PRE_PATH
    
    missing_files = []
    
    if not LABELED_MENU_PATH.exists():
        missing_files.append(str(LABELED_MENU_PATH))
    
    if not MENU_DATA_PRE_PATH.exists():
        missing_files.append(str(MENU_DATA_PRE_PATH))
    
    if missing_files:
        raise FileNotFoundError(f"Missing required data files: {missing_files}")
    
    return True

def create_directory_structure():
    """Create required directory structure"""
    from config.settings import MODELS_DIR, POST_DATA_DIR, DB_DATA_DIR
    
    directories = [MODELS_DIR, POST_DATA_DIR, DB_DATA_DIR]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print("Directory structure created successfully!")

def get_model_info():
    """Get information about trained models"""
    from config.settings import CUISINE_MODEL_PATH, CATEGORY_MODEL_PATH, TAGS_MODEL_PATH
    
    models = {
        'cuisine': CUISINE_MODEL_PATH,
        'category': CATEGORY_MODEL_PATH,
        'tags': TAGS_MODEL_PATH
    }
    
    model_info = {}
    for name, path in models.items():
        model_info[name] = {
            'exists': path.exists(),
            'path': str(path),
            'size': path.stat().st_size if path.exists() else 0
        }
    
    return model_info
