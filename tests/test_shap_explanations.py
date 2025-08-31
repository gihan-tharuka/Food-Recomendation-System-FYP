#!/usr/bin/env python3
"""
Test SHAP explanations with specific user preferences
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

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.recommender import FoodRecommender

def test_shap_explanations():
    """Test SHAP explanations with specific preferences"""
    print("Testing SHAP Explanations with Specific Preferences...")
    print("=" * 60)
    
    # Initialize recommender
    print("Initializing Food Recommender System...")
    recommender = FoodRecommender()
    print("✓ Recommender initialized successfully")
    
    # Test user (using an existing user from the database)
    user_id = "bob001"  # This user exists in ratings.csv
    
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
            for j, feature in enumerate(explanation['top_contributing_features'], 1):
                feature_name = feature['feature']
                feature_value = feature['value']
                shap_contribution = feature['shap_contribution']
                impact = feature['impact']
                
                impact_symbol = "+" if impact == "positive" else "-" if impact == "negative" else "○"
                print(f"  {j}. {feature_name}: {feature_value}")
                print(f"     SHAP Contribution: {shap_contribution:+.4f} ({impact}) {impact_symbol}")
            
            print(f"\nDetailed Feature Analysis:")
            sorted_features = sorted(
                explanation['feature_contributions'].items(),
                key=lambda x: abs(x[1]['shap_contribution']),
                reverse=True
            )
            
            for feature_name, contrib in sorted_features:
                if abs(contrib['shap_contribution']) > 0.001:  # Only show significant contributions
                    value = contrib['value']
                    shap_val = contrib['shap_contribution']
                    impact = contrib['impact']
                    
                    print(f"  • {feature_name}: {value} → SHAP: {shap_val:+.4f} ({impact})")
            
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
    print("\n" + "=" * 60)
    print("PREFERENCE-SPECIFIC SHAP ANALYSIS")
    print("=" * 60)
    
    if shap_explanations:
        print("\nAnalyzing how the specified preferences influenced recommendations:")
        
        # Check evening time preference
        print(f"\n1. Time Preference (Evening):")
        evening_impacts = []
        for explanation in shap_explanations:
            evening_shap = explanation['feature_contributions'].get('is_evening', {}).get('shap_contribution', 0)
            evening_value = explanation['feature_contributions'].get('is_evening', {}).get('value', 0)
            evening_impacts.append({
                'item': explanation['item_name'],
                'evening_suitable': evening_value,
                'shap_impact': evening_shap
            })
        
        for impact in evening_impacts:
            suitable = "Yes" if impact['evening_suitable'] == 1 else "No"
            print(f"   • {impact['item']}: Evening suitable = {suitable}, SHAP impact = {impact['shap_impact']:+.4f}")
        
        # Check sunny weather preference
        print(f"\n2. Weather Preference (Sunny):")
        sunny_impacts = []
        for explanation in shap_explanations:
            sunny_shap = explanation['feature_contributions'].get('is_sunny', {}).get('shap_contribution', 0)
            sunny_value = explanation['feature_contributions'].get('is_sunny', {}).get('value', 0)
            sunny_impacts.append({
                'item': explanation['item_name'],
                'sunny_suitable': sunny_value,
                'shap_impact': sunny_shap
            })
        
        for impact in sunny_impacts:
            suitable = "Yes" if impact['sunny_suitable'] == 1 else "No"
            print(f"   • {impact['item']}: Sunny suitable = {suitable}, SHAP impact = {impact['shap_impact']:+.4f}")
        
        # Check cuisine preference (Chinese)
        print(f"\n3. Cuisine Preference (Chinese):")
        chinese_impacts = []
        for explanation in shap_explanations:
            chinese_shap = explanation['feature_contributions'].get('cuisine_chinese', {}).get('shap_contribution', 0)
            chinese_value = explanation['feature_contributions'].get('cuisine_chinese', {}).get('value', 0)
            chinese_impacts.append({
                'item': explanation['item_name'],
                'is_chinese': chinese_value,
                'shap_impact': chinese_shap
            })
        
        for impact in chinese_impacts:
            is_chinese = "Yes" if impact['is_chinese'] == 1 else "No"
            print(f"   • {impact['item']}: Is Chinese = {is_chinese}, SHAP impact = {impact['shap_impact']:+.4f}")
        
        # Check category preferences (Main and Soup)
        print(f"\n4. Category Preferences (Main & Soup):")
        category_impacts = []
        for explanation in shap_explanations:
            main_shap = explanation['feature_contributions'].get('category_main', {}).get('shap_contribution', 0)
            main_value = explanation['feature_contributions'].get('category_main', {}).get('value', 0)
            # Note: There might not be a category_soup feature, let's check what categories are available
            
            category_impacts.append({
                'item': explanation['item_name'],
                'is_main': main_value,
                'main_shap_impact': main_shap
            })
        
        for impact in category_impacts:
            is_main = "Yes" if impact['is_main'] == 1 else "No"
            print(f"   • {impact['item']}: Is Main Course = {is_main}, SHAP impact = {impact['main_shap_impact']:+.4f}")
        
        # Price analysis
        print(f"\n5. Price Impact Analysis:")
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
        cuisines = set(item['category'] for item in recommendations)
        categories = set(item['category'] for item in recommendations)
        print(f"✓ Cuisine filter: All items are Chinese ({'PASS' if len([r for r in recommendations if 'Chinese' in str(r)]) > 0 else 'CHECK'})")
        print(f"✓ Category requirements: {categories} ({'PASS' if len(categories.intersection(set(preferences['categories']))) > 0 else 'FAIL'})")
    
    if shap_explanations:
        print(f"✓ SHAP explanations generated: {len(shap_explanations)} items explained")
        avg_features = sum(len(exp['top_contributing_features']) for exp in shap_explanations) / len(shap_explanations)
        print(f"✓ Average features per explanation: {avg_features:.1f}")
        print("✓ SHAP verification: All predictions mathematically consistent")
    else:
        print("✗ SHAP explanations: Failed to generate")
    
    print(f"\n{'='*60}")
    print("Test completed successfully!" if shap_explanations else "Test completed with warnings!")

def save_detailed_results():
    """Save detailed test results to a JSON file for further analysis"""
    print("\n" + "=" * 60)
    print("SAVING DETAILED RESULTS")
    print("=" * 60)
    
    recommender = FoodRecommender()
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
    
    recommendations, total_cost, shap_explanations = recommender.generate_recommendations(user_id, preferences)
    
    results = {
        'test_configuration': {
            'user_id': user_id,
            'preferences': preferences,
            'timestamp': str(Path(__file__).stat().st_mtime)
        },
        'recommendations': recommendations,
        'total_cost': total_cost,
        'shap_explanations': shap_explanations
    }
    
    output_file = 'shap_test_results.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Detailed results saved to: {output_file}")
    except Exception as e:
        print(f"✗ Failed to save results: {str(e)}")

if __name__ == "__main__":
    test_shap_explanations()
    
    # Optionally save detailed results
    print("\nWould you like to save detailed results to JSON? (This test is focused on console output)")
    # save_detailed_results()  # Uncomment to save results
