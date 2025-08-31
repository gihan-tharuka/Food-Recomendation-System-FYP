#!/usr/bin/env python3
"""
Debug script to test SHAP explanations generation and display
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender
import json

def test_shap_explanations():
    """Test SHAP explanations generation"""
    print("🔍 Testing SHAP Explanations Generation...")
    
    try:
        # Initialize recommender
        recommender = FoodRecommender()
        print("✅ Recommender initialized successfully")
        
        # Test preferences
        preferences = {
            'budget': 5000.0,  # Increase budget significantly
            'cuisine': 'Thai',  # Use a cuisine that exists in the menu
            'categories': ['Main', 'Soup'],  # Use categories that exist in the menu
            'category_priority': ['Main', 'Soup'],
            'require_each_category': False,
            'time_of_day': 'evening',
            'weather': 'sunny'
        }
        
        user_id = "alice001"  # Test with a valid user ID from ratings data
        
        print(f"🧪 Generating recommendations for user {user_id}...")
        
        # Generate recommendations
        result = recommender.generate_recommendations(user_id, preferences)
        
        # Check the result structure
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result length: {len(result) if isinstance(result, (list, tuple)) else 'Not a sequence'}")
        
        if isinstance(result, tuple) and len(result) == 3:
            recommendations, total_cost, shap_explanations = result
            
            print(f"✅ Found {len(recommendations)} recommendations")
            print(f"💰 Total cost: ${total_cost}")
            print(f"🧠 SHAP explanations type: {type(shap_explanations)}")
            
            if shap_explanations is not None:
                print(f"🧠 Number of SHAP explanations: {len(shap_explanations)}")
                
                # Print first explanation as example
                if len(shap_explanations) > 0:
                    first_explanation = shap_explanations[0]
                    print(f"\n📝 First explanation structure:")
                    print(json.dumps(first_explanation, indent=2, default=str))
                
                return True, shap_explanations
            else:
                print("❌ SHAP explanations are None")
                return False, None
        else:
            print(f"❌ Unexpected result structure: {result}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing SHAP explanations: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_shap_explainer_initialization():
    """Test if SHAP explainer is properly initialized"""
    print("\n🔧 Testing SHAP Explainer Initialization...")
    
    try:
        recommender = FoodRecommender()
        
        print(f"🧠 SHAP explainer: {recommender.shap_explainer}")
        print(f"🏷️ Feature names: {recommender.feature_names}")
        print(f"🤖 Surrogate model: {recommender.surrogate_model}")
        
        if recommender.shap_explainer is not None:
            print("✅ SHAP explainer initialized successfully")
            return True
        else:
            print("❌ SHAP explainer is None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing SHAP explainer initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting SHAP Explanations Debug Session...")
    
    # Test explainer initialization
    explainer_ok = test_shap_explainer_initialization()
    
    # Test explanations generation
    explanations_ok, explanations = test_shap_explanations()
    
    # Summary
    print(f"\n📊 Debug Summary:")
    print(f"   SHAP Explainer: {'✅ OK' if explainer_ok else '❌ Failed'}")
    print(f"   SHAP Explanations: {'✅ OK' if explanations_ok else '❌ Failed'}")
    
    if explanations_ok and explanations:
        print(f"   Generated {len(explanations)} explanations successfully")
    
    print("🏁 Debug session completed!")
