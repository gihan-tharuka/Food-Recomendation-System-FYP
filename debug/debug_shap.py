#!/usr/bin/env python3
"""
Debug SHAP explanations initialization and test with specific user preferences
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender

def debug_shap_initialization():
    """Debug SHAP initialization process"""
    print("DEBUGGING SHAP INITIALIZATION")
    print("=" * 50)
    
    # Initialize recommender
    recommender = FoodRecommender()
    
    # Check data loading
    print(f"✓ Users loaded: {len(recommender.users)} users")
    print(f"✓ Ratings loaded: {len(recommender.ratings)} ratings")
    print(f"✓ Menu items loaded: {len(recommender.menu)} items")
    
    # Check user-item matrix
    print(f"✓ User-item matrix shape: {recommender.user_item_matrix.shape}")
    print(f"✓ User similarity matrix shape: {recommender.user_similarity.shape}")
    
    # Check SHAP components
    print(f"\nSHAP Components:")
    print(f"- SHAP explainer: {recommender.shap_explainer}")
    print(f"- Feature names: {recommender.feature_names}")
    print(f"- Surrogate model: {getattr(recommender, 'surrogate_model', 'Not found')}")
    
    # Let's manually check the SHAP preparation process
    print(f"\nManual SHAP Preparation Check:")
    
    try:
        features_data = []
        target_data = []
        
        print(f"Processing {len(recommender.ratings)} rating records...")
        
        for i, (_, rating_row) in enumerate(recommender.ratings.iterrows()):
            if i >= 5:  # Just check first 5 for debugging
                break
                
            user_id = rating_row['user_id']
            item_id = rating_row['item_id']
            rating = rating_row['rating']
            
            print(f"  Processing rating {i+1}: user={user_id}, item={item_id}, rating={rating}")
            
            # Get item features
            item_info = recommender.menu[recommender.menu['item_id'] == item_id]
            if item_info.empty:
                print(f"    ⚠️  Item {item_id} not found in menu")
                continue
                
            item_row = item_info.iloc[0]
            print(f"    ✓ Item found: {item_row['item_name']} ({item_row['category']}, {item_row['cuisine']})")
            
            # Check if user is in matrix
            if user_id in recommender.user_item_matrix.index:
                user_index = recommender.user_item_matrix.index.get_loc(user_id)
                user_avg_rating = recommender.user_item_matrix.iloc[user_index].mean()
                user_rating_count = (recommender.user_item_matrix.iloc[user_index] > 0).sum()
                print(f"    ✓ User {user_id}: avg_rating={user_avg_rating:.2f}, rating_count={user_rating_count}")
            else:
                user_avg_rating = 3.0
                user_rating_count = 0
                print(f"    ⚠️  User {user_id} not in matrix, using defaults")
            
            # Create feature vector
            features = [
                float(item_row['price']),
                float(item_row.get('is_morning', 0)),
                float(item_row.get('is_afternoon', 0)),
                float(item_row.get('is_evening', 0)),
                float(item_row.get('is_sunny', 0)),
                float(item_row.get('is_rainy', 0)),
                float(item_row.get('is_cloudy', 0)),
                user_avg_rating,
                user_rating_count,
                1 if item_row['category'] == 'Appetizer' else 0,
                1 if item_row['category'] == 'Main Course' else 0,
                1 if item_row['category'] == 'Dessert' else 0,
                1 if item_row['category'] == 'Beverage' else 0,
                1 if item_row['cuisine'] == 'Italian' else 0,
                1 if item_row['cuisine'] == 'Chinese' else 0,
                1 if item_row['cuisine'] == 'Indian' else 0,
                1 if item_row['cuisine'] == 'Mexican' else 0,
            ]
            
            print(f"    ✓ Feature vector created: {len(features)} features")
            features_data.append(features)
            target_data.append(rating)
        
        print(f"\n✓ Collected {len(features_data)} feature vectors for training")
        
        if len(features_data) > 0:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split
            import shap
            
            X = np.array(features_data)
            y = np.array(target_data)
            
            print(f"✓ Training data shape: X={X.shape}, y={y.shape}")
            
            # Train surrogate model
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            surrogate_model = RandomForestRegressor(n_estimators=100, random_state=42)
            surrogate_model.fit(X_train, y_train)
            
            print(f"✓ Surrogate model trained successfully")
            print(f"  Training score: {surrogate_model.score(X_train, y_train):.3f}")
            print(f"  Test score: {surrogate_model.score(X_test, y_test):.3f}")
            
            # Initialize SHAP explainer
            shap_explainer = shap.TreeExplainer(surrogate_model)
            
            print(f"✓ SHAP explainer created successfully")
            print(f"  Expected value: {shap_explainer.expected_value:.3f}")
            
            return True, surrogate_model, shap_explainer
        else:
            print("✗ No training data collected")
            return False, None, None
            
    except Exception as e:
        print(f"✗ Error in manual SHAP preparation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_shap_with_debug():
    """Test SHAP explanations with debugging"""
    print("\n" + "=" * 60)
    print("TESTING SHAP EXPLANATIONS WITH DEBUG INFO")
    print("=" * 60)
    
    # Debug initialization first
    success, surrogate_model, shap_explainer = debug_shap_initialization()
    
    if not success:
        print("✗ SHAP initialization failed, cannot proceed with test")
        return
    
    # Create a modified recommender with working SHAP
    recommender = FoodRecommender()
    recommender.surrogate_model = surrogate_model
    recommender.shap_explainer = shap_explainer
    
    # Test user and preferences
    user_id = "bob001"
    preferences = {
        'budget': 8000,
        'cuisine': 'Chinese',
        'categories': ['Main', 'Soup'],
        'category_priority': ['Main', 'Side dish'],
        'require_each_category': True,
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    print(f"\nTest Configuration:")
    print(f"User ID: {user_id}")
    print(f"Budget: ${preferences['budget']}")
    print(f"Cuisine: {preferences['cuisine']}")
    print(f"Categories: {preferences['categories']}")
    print(f"Time: {preferences['time_of_day']}")
    print(f"Weather: {preferences['weather']}")
    
    # Generate recommendations
    print(f"\nGenerating recommendations...")
    recommendations, total_cost, shap_explanations = recommender.generate_recommendations(user_id, preferences)
    
    print(f"✓ Generated {len(recommendations)} recommendations")
    print(f"✓ Total cost: ${total_cost:.2f}")
    
    if recommendations:
        print(f"\nRecommended items:")
        for i, item in enumerate(recommendations[:3], 1):  # Show first 3
            print(f"{i}. {item['item_name']} ({item['category']}) - ${item['price']}")
    
    # Test SHAP explanations
    if shap_explanations:
        print(f"\n✓ SHAP explanations generated for {len(shap_explanations)} items")
        
        # Show detailed explanation for first item
        if len(shap_explanations) > 0:
            exp = shap_explanations[0]
            print(f"\nDetailed SHAP explanation for: {exp['item_name']}")
            print(f"Predicted rating: {exp['predicted_rating']:.3f}")
            print(f"Base value: {exp['base_value']:.3f}")
            
            print(f"\nTop contributing features:")
            for i, feature in enumerate(exp['top_contributing_features'][:3], 1):
                name = feature['feature']
                value = feature['value']
                shap_val = feature['shap_contribution']
                impact = feature['impact']
                print(f"  {i}. {name}: {value} → SHAP: {shap_val:+.4f} ({impact})")
                
        print(f"\n✓ SHAP test successful!")
    else:
        print(f"\n✗ SHAP explanations not generated")

if __name__ == "__main__":
    test_shap_with_debug()
