#!/usr/bin/env python3
"""
Debug script to check all ratings files for matching data
"""

import sys
from pathlib import Path
import pandas as pd
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_all_ratings_files():
    """Check all ratings files for matching item IDs with menu"""
    print("🔍 Checking all ratings files...")
    
    # Set data file paths
    project_root = Path(__file__).parent
    db_dir = os.path.join(project_root, "data", "DB")
    menu_csv = os.path.join(db_dir, "SpiciaMenu.csv")
    
    # Load menu data
    menu = pd.read_csv(menu_csv)
    menu_items = set(menu['item_id'].unique())
    print(f"📊 Menu items range: {min(menu_items)} - {max(menu_items)} ({len(menu_items)} items)")
    
    # Check all ratings files
    ratings_files = [
        "ratings.csv",
        "ratings_shap_test.csv", 
        "ratings_synthetic.csv"
    ]
    
    for ratings_file in ratings_files:
        ratings_path = os.path.join(db_dir, ratings_file)
        if os.path.exists(ratings_path):
            print(f"\n📁 Checking {ratings_file}:")
            try:
                ratings = pd.read_csv(ratings_path)
                print(f"   📊 Shape: {ratings.shape}")
                print(f"   📋 Columns: {list(ratings.columns)}")
                
                if 'item_id' in ratings.columns:
                    ratings_items = set(ratings['item_id'].unique())
                    matching_items = ratings_items.intersection(menu_items)
                    
                    print(f"   📊 Rating items range: {min(ratings_items)} - {max(ratings_items)} ({len(ratings_items)} unique items)")
                    print(f"   🔗 Matching items: {len(matching_items)}")
                    
                    if len(matching_items) > 0:
                        print(f"   ✅ Found {len(matching_items)} matching items - this file can be used for SHAP!")
                        print(f"   📋 Sample matching item IDs: {sorted(list(matching_items))[:10]}")
                    else:
                        print(f"   ❌ No matching items")
                else:
                    print(f"   ❌ No 'item_id' column found")
                    
            except Exception as e:
                print(f"   ❌ Error reading file: {str(e)}")
        else:
            print(f"❌ {ratings_file} does not exist")

if __name__ == "__main__":
    check_all_ratings_files()
