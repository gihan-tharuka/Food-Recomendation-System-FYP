#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender

def test_recommender():
    """Test the food recommender system"""
    print("Testing Food Recommender System...")
    
    # Initialize recommender
    recommender = FoodRecommender()
    print("✓ Recommender initialized successfully")
    
    # Test getting available cuisines
    cuisines = recommender.get_available_cuisines()
    print(f"✓ Available cuisines: {cuisines}")
    
    # Test getting available categories for Thai cuisine
    categories = recommender.get_available_categories('Thai')
    print(f"✓ Available categories for Thai cuisine: {categories}")
    
    # Test recommendation generation
    user_id = "bob001"  # This user exists in ratings.csv
    preferences = {
        'budget': 3000,
        'cuisine': 'Thai',
        'categories': ['Soup', 'Main'],
        'category_priority': ['Main', 'Soup'],
        'require_each_category': True,
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    print(f"\nGenerating recommendations for user: {user_id}")
    print(f"Preferences: {preferences}")
    
    recommendations, explanations, total_cost = recommender.generate_recommendations(user_id, preferences)
    
    print(f"\n✓ Generated {len(recommendations)} recommendations")
    print(f"✓ Total cost: {total_cost}")
    
    if recommendations:
        print("\nRecommended items:")
        for i, item in enumerate(recommendations, 1):
            print(f"{i}. {item['item_name']} ({item['category']}) - ${item['price']}")
            print(f"   Rating: {item['rating']:.1f}, Relevance: {item['relevance']:.2f}")
            print(f"   Explanation: {item['explanation']}")
            print()
    
    print("✓ Test completed successfully!")

if __name__ == "__main__":
    test_recommender()
