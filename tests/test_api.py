import requests
import json

try:
    response = requests.get('http://localhost:5000/api/menu-items')
    if response.status_code == 200:
        data = response.json()
        print('API Response Success!')
        if 'items' in data:
            for item in data['items'][:5]:
                print(f"Item {item['item_id']}: {item['item_name']} - Image URL: {item.get('image_url', 'None')}")
    else:
        print(f'API Error: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')
