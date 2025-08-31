#!/usr/bin/env python3
"""
Debug script to check data files
"""

import sys
from pathlib import Path
import pandas as pd
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_data_files():
    """Check the data files"""
    print("🔍 Checking data files...")
    
    # Set data file paths
    project_root = Path(__file__).parent
    users_csv = os.path.join(project_root, "data", "DB", "users.csv")
    ratings_csv = os.path.join(project_root, "data", "DB", "ratings.csv")
    menu_csv = os.path.join(project_root, "data", "DB", "SpiciaMenu.csv")
    
    print(f"📁 Users file: {users_csv}")
    print(f"📁 Ratings file: {ratings_csv}")
    print(f"📁 Menu file: {menu_csv}")
    
    # Check if files exist
    for name, filepath in [("Users", users_csv), ("Ratings", ratings_csv), ("Menu", menu_csv)]:
        if os.path.exists(filepath):
            print(f"✅ {name} file exists")
            try:
                df = pd.read_csv(filepath)
                print(f"   📊 Shape: {df.shape}")
                print(f"   📋 Columns: {list(df.columns)}")
                if len(df) > 0:
                    print(f"   🔍 First few rows:")
                    print(df.head())
                else:
                    print(f"   ⚠️ File is empty")
                print()
            except Exception as e:
                print(f"   ❌ Error reading {name} file: {str(e)}")
        else:
            print(f"❌ {name} file does not exist")
    
    # Test specific data matching
    print("🔍 Testing data matching...")
    try:
        ratings = pd.read_csv(ratings_csv)
        menu = pd.read_csv(menu_csv)
        
        print(f"📊 Ratings data: {len(ratings)} rows")
        print(f"📊 Menu data: {len(menu)} rows")
        
        if len(ratings) > 0 and len(menu) > 0:
            # Check if item_ids in ratings exist in menu
            ratings_items = set(ratings['item_id'].unique())
            menu_items = set(menu['item_id'].unique())
            
            matching_items = ratings_items.intersection(menu_items)
            print(f"🔗 Items in both ratings and menu: {len(matching_items)}")
            print(f"📋 Rating item IDs: {sorted(list(ratings_items))}")
            print(f"📋 Menu item IDs: {sorted(list(menu_items))}")
            
            if len(matching_items) == 0:
                print("❌ No matching items between ratings and menu!")
            else:
                print(f"✅ Found {len(matching_items)} matching items")
                
    except Exception as e:
        print(f"❌ Error during data matching test: {str(e)}")

if __name__ == "__main__":
    check_data_files()
