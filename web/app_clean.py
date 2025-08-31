from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
from pathlib import Path
import json
import pandas as pd
import datetime
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import *

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Store session data (in production, use proper session management)
user_sessions = {}

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/train')
def train():
    """Serve the train models page"""
    return render_template('train.html')

@app.route('/predict')
def predict():
    """Serve the predict page"""
    return render_template('predict.html')

@app.route('/recommend')
def recommend():
    """Serve the recommendations page"""
    return render_template('recommend.html')

@app.route('/info')
def info():
    """Serve the system info page"""
    return render_template('info.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/train', methods=['POST'])
def train_models():
    """Train all ML models"""
    try:
        from src.models.trainer import ModelTrainer
        trainer = ModelTrainer()
        trainer.train_all_models()
        return jsonify({'success': True, 'message': 'Models trained successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def generate_predictions():
    """Generate predictions for menu items"""
    try:
        from src.models.predictor import ModelPredictor
        predictor = ModelPredictor()
        results = predictor.predict_and_save()
        return jsonify({
            'success': True, 
            'message': f'Predictions generated for {len(results)} items',
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        model_info = {}
        models = {
            'cuisine': CUISINE_MODEL_PATH,
            'category': CATEGORY_MODEL_PATH,
            'tags': TAGS_MODEL_PATH
        }
        
        for name, path in models.items():
            model_info[name] = {
                'exists': path.exists(),
                'path': str(path),
                'size': path.stat().st_size if path.exists() else 0
            }
        
        return jsonify({'success': True, 'models': model_info})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'message': 'Name and email required'}), 400
        
        # Load existing users
        if USERS_PATH.exists():
            users_df = pd.read_csv(USERS_PATH)
        else:
            users_df = pd.DataFrame(columns=['user_id', 'name', 'email'])
        
        # Generate new user ID
        new_user_id = str(uuid4())
        
        # Add new user
        new_user = pd.DataFrame([{
            'user_id': new_user_id,
            'name': name,
            'email': email
        }])
        
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        
        # Ensure directory exists
        USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        users_df.to_csv(USERS_PATH, index=False)
        
        # Store in session
        user_sessions[new_user_id] = {'name': name, 'email': email}
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': new_user_id,
                'name': name,
                'email': email
            },
            'message': f'User {name} registered successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    """Login existing user"""
    try:
        data = request.json
        user_id = data.get('user_id', '').strip()
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        # Load users
        if not USERS_PATH.exists():
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        users_df = pd.read_csv(USERS_PATH)
        user_row = users_df[users_df['user_id'] == user_id]
        
        if user_row.empty:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = user_row.iloc[0]
        user_sessions[user_id] = {
            'name': user_data['name'],
            'email': user_data['email']
        }
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user_id,
                'name': user_data['name'],
                'email': user_data['email']
            },
            'message': f'Welcome back {user_data["name"]}!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get personalized recommendations using the original recommender logic"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or user_id not in user_sessions:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        # Extract preferences exactly as in recommender.py
        total_budget = float(data.get('budget', 50))
        preferred_cuisine = data.get('cuisine', '').title()
        user_categories = data.get('categories', [])
        category_priority = data.get('category_priority', [])
        require_each_category = data.get('require_each_category', False)
        current_time = data.get('time_of_day', 'morning')
        current_weather = data.get('weather', 'sunny')
        
        # Validate required fields
        if not preferred_cuisine:
            return jsonify({'success': False, 'message': 'Cuisine preference is required'}), 400
        if not user_categories:
            return jsonify({'success': False, 'message': 'At least one category must be selected'}), 400
        
        # Load menu data
        if not LABELED_MENU_PATH.exists():
            return jsonify({'success': False, 'message': 'Menu data not found'}), 500
        
        menu = pd.read_csv(LABELED_MENU_PATH)
        
        # Load ratings
        if RATINGS_PATH.exists():
            ratings_df = pd.read_csv(RATINGS_PATH)
            user_ratings_df = ratings_df[ratings_df['user_id'] == user_id]
            user_ratings = dict(zip(user_ratings_df['item_id'], user_ratings_df['rating']))
        else:
            user_ratings = {}
        
        # Apply the exact recommendation logic from recommender.py
        recommendations, explanations, total_cost = apply_recommendation_logic(
            menu, user_ratings, total_budget, preferred_cuisine, 
            user_categories, category_priority, require_each_category,
            current_time, current_weather
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'explanations': explanations,
            'total_cost': total_cost,
            'preferences': {
                'budget': total_budget,
                'cuisine': preferred_cuisine,
                'categories': user_categories,
                'category_priority': category_priority,
                'require_each_category': require_each_category,
                'time_of_day': current_time,
                'weather': current_weather
            },
            'message': f'Found {len(recommendations)} recommendations within budget of ${total_budget}'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

def apply_recommendation_logic(menu, user_ratings, total_budget, preferred_cuisine, 
                             user_categories, category_priority, require_each_category,
                             current_time, current_weather):
    """Apply the exact recommendation logic from recommender.py"""
    
    # Set up context columns
    time_col = f'is_{current_time}'
    weather_col = f'is_{current_weather}'
    
    # Filter menu based on cuisine and categories
    filtered_menu = menu[
        (menu['cuisine'].str.lower() == preferred_cuisine.lower()) &
        (menu['category'].isin(user_categories))
    ]
    
    if filtered_menu.empty:
        return [], {}, 0.0
    
    # Calculate weights and utilities exactly as in recommender.py
    priority_weights = {cat: len(category_priority) - i for i, cat in enumerate(category_priority)}
    contextual_boost = 1.2
    weather_boost = 1.2
    max_rating = 5.0
    
    items = []
    explanations = {}
    
    for _, row in filtered_menu.iterrows():
        price = row['price']
        category = row['category']
        item_id = row['item_id']
        item_name = row['item_name']
        cuisine = row['cuisine']
        
        # Calculate weights exactly as in recommender.py
        base_weight = priority_weights.get(category, 1)
        context_weight = contextual_boost if row.get(time_col, False) else 1.0
        weather_weight = weather_boost if row.get(weather_col, False) else 1.0
        rating = user_ratings.get(item_id)
        rating_weight = rating / max_rating if rating else 1.0
        
        value = price * base_weight * context_weight * weather_weight * rating_weight
        
        # Build explanation exactly as in recommender.py
        reason = []
        if row['cuisine'].lower() == preferred_cuisine.lower():
            reason.append("✓ matches your preferred cuisine")
        if category in user_categories:
            reason.append(f"✓ fits category: {category}")
        if category in priority_weights:
            reason.append(f"✓ high priority category (weight={base_weight})")
        if row.get(time_col, False):
            reason.append(f"✓ suitable for {current_time}")
        if row.get(weather_col, False):
            reason.append(f"✓ suitable for {current_weather} weather")
        if rating:
            reason.append(f"✓ rated {rating}/5 by you")
        
        explanations[item_id] = '; '.join(reason)
        
        items.append({
            'price': price,
            'value': value,
            'item_id': item_id,
            'item_name': item_name,
            'category': category,
            'cuisine': cuisine
        })
    
    # Apply pre-selection logic if required
    preselected = []
    remaining_items = items.copy()
    remaining_budget = total_budget
    
    if require_each_category:
        for cat in user_categories:
            cat_items = [item for item in items if item['category'] == cat]
            if cat_items:
                cheapest = min(cat_items, key=lambda x: x['price'])
                if cheapest not in preselected:
                    preselected.append(cheapest)
                    remaining_budget -= cheapest['price']
                    remaining_items.remove(cheapest)
    
    # Apply knapsack algorithm exactly as in recommender.py
    selected_items = knapsack_algorithm(remaining_items, remaining_budget)
    
    # Combine final selection
    final_selection = preselected + selected_items
    total_cost = sum(item['price'] for item in final_selection)
    
    return final_selection, explanations, total_cost

def knapsack_algorithm(items, budget):
    """Knapsack algorithm implementation exactly as in recommender.py"""
    if not items or budget <= 0:
        return []
    
    n = len(items)
    dp = [[0] * (int(budget) + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        price = int(items[i-1]['price'])
        value = items[i-1]['value']
        for w in range(int(budget) + 1):
            if price <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-price] + value)
            else:
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    w = int(budget)
    selected = []
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(items[i-1])
            w -= int(items[i-1]['price'])
    
    selected.reverse()
    return selected

@app.route('/api/rate', methods=['POST'])
def rate_item():
    """Rate an item"""
    try:
        data = request.json
        user_id = data.get('user_id')
        item_id = data.get('item_id')
        rating = int(data.get('rating', 0))
        
        if not user_id or user_id not in user_sessions:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        if not item_id or not (1 <= rating <= 5):
            return jsonify({'success': False, 'message': 'Invalid item ID or rating'}), 400
        
        # Load existing ratings
        if RATINGS_PATH.exists():
            ratings_df = pd.read_csv(RATINGS_PATH)
        else:
            ratings_df = pd.DataFrame(columns=['user_id', 'item_id', 'rating', 'date'])
        
        # Add or update rating
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        new_rating = pd.DataFrame([{
            'user_id': user_id,
            'item_id': item_id,
            'rating': rating,
            'date': today
        }])
        
        # Remove existing rating for this user-item pair and add new one
        ratings_df = ratings_df[~((ratings_df['user_id'] == user_id) & (ratings_df['item_id'] == item_id))]
        ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
        
        # Ensure directory exists and save
        RATINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ratings_df.to_csv(RATINGS_PATH, index=False)
        
        return jsonify({
            'success': True,
            'message': 'Rating saved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PRE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    POST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("🍽️ Starting Food Recommendation System Web Server...")
    print(f"📂 Data directory: {DATA_DIR}")
    print(f"🤖 Models directory: {MODELS_DIR}")
    print("🌐 Open your browser and go to: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
