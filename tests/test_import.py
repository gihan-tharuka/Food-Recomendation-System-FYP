#!/usr/bin/env python3
"""
Test script for the database import functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.database_models import MenuModel
from config.settings import POST_DATA_DIR

def test_import():
    """Test the database import functionality"""
    try:
        predicted_csv_path = POST_DATA_DIR / "Spicia-menu-predicted.csv"
        
        if not predicted_csv_path.exists():
            print(f"❌ Predicted CSV file not found: {predicted_csv_path}")
            return False
        
        print(f"📁 Using predicted data from: {predicted_csv_path}")
        print("🔄 Importing to database...")
        
        count = MenuModel.import_predicted_data(str(predicted_csv_path))
        
        print(f"✅ Successfully imported {count} menu items to database!")
        return True
        
    except Exception as e:
        print(f"❌ Error importing to database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    if not success:
        sys.exit(1)
