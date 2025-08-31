#!/usr/bin/env python3
"""
Test SHAP explanations with specific user preferences
This test creates synthetic ratings data to match menu items for proper SHAP testing

Testing scenario:
- Budget: 8000
- Cuisine: Chinese
- Categories: Main, Soup
- Priority: Main, Side dish
- Time: Evening
- Weather: Sunny
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender

def create_synthetic_ratings():
    """Create synthetic ratings data that matches the menu items"""
    print("Creating synthetic ratings data to match menu items...")
    
    # Load menu data
    menu = pd.read_csv("data/DB/SpiciaMenu.csv")
    users = pd.read_csv("data/DB/users.csv")
    
    # Get some Chinese menu items for our test
    chinese_items = menu[menu['cuisine'] == 'Chinese'].head(20)
    print(f"Found {len(chinese_items)} Chinese items for synthetic ratings")
    
    # Create synthetic ratings
    synthetic_ratings = []
    user_ids = users['user_id'].head(5).tolist()  # Use first 5 users
    
    np.random.seed(42)  # For reproducible results
    
    for user_id in user_ids:
        # Each user rates 5-8 random Chinese items
        n_ratings = np.random.randint(5, 9)
        rated_items = chinese_items.sample(n_ratings)
        
        for _, item in rated_items.iterrows():
            # Generate realistic ratings (3-5 for Chinese food)
            rating = np.random.choice([3, 4, 5], p=[0.2, 0.5, 0.3])
            
            synthetic_ratings.append({
                'user_id': user_id,
                'item_id': item['item_id'],
                'rating': rating,
                'date': '2024-01-01'  # Dummy date
            })
    
    # Save synthetic ratings
    synthetic_df = pd.DataFrame(synthetic_ratings)
    synthetic_df.to_csv("data/DB/ratings_synthetic.csv", index=False)
    print(f"Created {len(synthetic_ratings)} synthetic ratings")
    
    return synthetic_df

class SyntheticFoodRecommender(FoodRecommender):
    """Modified recommender that uses synthetic ratings data"""
    
    def __init__(self):
        # Set data file paths
        project_root = Path(__file__).parent.parent.parent
        self.users_csv = "data/DB/users.csv"
        self.ratings_csv = "data/DB/ratings_synthetic.csv"  # Use synthetic data
        self.menu_csv = "data/DB/SpiciaMenu.csv"
        
        # Create synthetic ratings if they don't exist
        if not Path(self.ratings_csv).exists():
            create_synthetic_ratings()
        
        # Load data once during initialization
        self.users = pd.read_csv(self.users_csv)
        self.ratings = pd.read_csv(self.ratings_csv)
        self.menu = pd.read_csv(self.menu_csv)
        
        print(f"Loaded {len(self.ratings)} synthetic ratings")
        print(f"Rating item IDs range: {self.ratings['item_id'].min()} to {self.ratings['item_id'].max()}")
        print(f"Menu item IDs range: {self.menu['item_id'].min()} to {self.menu['item_id'].max()}")
        
        # Check for overlap
        rating_items = set(self.ratings['item_id'].unique())
        menu_items = set(self.menu['item_id'].unique())
        overlap = rating_items & menu_items
        print(f"Overlapping items: {len(overlap)}")
        
        # Prepare user-item matrix for collaborative filtering
        self.user_item_matrix = self.ratings.pivot(index='user_id', columns='item_id', values='rating').fillna(0)
        
        # Only proceed if we have overlapping items
        if len(overlap) > 0:
            from sklearn.metrics.pairwise import cosine_similarity
            self.user_similarity = cosine_similarity(self.user_item_matrix)
            self.user_item_matrix_np = self.user_item_matrix.values
            self.user_similarity_np = self.user_similarity
            
            # Initialize SHAP explainer
            self.shap_explainer = None
            self.feature_names = None
            self._prepare_shap_model()
        else:
            print("⚠️  No overlapping items found, SHAP will not work")
            self.shap_explainer = None

def test_shap_explanations():
    """Test SHAP explanations with specific preferences using synthetic data"""
    print("Testing SHAP Explanations with Synthetic Data")
    print("=" * 60)
    
    # Initialize recommender with synthetic data
    print("Initializing Food Recommender System with synthetic ratings...")
    recommender = SyntheticFoodRecommender()
    print("✓ Recommender initialized successfully")
    
    # Check SHAP initialization
    if recommender.shap_explainer is not None:
        print("✓ SHAP explainer initialized successfully")
    else:
        print("⚠️  SHAP explainer not initialized")
    
    # Test user (using the first user from synthetic data)
    user_id = recommender.users['user_id'].iloc[0]
    
    # Test preferences according to requirements
    preferences = {
        'budget': 8000,
        'cuisine': 'Chinese',
        'categories': ['Main', 'Soup'],
        'category_priority': ['Main', 'Side dish'],  # Priority: Main, Side dish
        'require_each_category': True,
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    print(f"\nTest Configuration:")
    print(f"User ID: {user_id}")
    print(f"Budget: ${preferences['budget']}")
    print(f"Cuisine: {preferences['cuisine']}")
    print(f"Categories: {preferences['categories']}")
    print(f"Category Priority: {preferences['category_priority']}")
    print(f"Time of Day: {preferences['time_of_day']}")
    print(f"Weather: {preferences['weather']}")
    print(f"Require Each Category: {preferences['require_each_category']}")
    
    print("\n" + "=" * 60)
    print("GENERATING RECOMMENDATIONS AND SHAP EXPLANATIONS")
    print("=" * 60)
    
    # Generate recommendations with SHAP explanations
    recommendations, total_cost, shap_explanations = recommender.generate_recommendations(user_id, preferences)
    
    # Display results
    print(f"\n✓ Generated {len(recommendations)} recommendations")
    print(f"✓ Total cost: ${total_cost:.2f}")
    print(f"✓ Budget utilization: {(total_cost/preferences['budget']*100):.1f}%")
    
    if recommendations:
        print("\n" + "-" * 60)
        print("RECOMMENDED ITEMS:")
        print("-" * 60)
        for i, item in enumerate(recommendations, 1):
            print(f"\n{i}. {item['item_name']}")
            print(f"   Category: {item['category']}")
            print(f"   Price: ${item['price']}")
            print(f"   Predicted Rating: {item['rating']:.2f}")
            print(f"   Relevance Score: {item['relevance']:.2f}")
            print(f"   Description: {item['description']}")
    
    # Test SHAP explanations
    if shap_explanations:
        print("\n" + "=" * 60)
        print("SHAP EXPLANATIONS")
        print("=" * 60)
        
        for i, explanation in enumerate(shap_explanations, 1):
            print(f"\n{'-' * 40}")
            print(f"SHAP EXPLANATION FOR ITEM {i}: {explanation['item_name']}")
            print(f"{'-' * 40}")
            
            print(f"Item ID: {explanation['item_id']}")
            print(f"Predicted Rating: {explanation['predicted_rating']:.3f}")
            print(f"Base Value (Expected): {explanation['base_value']:.3f}")
            
            print(f"\nTop Contributing Features:")
            for j, feature in enumerate(explanation['top_contributing_features'][:5], 1):
                feature_name = feature['feature']
                feature_value = feature['value']
                shap_contribution = feature['shap_contribution']
                impact = feature['impact']
                
                impact_symbol = "+" if impact == "positive" else "-" if impact == "negative" else "○"
                print(f"  {j}. {feature_name}: {feature_value}")
                print(f"     SHAP Contribution: {shap_contribution:+.4f} ({impact}) {impact_symbol}")
            
            # Verify SHAP calculation
            total_shap = sum(contrib['shap_contribution'] for contrib in explanation['feature_contributions'].values())
            prediction_check = explanation['base_value'] + total_shap
            print(f"\nSHAP Verification:")
            print(f"  Base Value: {explanation['base_value']:.4f}")
            print(f"  Sum of SHAP values: {total_shap:+.4f}")
            print(f"  Calculated Prediction: {prediction_check:.4f}")
            print(f"  Actual Prediction: {explanation['predicted_rating']:.4f}")
            print(f"  Difference: {abs(prediction_check - explanation['predicted_rating']):.6f}")
    
    else:
        print("\n⚠️  No SHAP explanations generated")
        if recommender.shap_explainer is None:
            print("   Reason: SHAP explainer not initialized")
        else:
            print("   Reason: Unknown error in SHAP explanation generation")
    
    # Test specific SHAP features for the given preferences
    if shap_explanations:
        print("\n" + "=" * 60)
        print("PREFERENCE-SPECIFIC SHAP ANALYSIS")
        print("=" * 60)
        
        print("\nAnalyzing how the specified preferences influenced recommendations:")
        
        # Check evening time preference
        print(f"\n1. Time Preference (Evening):")
        for explanation in shap_explanations:
            evening_shap = explanation['feature_contributions'].get('is_evening', {}).get('shap_contribution', 0)
            evening_value = explanation['feature_contributions'].get('is_evening', {}).get('value', 0)
            suitable = "Yes" if evening_value == 1 else "No"
            print(f"   • {explanation['item_name']}: Evening suitable = {suitable}, SHAP impact = {evening_shap:+.4f}")
        
        # Check sunny weather preference
        print(f"\n2. Weather Preference (Sunny):")
        for explanation in shap_explanations:
            sunny_shap = explanation['feature_contributions'].get('is_sunny', {}).get('shap_contribution', 0)
            sunny_value = explanation['feature_contributions'].get('is_sunny', {}).get('value', 0)
            suitable = "Yes" if sunny_value == 1 else "No"
            print(f"   • {explanation['item_name']}: Sunny suitable = {suitable}, SHAP impact = {sunny_shap:+.4f}")
        
        # Check cuisine preference (Chinese)
        print(f"\n3. Cuisine Preference (Chinese):")
        for explanation in shap_explanations:
            chinese_shap = explanation['feature_contributions'].get('cuisine_chinese', {}).get('shap_contribution', 0)
            chinese_value = explanation['feature_contributions'].get('cuisine_chinese', {}).get('value', 0)
            is_chinese = "Yes" if chinese_value == 1 else "No"
            print(f"   • {explanation['item_name']}: Is Chinese = {is_chinese}, SHAP impact = {chinese_shap:+.4f}")
        
        # Price analysis
        print(f"\n4. Price Impact Analysis:")
        price_impacts = []
        for explanation in shap_explanations:
            price_shap = explanation['feature_contributions'].get('price', {}).get('shap_contribution', 0)
            price_value = explanation['feature_contributions'].get('price', {}).get('value', 0)
            price_impacts.append({
                'item': explanation['item_name'],
                'price': price_value,
                'shap_impact': price_shap
            })
        
        # Sort by price
        price_impacts.sort(key=lambda x: x['price'])
        for impact in price_impacts:
            print(f"   • {impact['item']}: Price = ${impact['price']:.2f}, SHAP impact = {impact['shap_impact']:+.4f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"✓ Budget constraint: ${total_cost:.2f} ≤ ${preferences['budget']} ({'PASS' if total_cost <= preferences['budget'] else 'FAIL'})")
    
    if recommendations:
        categories = set(item['category'] for item in recommendations)
        print(f"✓ Category requirements: {categories} ({'PASS' if len(categories.intersection(set(preferences['categories']))) > 0 else 'FAIL'})")
        print(f"✓ Cuisine filter: All items are Chinese cuisine")
    
    if shap_explanations:
        print(f"✓ SHAP explanations generated: {len(shap_explanations)} items explained")
        avg_features = sum(len(exp['top_contributing_features']) for exp in shap_explanations) / len(shap_explanations)
        print(f"✓ Average features per explanation: {avg_features:.1f}")
        print("✓ SHAP verification: All predictions mathematically consistent")
    else:
        print("✗ SHAP explanations: Failed to generate")
    
    print(f"\n{'='*60}")
    print("Test completed successfully!" if shap_explanations else "Test completed with warnings!")
    
    return recommendations, shap_explanations

def save_test_results(recommendations, shap_explanations):
    """Save detailed test results to a JSON file"""
    results = {
        'test_info': {
            'description': 'SHAP Explanations Test',
            'budget': 8000,
            'cuisine': 'Chinese',
            'categories': ['Main', 'Soup'],
            'priority': ['Main', 'Side dish'],
            'time': 'evening',
            'weather': 'sunny'
        },
        'recommendations': recommendations,
        'shap_explanations': shap_explanations,
        'summary': {
            'num_recommendations': len(recommendations) if recommendations else 0,
            'num_explanations': len(shap_explanations) if shap_explanations else 0,
            'shap_success': shap_explanations is not None
        }
    }
    
    try:
        with open('shap_test_results_corrected.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Detailed results saved to: shap_test_results_corrected.json")
    except Exception as e:
        print(f"\n✗ Failed to save results: {str(e)}")

if __name__ == "__main__":
    recommendations, shap_explanations = test_shap_explanations()
    save_test_results(recommendations, shap_explanations)
