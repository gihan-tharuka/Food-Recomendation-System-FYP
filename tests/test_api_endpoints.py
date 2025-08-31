#!/usr/bin/env python3

import requests
import json

def test_recommendation_api():
    """Test the complete recommendation workflow"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Food Recommendation System API")
    print("=" * 50)
    
    # Test 1: Get cuisines
    print("\n1. Testing /api/cuisines")
    try:
        response = requests.get(f"{base_url}/api/cuisines")
        data = response.json()
        if data['success']:
            print(f"✓ Found {len(data['cuisines'])} cuisines")
            print(f"   Cuisines: {', '.join(data['cuisines'][:5])}...")
        else:
            print(f"✗ Failed: {data['message']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Get categories for Thai cuisine
    print("\n2. Testing /api/categories?cuisine=Thai")
    try:
        response = requests.get(f"{base_url}/api/categories?cuisine=Thai")
        data = response.json()
        if data['success']:
            print(f"✓ Found {len(data['categories'])} categories for Thai cuisine")
            print(f"   Categories: {', '.join(data['categories'])}")
        else:
            print(f"✗ Failed: {data['message']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Test recommendation API (requires user session simulation)
    print("\n3. Testing /api/recommend (simulated)")
    test_preferences = {
        'user_id': 'bob001',
        'budget': 3000,
        'cuisine': 'Thai',
        'categories': ['Soup', 'Main'],
        'category_priority': ['Main', 'Soup'],
        'require_each_category': True,
        'time_of_day': 'evening',
        'weather': 'sunny'
    }
    
    try:
        # Note: This will fail without proper session but tests the endpoint
        response = requests.post(f"{base_url}/api/recommend", 
                               json=test_preferences,
                               headers={'Content-Type': 'application/json'})
        data = response.json()
        
        if response.status_code == 401:
            print("✓ API correctly requires authentication")
        elif data.get('success'):
            print(f"✓ Generated {len(data['recommendations'])} recommendations")
            print(f"   Total cost: ${data['total_cost']}")
        else:
            print(f"✗ Failed: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✓ API tests completed!")

if __name__ == "__main__":
    test_recommendation_api()
