#!/usr/bin/env python3
"""
Test script to reproduce and verify the category priority issue
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.models.recommender import FoodRecommender

def test_category_priority_issue():
    """Test the category priority issue with International cuisine"""
    print("🧪 Testing Category Priority Issue...")
    
    # Initialize recommender
    recommender = FoodRecommender()
    
    # Test case: International cuisine, dessert (priority 1) and beverage (priority 2)
    print("\n" + "="*70)
    print("TEST: Category Priority Issue Reproduction")
    print("="*70)
    
    preferences = {
        'budget': 3000,
        'cuisine': 'International',
        'categories': ['Dessert', 'Beverage'],
        'category_priority': ['Dessert', 'Beverage'],  # Dessert should get more budget
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    print(f"Budget: ₹{preferences['budget']}")
    print(f"Cuisine: {preferences['cuisine']}")
    print(f"Categories: {preferences['categories']}")
    print(f"Priority Order: {preferences['category_priority']} (1st gets more budget)")
    print(f"Context: {preferences['time_of_day']}, {preferences['weather']}")
    
    recommendations, cost, explanations = recommender.generate_recommendations(
        user_id=1, preferences=preferences
    )
    
    print(f"\n📊 Results:")
    print(f"Total Cost: ₹{cost}")
    print("\nSelected Items:")
    
    category_costs = {}
    category_counts = {}
    
    for i, rec in enumerate(recommendations, 1):
        category = rec['category']
        price = rec['price']
        
        # Track costs and counts by category
        category_costs[category] = category_costs.get(category, 0) + price
        category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"{i}. {rec['item_name']} - ₹{price} ({category})")
    
    print(f"\n📈 Category Budget Allocation:")
    total_cost = sum(category_costs.values())
    for category in preferences['categories']:
        spent = category_costs.get(category, 0)
        percentage = (spent / total_cost * 100) if total_cost > 0 else 0
        count = category_counts.get(category, 0)
        print(f"  {category}: ₹{spent} ({percentage:.1f}%) - {count} items")
    
    # Calculate expected priority allocation
    print(f"\n🎯 Expected vs Actual Priority Allocation:")
    priority_weights = {cat: len(preferences['category_priority']) - idx 
                       for idx, cat in enumerate(preferences['category_priority'])}
    priority_total = sum(priority_weights.values())
    
    for cat, weight in priority_weights.items():
        expected_percentage = (weight / priority_total) * 100
        actual_percentage = (category_costs.get(cat, 0) / total_cost * 100) if total_cost > 0 else 0
        print(f"  {cat}: Expected {expected_percentage:.1f}%, Actual {actual_percentage:.1f}%")
        
        # Check if priority is respected
        if cat == 'Dessert' and actual_percentage < expected_percentage * 0.7:  # Allow 30% tolerance
            print(f"    ❌ ISSUE: {cat} (priority 1) got much less budget than expected!")
        elif cat == 'Dessert':
            print(f"    ✅ OK: {cat} priority respected")
    
    # Check for the specific issue: dessert getting less than beverage
    dessert_cost = category_costs.get('Dessert', 0)
    beverage_cost = category_costs.get('Beverage', 0)
    
    print(f"\n🔍 Priority Issue Check:")
    if dessert_cost > 0 and beverage_cost > 0:
        if dessert_cost < beverage_cost:
            print(f"❌ CONFIRMED ISSUE: Dessert (₹{dessert_cost}) got less budget than Beverage (₹{beverage_cost})")
            print("   This violates the priority order where Dessert should get more budget!")
            return False
        else:
            print(f"✅ Priority respected: Dessert (₹{dessert_cost}) >= Beverage (₹{beverage_cost})")
            return True
    else:
        print("⚠️ Cannot verify - one category has no items selected")
        return None

if __name__ == "__main__":
    test_category_priority_issue()
