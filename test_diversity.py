#!/usr/bin/env python3
"""
Test script to verify diversity improvements in the recommender system
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.models.recommender import FoodRecommender

def test_diversity():
    """Test the diversity constraints in recommendations"""
    print("🧪 Testing Recommender Diversity...")
    
    # Initialize recommender
    recommender = FoodRecommender()
    
    # Test case 1: Chinese cuisine with soup category (should avoid multiple sweet corn soups)
    print("\n" + "="*60)
    print("TEST 1: Chinese Cuisine with Soup Category")
    print("="*60)
    
    preferences1 = {
        'budget': 3000,
        'cuisine': 'Chinese',
        'categories': ['Soup'],
        'time_of_day': 'afternoon',
        'weather': 'rainy'
    }
    
    recommendations1, cost1, explanations1 = recommender.generate_recommendations(
        user_id=1, preferences=preferences1
    )
    
    print(f"\n📊 Recommendations for Chinese Soup (Budget: {preferences1['budget']}):")
    print(f"Total Cost: {cost1}")
    print("\nSelected Items:")
    dish_types = {}
    for i, rec in enumerate(recommendations1, 1):
        dish_type = recommender._extract_dish_type(rec['item_name'])
        dish_types[dish_type] = dish_types.get(dish_type, 0) + 1
        print(f"{i}. {rec['item_name']} - ₹{rec['price']} (Type: {dish_type})")
    
    print(f"\nDish Type Distribution: {dish_types}")
    
    # Check if we have too many similar items
    max_same_type = max(dish_types.values()) if dish_types else 0
    if max_same_type <= 2:
        print("✅ PASS: No more than 2 items of the same dish type")
    else:
        print(f"❌ FAIL: Found {max_same_type} items of the same dish type")
    
    # Test case 2: Asian cuisine with side dish category (should avoid multiple chicken dishes)
    print("\n" + "="*60)
    print("TEST 2: Asian Cuisine with Side Dish Category")
    print("="*60)
    
    preferences2 = {
        'budget': 4000,
        'cuisine': 'Asian',
        'categories': ['Side dish'],
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    recommendations2, cost2, explanations2 = recommender.generate_recommendations(
        user_id=2, preferences=preferences2
    )
    
    print(f"\n📊 Recommendations for Asian Side Dishes (Budget: {preferences2['budget']}):")
    print(f"Total Cost: {cost2}")
    print("\nSelected Items:")
    dish_types2 = {}
    for i, rec in enumerate(recommendations2, 1):
        dish_type = recommender._extract_dish_type(rec['item_name'])
        dish_types2[dish_type] = dish_types2.get(dish_type, 0) + 1
        print(f"{i}. {rec['item_name']} - ₹{rec['price']} (Type: {dish_type})")
    
    print(f"\nDish Type Distribution: {dish_types2}")
    
    # Check if we have too many similar items
    max_same_type2 = max(dish_types2.values()) if dish_types2 else 0
    if max_same_type2 <= 2:
        print("✅ PASS: No more than 2 items of the same dish type")
    else:
        print(f"❌ FAIL: Found {max_same_type2} items of the same dish type")
    
    # Test case 3: Multiple categories to test overall diversity
    print("\n" + "="*60)
    print("TEST 3: Multiple Categories for Overall Diversity")
    print("="*60)
    
    preferences3 = {
        'budget': 5000,
        'cuisine': 'Asian',
        'categories': ['Soup', 'Side dish', 'Main Course'],
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    recommendations3, cost3, explanations3 = recommender.generate_recommendations(
        user_id=3, preferences=preferences3
    )
    
    print(f"\n📊 Recommendations for Multiple Categories (Budget: {preferences3['budget']}):")
    print(f"Total Cost: {cost3}")
    print("\nSelected Items:")
    dish_types3 = {}
    categories3 = {}
    for i, rec in enumerate(recommendations3, 1):
        dish_type = recommender._extract_dish_type(rec['item_name'])
        category = rec['category']
        dish_types3[dish_type] = dish_types3.get(dish_type, 0) + 1
        categories3[category] = categories3.get(category, 0) + 1
        print(f"{i}. {rec['item_name']} - ₹{rec['price']} (Category: {category}, Type: {dish_type})")
    
    print(f"\nDish Type Distribution: {dish_types3}")
    print(f"Category Distribution: {categories3}")
    
    # Check diversity across categories
    max_same_type3 = max(dish_types3.values()) if dish_types3 else 0
    if max_same_type3 <= 2:
        print("✅ PASS: No more than 2 items of the same dish type")
    else:
        print(f"❌ FAIL: Found {max_same_type3} items of the same dish type")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("The enhanced recommender now includes:")
    print("1. ✅ Dish type classification to identify similar items")
    print("2. ✅ Constraints to limit max 2 items per dish type family")
    print("3. ✅ Preference for variety when multiple dish types available")
    print("4. ✅ Fallback selection with diversity considerations")
    print("\nThis should significantly reduce the selection of very similar items!")

if __name__ == "__main__":
    test_diversity()
