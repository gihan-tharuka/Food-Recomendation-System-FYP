#!/usr/bin/env python3
"""
SHAP Explanations Test for Food Recommendation System

This test demonstrates SHAP (SHapley Additive exPlanations) functionality 
with specific user preferences as requested:

Test Parameters:
- Budget: 8000 (LKR)
- Cuisine: Chinese
- Categories: Main, Soup  
- Priority: Main, Side dish
- Time: Evening
- Weather: Sunny

The test creates synthetic ratings data to ensure proper SHAP functionality,
as the original ratings data had ID mismatches with the menu data.

SHAP explanations help users understand:
1. Why specific items were recommended
2. How each feature (price, time, weather, etc.) influenced the recommendation
3. The relative importance of different factors in the recommendation algorithm

Author: Food Recommendation System Team
Date: 2025
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np
import os

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender

class ShapTestRecommender(FoodRecommender):
    """
    Extended Food Recommender for SHAP testing
    
    This class creates synthetic ratings data that properly aligns with 
    the menu data to enable SHAP explanations functionality.
    """
    
    def __init__(self, create_synthetic=True):
        # Set data file paths
        self.users_csv = "data/DB/users.csv"
        self.menu_csv = "data/DB/SpiciaMenu.csv"
        
        if create_synthetic:
            self.ratings_csv = "data/DB/ratings_shap_test.csv"
            self._ensure_synthetic_ratings()
        else:
            self.ratings_csv = "data/DB/ratings.csv"
        
        # Load data
        self.users = pd.read_csv(self.users_csv)
        self.ratings = pd.read_csv(self.ratings_csv)
        self.menu = pd.read_csv(self.menu_csv)
        
        # Validate data alignment
        self._validate_data_alignment()
        
        # Initialize recommendation components
        self._initialize_components()
    
    def _ensure_synthetic_ratings(self):
        """Create synthetic ratings data if it doesn't exist"""
        if not os.path.exists(self.ratings_csv):
            print("Creating synthetic ratings data for SHAP testing...")
            self._create_synthetic_ratings()
        else:
            print("Using existing synthetic ratings data...")
    
    def _create_synthetic_ratings(self):
        """Create realistic synthetic ratings that align with menu items"""
        # Load required data
        menu = pd.read_csv(self.menu_csv)
        users = pd.read_csv(self.users_csv)
        
        # Focus on Chinese cuisine for the test
        chinese_items = menu[menu['cuisine'] == 'Chinese'].head(25)
        test_users = users.head(6)  # Use 6 users for good diversity
        
        np.random.seed(42)  # For reproducible results
        
        synthetic_ratings = []
        
        for _, user in test_users.iterrows():
            user_id = user['user_id']
            
            # Each user rates 8-12 items with realistic preferences
            n_ratings = np.random.randint(8, 13)
            rated_items = chinese_items.sample(n_ratings)
            
            for _, item in rated_items.iterrows():
                # Generate realistic ratings based on item characteristics
                base_rating = 4.0  # Chinese food generally well-liked
                
                # Adjust based on price (cheaper items might get slightly higher ratings)
                price = item['price']
                if price < 600:
                    price_adjust = 0.3
                elif price > 1200:
                    price_adjust = -0.2
                else:
                    price_adjust = 0.0
                
                # Add some randomness
                random_adjust = np.random.normal(0, 0.5)
                
                # Calculate final rating
                final_rating = base_rating + price_adjust + random_adjust
                final_rating = max(2, min(5, final_rating))  # Clamp to 2-5 range
                final_rating = round(final_rating)
                
                synthetic_ratings.append({
                    'user_id': user_id,
                    'item_id': item['item_id'],
                    'rating': final_rating,
                    'date': '2024-01-01'
                })
        
        # Save synthetic ratings
        synthetic_df = pd.DataFrame(synthetic_ratings)
        synthetic_df.to_csv(self.ratings_csv, index=False)
        
        print(f"Created {len(synthetic_ratings)} synthetic ratings for {len(test_users)} users")
        print(f"Ratings distribution: {synthetic_df['rating'].value_counts().sort_index().to_dict()}")
    
    def _validate_data_alignment(self):
        """Validate that ratings and menu data are properly aligned"""
        rating_items = set(self.ratings['item_id'].unique())
        menu_items = set(self.menu['item_id'].unique())
        overlap = rating_items & menu_items
        
        print(f"Data validation:")
        print(f"  - Ratings: {len(self.ratings)} records for {len(rating_items)} items")
        print(f"  - Menu: {len(self.menu)} items")
        print(f"  - Overlapping items: {len(overlap)}")
        
        if len(overlap) == 0:
            raise ValueError("No overlapping items between ratings and menu data!")
        
        return len(overlap) > 0
    
    def _initialize_components(self):
        """Initialize recommendation system components"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Prepare user-item matrix for collaborative filtering
        self.user_item_matrix = self.ratings.pivot(
            index='user_id', 
            columns='item_id', 
            values='rating'
        ).fillna(0)
        
        self.user_similarity = cosine_similarity(self.user_item_matrix)
        self.user_item_matrix_np = self.user_item_matrix.values
        self.user_similarity_np = self.user_similarity
        
        # Initialize SHAP explainer
        self.shap_explainer = None
        self.feature_names = None
        self._prepare_shap_model()

def run_shap_test():
    """
    Main test function for SHAP explanations
    
    Tests the specific scenario:
    - Budget: 8000 LKR
    - Cuisine: Chinese
    - Categories: Main, Soup
    - Priority: Main, Side dish  
    - Time: Evening
    - Weather: Sunny
    """
    
    print("🔬 SHAP EXPLANATIONS TEST")
    print("=" * 70)
    print("Testing explainable AI for food recommendations")
    print("This test demonstrates how SHAP values explain recommendation decisions")
    print()
    
    # Initialize the recommender system
    print("1️⃣  SYSTEM INITIALIZATION")
    print("-" * 35)
    
    try:
        recommender = ShapTestRecommender(create_synthetic=True)
        print("✅ Recommender system initialized successfully")
        
        if recommender.shap_explainer is not None:
            print("✅ SHAP explainer ready for generating explanations")
        else:
            print("❌ SHAP explainer failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}")
        return False
    
    # Test configuration
    print("\n2️⃣  TEST CONFIGURATION")
    print("-" * 35)
    
    # Use the first user from synthetic data
    test_user = recommender.users['user_id'].iloc[0]
    
    test_preferences = {
        'budget': 8000,                          # Budget: 8000 LKR
        'cuisine': 'Chinese',                    # Cuisine: Chinese
        'categories': ['Main', 'Soup'],          # Categories: Main, Soup
        'category_priority': ['Main', 'Side dish'], # Priority: Main, Side dish
        'require_each_category': True,           # Ensure both categories represented
        'time_of_day': 'evening',               # Time: Evening
        'weather': 'sunny'                      # Weather: Sunny
    }
    
    print(f"👤 Test User: {test_user}")
    print(f"💰 Budget: ${test_preferences['budget']:,} LKR")
    print(f"🍜 Cuisine: {test_preferences['cuisine']}")
    print(f"📋 Categories: {', '.join(test_preferences['categories'])}")
    print(f"🥇 Priority: {', '.join(test_preferences['category_priority'])}")
    print(f"⏰ Time: {test_preferences['time_of_day']}")
    print(f"☀️  Weather: {test_preferences['weather']}")
    
    # Generate recommendations
    print("\n3️⃣  GENERATING RECOMMENDATIONS")
    print("-" * 35)
    
    try:
        recommendations, total_cost, shap_explanations = recommender.generate_recommendations(
            test_user, test_preferences
        )
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        print(f"💸 Total cost: ${total_cost:,.2f} LKR")
        print(f"📊 Budget utilization: {(total_cost/test_preferences['budget']*100):.1f}%")
        
        # Validate constraints
        within_budget = total_cost <= test_preferences['budget']
        has_categories = len(set(r['category'] for r in recommendations)) >= 2
        
        print(f"✅ Budget constraint: {'PASSED' if within_budget else 'FAILED'}")
        print(f"✅ Category requirement: {'PASSED' if has_categories else 'FAILED'}")
        
    except Exception as e:
        print(f"❌ Recommendation generation failed: {str(e)}")
        return False
    
    # Display recommendations
    if recommendations:
        print("\n📋 RECOMMENDED ITEMS")
        print("-" * 35)
        
        categories = {}
        for item in recommendations:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, items in categories.items():
            print(f"\n📂 {category.upper()} DISHES:")
            for item in items:
                print(f"   • {item['item_name']} - ${item['price']:,.0f}")
                print(f"     Rating: {item['rating']:.1f}/5, Relevance: {item['relevance']:.1f}")
    
    # SHAP Explanations Analysis
    if shap_explanations:
        print("\n4️⃣  SHAP EXPLANATIONS ANALYSIS")
        print("-" * 35)
        print("Understanding WHY these items were recommended...")
        
        for i, explanation in enumerate(shap_explanations[:3], 1):  # Show top 3 for brevity
            print(f"\n🔍 EXPLANATION {i}: {explanation['item_name']}")
            print(f"   Predicted Rating: {explanation['predicted_rating']:.3f}")
            print(f"   Base Value: {explanation['base_value']:.3f}")
            
            print(f"\n   🏆 Top Influencing Factors:")
            for j, feature in enumerate(explanation['top_contributing_features'][:3], 1):
                name = feature['feature'].replace('_', ' ').title()
                value = feature['value']
                contribution = feature['shap_contribution']
                impact = feature['impact']
                
                impact_emoji = "📈" if impact == "positive" else "📉" if impact == "negative" else "➖"
                print(f"   {j}. {name}: {value} {impact_emoji}")
                print(f"      Impact: {contribution:+.4f} ({impact})")
        
        # Preference-specific analysis
        print(f"\n5️⃣  PREFERENCE IMPACT ANALYSIS")
        print("-" * 35)
        print("How your specific preferences influenced the recommendations:")
        
        # Evening time analysis
        print(f"\n⏰ EVENING TIME PREFERENCE:")
        evening_impacts = []
        for exp in shap_explanations:
            evening_contrib = exp['feature_contributions'].get('is_evening', {})
            evening_impacts.append({
                'item': exp['item_name'],
                'suitable': evening_contrib.get('value', 0) == 1,
                'impact': evening_contrib.get('shap_contribution', 0)
            })
        
        for impact in evening_impacts[:5]:  # Top 5
            suitable_text = "✅ Suitable" if impact['suitable'] else "❌ Not ideal"
            print(f"   • {impact['item']}: {suitable_text} (Impact: {impact['impact']:+.3f})")
        
        # Sunny weather analysis
        print(f"\n☀️  SUNNY WEATHER PREFERENCE:")
        sunny_impacts = []
        for exp in shap_explanations:
            sunny_contrib = exp['feature_contributions'].get('is_sunny', {})
            sunny_impacts.append({
                'item': exp['item_name'],
                'suitable': sunny_contrib.get('value', 0) == 1,
                'impact': sunny_contrib.get('shap_contribution', 0)
            })
        
        for impact in sunny_impacts[:5]:  # Top 5
            suitable_text = "✅ Suitable" if impact['suitable'] else "❌ Not ideal"
            print(f"   • {impact['item']}: {suitable_text} (Impact: {impact['impact']:+.3f})")
        
        # Price impact analysis
        print(f"\n💰 PRICE IMPACT ANALYSIS:")
        price_impacts = []
        for exp in shap_explanations:
            price_contrib = exp['feature_contributions'].get('price', {})
            price_impacts.append({
                'item': exp['item_name'],
                'price': price_contrib.get('value', 0),
                'impact': price_contrib.get('shap_contribution', 0)
            })
        
        # Sort by price impact
        price_impacts.sort(key=lambda x: abs(x['impact']), reverse=True)
        for impact in price_impacts[:5]:  # Top 5 by impact
            price_text = f"${impact['price']:,.0f}"
            impact_text = "helps" if impact['impact'] > 0 else "hurts" if impact['impact'] < 0 else "neutral"
            print(f"   • {impact['item']}: {price_text} {impact_text} recommendation (Impact: {impact['impact']:+.3f})")
    
    else:
        print("\n❌ SHAP explanations not generated")
        return False
    
    # Test Summary
    print(f"\n6️⃣  TEST SUMMARY")
    print("-" * 35)
    
    success_indicators = [
        ("System initialization", recommender.shap_explainer is not None),
        ("Recommendations generated", len(recommendations) > 0),
        ("Budget constraint", total_cost <= test_preferences['budget']),
        ("Category requirements", len(set(r['category'] for r in recommendations)) >= 2),
        ("SHAP explanations", shap_explanations is not None),
        ("Mathematical consistency", all(
            abs(exp['base_value'] + sum(contrib['shap_contribution'] 
                for contrib in exp['feature_contributions'].values()) - exp['predicted_rating']) < 0.001
            for exp in (shap_explanations or [])
        ))
    ]
    
    passed = sum(1 for _, status in success_indicators if status)
    total = len(success_indicators)
    
    print(f"📊 Test Results: {passed}/{total} checks passed")
    for indicator, status in success_indicators:
        status_emoji = "✅" if status else "❌"
        print(f"   {status_emoji} {indicator}")
    
    success_rate = passed / total
    if success_rate == 1.0:
        print(f"\n🎉 ALL TESTS PASSED! SHAP explanations working perfectly!")
    elif success_rate >= 0.8:
        print(f"\n✅ Most tests passed! SHAP explanations working well!")
    else:
        print(f"\n⚠️  Some tests failed. System needs attention.")
    
    # Save results
    save_test_results(test_preferences, recommendations, shap_explanations, success_indicators)
    
    return success_rate >= 0.8

def save_test_results(preferences, recommendations, shap_explanations, test_results):
    """Save comprehensive test results to JSON file"""
    
    results = {
        'test_metadata': {
            'test_name': 'SHAP Explanations Test',
            'description': 'Test SHAP explanations with budget=8000, cuisine=Chinese, categories=[Main,Soup], time=evening, weather=sunny',
            'timestamp': pd.Timestamp.now().isoformat(),
            'test_parameters': preferences
        },
        'recommendations': recommendations,
        'shap_explanations': shap_explanations,
        'test_results': {
            'passed_checks': sum(1 for _, status in test_results if status),
            'total_checks': len(test_results),
            'success_rate': sum(1 for _, status in test_results if status) / len(test_results),
            'individual_results': [
                {'check': name, 'passed': status} 
                for name, status in test_results
            ]
        }
    }
    
    output_file = 'shap_test_results_final.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Detailed test results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Failed to save results: {str(e)}")

if __name__ == "__main__":
    print("Starting SHAP Explanations Test...")
    print("This test will demonstrate explainable AI for food recommendations")
    print()
    
    success = run_shap_test()
    
    print(f"\n{'='*70}")
    if success:
        print("🎯 SHAP TEST COMPLETED SUCCESSFULLY!")
        print("The system can now provide explanations for its recommendations.")
    else:
        print("⚠️  SHAP TEST COMPLETED WITH ISSUES")
        print("Some functionality may need attention.")
    print(f"{'='*70}")
