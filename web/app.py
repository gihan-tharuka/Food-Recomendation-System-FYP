from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sys
import time
from pathlib import Path
import json
import pandas as pd
import datetime
from uuid import uuid4
from werkzeug.utils import secure_filename
from PIL import Image

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import *

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# File upload configuration
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

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

@app.route('/login')
def login():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Serve the registration page"""
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Serve the customer dashboard page"""
    return render_template('customer-dashboard.html')

@app.route('/staff-dashboard')
def staff_dashboard():
    """Serve the staff dashboard page"""
    return render_template('staff-dashboard.html')

@app.route('/manage-users')
def manage_users():
    """Serve the user management page (staff only)"""
    return render_template('manage-users.html')

@app.route('/manage-menu')
def manage_menu():
    """Serve the menu management page (staff only)"""
    return render_template('manage-menu.html')

@app.route('/menu')
def menu():
    """Serve the customer menu page"""
    return render_template('menu.html')

@app.route('/about')
def about():
    """Serve the about page"""
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    """Serve the gallery page"""
    return render_template('gallery.html')

@app.route('/contact')
def contact():
    """Serve the contact page"""
    return render_template('contact.html')

@app.route('/manage-ratings')
def manage_ratings():
    """Serve the ratings management page (staff only)"""
    return render_template('manage-ratings.html')

@app.route('/manage-orders')
def manage_orders():
    """Serve the orders management page (staff only)"""
    return render_template('manage-orders.html')

@app.route('/receipt')
def receipt():
    """Serve the order receipt page"""
    return render_template('receipt.html')

@app.route('/my-ratings')
def my_ratings():
    """Serve the user's personal ratings page (customers)"""
    return render_template('my-ratings.html')

@app.route('/account')
def account():
    """Serve the account management page"""
    return render_template('account.html')

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
        results = trainer.train_all_models()
        return jsonify({
            'success': True, 
            'message': 'Models trained successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def generate_predictions():
    """Generate predictions for menu items"""
    try:
        from src.models.predictor import ModelPredictor
        from config.settings import PRE_DATA_DIR
        import glob
        
        # Find the most recent CSV file in PRE_DATA_DIR
        csv_files = list(PRE_DATA_DIR.glob("*.csv"))
        
        if not csv_files:
            return jsonify({
                'success': False, 
                'message': 'No CSV files found in data/Pre directory. Please upload a CSV file first.'
            }), 400
        
        # Sort by modification time and get the most recent file
        most_recent_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        input_filename = most_recent_file.name
        
        predictor = ModelPredictor()
        results = predictor.predict_and_save(input_filename=input_filename)
        
        return jsonify({
            'success': True, 
            'message': f'Predictions generated for {len(results)} items using {input_filename}',
            'count': len(results),
            'input_file': input_filename
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/import-predictions', methods=['POST'])
def import_predictions_to_database():
    """Import predicted data from CSV to MySQL database"""
    try:
        from src.models.database_models import MenuModel
        from config.settings import POST_DATA_DIR
        
        # Path to the predicted CSV file
        predicted_csv_path = POST_DATA_DIR / "Spicia-menu-predicted.csv"
        
        if not predicted_csv_path.exists():
            return jsonify({
                'success': False, 
                'message': 'Predicted data file not found. Please generate predictions first.'
            }), 400
        
        # Import the data
        count = MenuModel.import_predicted_data(str(predicted_csv_path))
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {count} menu items to database',
            'count': count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Upload CSV file to data/Pre directory for predictions"""
    try:
        # Check if file is present in request
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['csv_file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Check file extension
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'message': 'Only CSV files are allowed'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Create timestamp-based filename to avoid conflicts
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        
        # Define the target directory (data/Pre)
        from config.settings import PRE_DATA_DIR
        target_path = PRE_DATA_DIR / unique_filename
        
        # Save the file
        file.save(str(target_path))
        
        # Validate CSV structure
        try:
            df = pd.read_csv(target_path)
            row_count = len(df)
            
            # Check required columns
            required_columns = ['item_name', 'price']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Remove the uploaded file if validation fails
                os.remove(target_path)
                return jsonify({
                    'success': False, 
                    'message': f'CSV missing required columns: {", ".join(missing_columns)}. Required: item_name, price'
                }), 400
            
            return jsonify({
                'success': True,
                'message': f'CSV file uploaded successfully',
                'filename': unique_filename,
                'row_count': row_count,
                'columns': list(df.columns)
            })
            
        except Exception as csv_error:
            # Remove the uploaded file if validation fails
            if os.path.exists(target_path):
                os.remove(target_path)
            return jsonify({
                'success': False,
                'message': f'Invalid CSV format: {str(csv_error)}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/current-data-source', methods=['GET'])
def get_current_data_source():
    """Get information about the current data source file"""
    try:
        from config.settings import PRE_DATA_DIR
        
        # Find the most recent CSV file in PRE_DATA_DIR
        csv_files = list(PRE_DATA_DIR.glob("*.csv"))
        
        if not csv_files:
            return jsonify({
                'success': False,
                'message': 'No CSV files found in data/Pre directory'
            }), 404
        
        # Sort by modification time and get the most recent file
        most_recent_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        
        # Get file info
        df = pd.read_csv(most_recent_file)
        file_info = {
            'filename': most_recent_file.name,
            'full_path': f"data/Pre/{most_recent_file.name}",
            'row_count': len(df),
            'columns': list(df.columns),
            'file_size': most_recent_file.stat().st_size,
            'modified_time': most_recent_file.stat().st_mtime
        }
        
        return jsonify({
            'success': True,
            'data': file_info
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
    """Register a new user with password"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'customer').strip()  # Default to customer
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Name, email and password are required'}), 400
        
        # Validate role
        if role not in ['customer', 'staff']:
            role = 'customer'  # Default to customer for security
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        if USE_DATABASE:
            try:
                from src.models.database_models import UserModel
                user_data = UserModel.create_user(name, email, password, role)
                
                # Store in session
                user_sessions[user_data['user_id']] = {
                    'name': user_data['name'], 
                    'email': user_data['email'],
                    'role': user_data['role']
                }
                
                return jsonify({
                    'success': True,
                    'user': user_data,
                    'message': f'User {name} registered successfully!'
                })
                
            except ValueError as e:
                return jsonify({'success': False, 'message': str(e)}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'}), 500
        else:
            # CSV fallback (simplified - no password support in CSV mode)
            return jsonify({'success': False, 'message': 'Password authentication requires database mode'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
        
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
    """Login user with email and password"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        if USE_DATABASE:
            try:
                from src.models.database_models import UserModel
                user_data = UserModel.authenticate_user(email, password)
                
                if not user_data:
                    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
                
                # Store in session
                user_sessions[user_data['user_id']] = {
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'role': user_data['role']
                }
                
                return jsonify({
                    'success': True,
                    'user': user_data,
                    'message': f'Welcome back {user_data["name"]}!'
                })
                
            except Exception as e:
                return jsonify({'success': False, 'message': f'Login failed: {str(e)}'}), 500
        else:
            # CSV fallback (no password support)
            return jsonify({'success': False, 'message': 'Password authentication requires database mode'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get personalized recommendations using the FoodRecommender class"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or user_id not in user_sessions:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        # Extract preferences
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
        
        # Use the FoodRecommender class
        from src.models.recommender import FoodRecommender
        recommender = FoodRecommender()
        
        preferences = {
            'budget': total_budget,
            'cuisine': preferred_cuisine,
            'categories': user_categories,
            'category_priority': category_priority,
            'require_each_category': require_each_category,
            'time_of_day': current_time,
            'weather': current_weather
        }
        
        recommendations, total_cost, explanations = recommender.generate_recommendations(user_id, preferences)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'explanations': explanations,
            'total_cost': total_cost,
            'preferences': preferences,
            'message': f'Found {len(recommendations)} recommendations within budget of ${total_budget}'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rate', methods=['POST'])
def rate_item():
    """Rate an item using the FoodRecommender class"""
    try:
        data = request.json
        user_id = data.get('user_id')
        item_id = data.get('item_id')
        rating = int(data.get('rating', 0))
        
        if not user_id or user_id not in user_sessions:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        if not item_id or not (1 <= rating <= 5):
            return jsonify({'success': False, 'message': 'Invalid item ID or rating'}), 400
        
        # Use the FoodRecommender class to save rating
        from src.models.recommender import FoodRecommender
        recommender = FoodRecommender()
        
        success = recommender.save_rating(user_id, item_id, rating)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Rating saved successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save rating'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user-ratings', methods=['GET'])
def get_user_ratings_legacy():
    """Get all ratings for a specific user (legacy endpoint)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id or user_id not in user_sessions:
            return jsonify({'success': False, 'message': 'Please login first'}), 401
        
        # Use the FoodRecommender class to get user ratings
        from src.models.recommender import FoodRecommender
        recommender = FoodRecommender()
        
        ratings = recommender.get_user_ratings(user_id)
        
        return jsonify({
            'success': True,
            'ratings': ratings
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cuisines', methods=['GET'])
def get_cuisines():
    """Get available cuisines from the menu"""
    try:
        from src.models.recommender import FoodRecommender
        recommender = FoodRecommender()
        cuisines = recommender.get_available_cuisines()
        
        return jsonify({
            'success': True,
            'cuisines': sorted(cuisines)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories, optionally filtered by cuisine with international supplements"""
    try:
        cuisine = request.args.get('cuisine')
        
        from src.models.recommender import FoodRecommender
        recommender = FoodRecommender()
        
        if cuisine:
            # Get categories with supplements analysis
            analysis = recommender.get_categories_with_supplements(cuisine)
            
            return jsonify({
                'success': True,
                'categories': analysis['total_categories'],
                'native_categories': analysis['native_categories'],
                'supplemented_categories': analysis['supplemented_categories'],
                'warning_needed': analysis['warning_needed'],
                'cuisine': cuisine
            })
        else:
            # Return all categories if no cuisine specified
            categories = recommender.get_available_categories()
            return jsonify({
                'success': True,
                'categories': sorted(categories),
                'native_categories': sorted(categories),
                'supplemented_categories': [],
                'warning_needed': False,
                'cuisine': None
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'authenticated': False}), 200
        
        if user_id in user_sessions:
            return jsonify({
                'authenticated': True,
                'user': {
                    'user_id': user_id,
                    'name': user_sessions[user_id]['name'],
                    'email': user_sessions[user_id]['email'],
                    'role': user_sessions[user_id].get('role', 'customer')
                }
            })
        else:
            return jsonify({'authenticated': False}), 200
            
    except Exception as e:
        return jsonify({'authenticated': False, 'error': str(e)}), 500

@app.route('/api/system-stats', methods=['GET'])
def get_system_stats():
    """Get system statistics for staff dashboard"""
    try:
        if USE_DATABASE:
            from src.models.database_models import UserModel, RatingModel
            
            # Get user count
            users = UserModel.get_all_users()
            total_users = len(users)
            
            # Get ratings data
            ratings_df = RatingModel.get_all_ratings_dataframe()
            total_ratings = len(ratings_df)
            avg_rating = ratings_df['rating'].mean() if not ratings_df.empty else 0
            
        else:
            # CSV fallback
            try:
                users_df = pd.read_csv(USERS_CSV_PATH) if USERS_CSV_PATH.exists() else pd.DataFrame()
                ratings_df = pd.read_csv(RATINGS_CSV_PATH) if RATINGS_CSV_PATH.exists() else pd.DataFrame()
                
                total_users = len(users_df)
                total_ratings = len(ratings_df)
                avg_rating = ratings_df['rating'].mean() if not ratings_df.empty else 0
            except:
                total_users = total_ratings = avg_rating = 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_ratings': total_ratings,
                'avg_rating': float(avg_rating),
                'system_status': 'healthy'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get system stats: {str(e)}'
        }), 500

# =============================================================================
# USER MANAGEMENT API ENDPOINTS
# =============================================================================

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get all users for management"""
    try:
        if USE_DATABASE:
            from src.models.database_models import UserModel
            users = UserModel.get_all_users()
            
            # Convert to list of dicts with safe date handling
            user_list = []
            for user in users:
                user_dict = {
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': user.get('role', 'customer'),
                    'created_at': user.get('created_at', '').isoformat() if hasattr(user.get('created_at', ''), 'isoformat') else str(user.get('created_at', ''))
                }
                user_list.append(user_dict)
            
            return jsonify({'success': True, 'users': user_list}), 200
        else:
            # CSV fallback
            if USERS_CSV_PATH.exists():
                users_df = pd.read_csv(USERS_CSV_PATH)
                users_list = users_df.to_dict('records')
                return jsonify({'success': True, 'users': users_list}), 200
            else:
                return jsonify({'success': True, 'users': []}), 200
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'customer')
        
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'Name, email, and password are required'}), 400
            
        if USE_DATABASE:
            from src.models.database_models import UserModel
            
            # Check if user already exists
            existing_user = UserModel.get_user_by_email(email)
            if existing_user:
                return jsonify({'success': False, 'message': 'User with this email already exists'}), 400
            
            # Create new user
            user = UserModel.create_user(name, email, password, role)
            if user:
                return jsonify({'success': True, 'message': 'User created successfully', 'user_id': user['user_id']}), 201
            else:
                return jsonify({'success': False, 'message': 'Failed to create user'}), 500
        else:
            # CSV fallback - basic implementation
            import uuid
            import bcrypt
            from datetime import datetime
            
            user_id = str(uuid.uuid4())
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            new_user = {
                'user_id': user_id,
                'name': name,
                'email': email,
                'password': hashed_password,
                'role': role,
                'created_at': datetime.now().isoformat()
            }
            
            # Add to CSV
            if USERS_CSV_PATH.exists():
                users_df = pd.read_csv(USERS_CSV_PATH)
            else:
                users_df = pd.DataFrame()
            
            users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
            users_df.to_csv(USERS_CSV_PATH, index=False)
            
            return jsonify({'success': True, 'message': 'User created successfully', 'user_id': user_id}), 201
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')  # Optional for updates
        role = data.get('role', 'customer')
        
        if not all([name, email]):
            return jsonify({'success': False, 'message': 'Name and email are required'}), 400
            
        if USE_DATABASE:
            from src.models.database_models import UserModel
            
            # Check if user exists
            existing_user = UserModel.get_user_by_id(user_id)
            if not existing_user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Check if email is taken by another user
            email_user = UserModel.get_user_by_email(email)
            if email_user and email_user['user_id'] != user_id:
                return jsonify({'success': False, 'message': 'Email already taken by another user'}), 400
            
            # Update user
            success = UserModel.update_user(user_id, name, email, password, role)
            if success:
                return jsonify({'success': True, 'message': 'User updated successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to update user'}), 500
        else:
            # CSV fallback
            if not USERS_CSV_PATH.exists():
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            users_df = pd.read_csv(USERS_CSV_PATH)
            user_index = users_df[users_df['user_id'] == user_id].index
            
            if len(user_index) == 0:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Update user data
            users_df.loc[user_index[0], 'name'] = name
            users_df.loc[user_index[0], 'email'] = email
            users_df.loc[user_index[0], 'role'] = role
            
            if password:
                import bcrypt
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                users_df.loc[user_index[0], 'password'] = hashed_password
            
            users_df.to_csv(USERS_CSV_PATH, index=False)
            return jsonify({'success': True, 'message': 'User updated successfully'}), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and their ratings"""
    try:
        if USE_DATABASE:
            from src.models.database_models import UserModel, RatingModel
            
            # Check if user exists
            existing_user = UserModel.get_user_by_id(user_id)
            if not existing_user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Delete user's ratings first
            RatingModel.delete_user_ratings(user_id)
            
            # Delete user
            success = UserModel.delete_user(user_id)
            if success:
                return jsonify({'success': True, 'message': 'User and associated ratings deleted successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to delete user'}), 500
        else:
            # CSV fallback
            if not USERS_CSV_PATH.exists():
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            users_df = pd.read_csv(USERS_CSV_PATH)
            user_exists = user_id in users_df['user_id'].values
            
            if not user_exists:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Remove user from CSV
            users_df = users_df[users_df['user_id'] != user_id]
            users_df.to_csv(USERS_CSV_PATH, index=False)
            
            # Remove user's ratings
            if RATINGS_CSV_PATH.exists():
                ratings_df = pd.read_csv(RATINGS_CSV_PATH)
                ratings_df = ratings_df[ratings_df['user_id'] != user_id]
                ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
            
            return jsonify({'success': True, 'message': 'User and associated ratings deleted successfully'}), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# RATING MANAGEMENT API ENDPOINTS
# =============================================================================

@app.route('/api/ratings', methods=['GET'])
def get_all_ratings():
    """Get all ratings for management"""
    try:
        if USE_DATABASE:
            from src.models.database_models import RatingModel
            ratings_df = RatingModel.get_all_ratings_dataframe()
            
            if not ratings_df.empty:
                # Convert to list of dicts with proper date handling
                ratings_list = []
                for _, row in ratings_df.iterrows():
                    rating_dict = {
                        'user_id': row['user_id'],
                        'food_id': int(row['item_id']),  # Map item_id to food_id for frontend
                        'rating': float(row['rating']),  # Convert Decimal to float
                        'created_at': row.get('created_at', '').isoformat() if hasattr(row.get('created_at', ''), 'isoformat') else str(row.get('created_at', ''))
                    }
                    ratings_list.append(rating_dict)
                
                return jsonify({'success': True, 'ratings': ratings_list}), 200
            else:
                return jsonify({'success': True, 'ratings': []}), 200
        else:
            # CSV fallback
            if RATINGS_CSV_PATH.exists():
                ratings_df = pd.read_csv(RATINGS_CSV_PATH)
                ratings_list = ratings_df.to_dict('records')
                return jsonify({'success': True, 'ratings': ratings_list}), 200
            else:
                return jsonify({'success': True, 'ratings': []}), 200
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ratings', methods=['POST'])
def create_rating():
    """Create a new rating"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        food_id = data.get('food_id')
        rating = data.get('rating')
        
        if not all([user_id, food_id is not None, rating is not None]):
            return jsonify({'success': False, 'message': 'User ID, food ID, and rating are required'}), 400
        
        if not (1 <= rating <= 5):
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
            
        if USE_DATABASE:
            from src.models.database_models import RatingModel, UserModel
            
            # Check if user exists
            user = UserModel.get_user_by_id(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Create or update rating
            success = RatingModel.add_rating(user_id, food_id, rating)
            if success:
                return jsonify({'success': True, 'message': 'Rating created successfully'}), 201
            else:
                return jsonify({'success': False, 'message': 'Failed to create rating'}), 500
        else:
            # CSV fallback
            from datetime import datetime
            
            new_rating = {
                'user_id': user_id,
                'food_id': food_id,
                'rating': rating,
                'created_at': datetime.now().isoformat()
            }
            
            if RATINGS_CSV_PATH.exists():
                ratings_df = pd.read_csv(RATINGS_CSV_PATH)
                # Remove existing rating for this user-food pair
                ratings_df = ratings_df[~((ratings_df['user_id'] == user_id) & (ratings_df['food_id'] == food_id))]
            else:
                ratings_df = pd.DataFrame()
            
            ratings_df = pd.concat([ratings_df, pd.DataFrame([new_rating])], ignore_index=True)
            ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
            
            return jsonify({'success': True, 'message': 'Rating created successfully'}), 201
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ratings/<user_id>/<int:food_id>', methods=['PUT'])
def update_rating(user_id, food_id):
    """Update an existing rating"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        
        if rating is None:
            return jsonify({'success': False, 'message': 'Rating is required'}), 400
        
        if not (1 <= rating <= 5):
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
            
        if USE_DATABASE:
            from src.models.database_models import RatingModel
            
            # Update rating
            success = RatingModel.add_rating(user_id, food_id, rating)  # add_rating handles updates too
            if success:
                return jsonify({'success': True, 'message': 'Rating updated successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to update rating'}), 500
        else:
            # CSV fallback
            if not RATINGS_CSV_PATH.exists():
                return jsonify({'success': False, 'message': 'Rating not found'}), 404
            
            ratings_df = pd.read_csv(RATINGS_CSV_PATH)
            rating_index = ratings_df[(ratings_df['user_id'] == user_id) & (ratings_df['food_id'] == food_id)].index
            
            if len(rating_index) == 0:
                return jsonify({'success': False, 'message': 'Rating not found'}), 404
            
            ratings_df.loc[rating_index[0], 'rating'] = rating
            ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
            
            return jsonify({'success': True, 'message': 'Rating updated successfully'}), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ratings/<user_id>/<int:food_id>', methods=['DELETE'])
def delete_rating(user_id, food_id):
    """Delete a specific rating"""
    try:
        if USE_DATABASE:
            from src.models.database_models import RatingModel
            
            # Delete rating
            success = RatingModel.delete_rating(user_id, food_id)
            if success:
                return jsonify({'success': True, 'message': 'Rating deleted successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Rating not found or failed to delete'}), 404
        else:
            # CSV fallback
            if not RATINGS_CSV_PATH.exists():
                return jsonify({'success': False, 'message': 'Rating not found'}), 404
            
            ratings_df = pd.read_csv(RATINGS_CSV_PATH)
            initial_length = len(ratings_df)
            
            ratings_df = ratings_df[~((ratings_df['user_id'] == user_id) & (ratings_df['food_id'] == food_id))]
            
            if len(ratings_df) == initial_length:
                return jsonify({'success': False, 'message': 'Rating not found'}), 404
            
            ratings_df.to_csv(RATINGS_CSV_PATH, index=False)
            return jsonify({'success': True, 'message': 'Rating deleted successfully'}), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ratings/bulk', methods=['POST'])
def submit_bulk_ratings():
    """Submit multiple ratings at once"""
    try:
        data = request.get_json()
        ratings_data = data.get('ratings', [])
        
        if not ratings_data:
            return jsonify({'success': False, 'message': 'No ratings provided'}), 400
        
        if USE_DATABASE:
            from src.models.database_models import RatingModel
            
            success_count = 0
            errors = []
            
            for rating in ratings_data:
                try:
                    # Validate rating data
                    required_fields = ['user_id', 'item_id', 'rating']
                    for field in required_fields:
                        if field not in rating:
                            errors.append(f'Missing field {field} in rating')
                            continue
                    
                    # Check if rating already exists
                    existing_rating = RatingModel.get_user_item_rating(rating['user_id'], rating['item_id'])
                    
                    if existing_rating:
                        # Update existing rating
                        success = RatingModel.update_rating(
                            rating['user_id'], 
                            rating['item_id'], 
                            rating['rating'],
                            rating.get('comment')
                        )
                    else:
                        # Create new rating
                        success = RatingModel.create_rating(
                            rating['user_id'],
                            rating['item_id'],
                            rating['rating'],
                            rating.get('comment')
                        )
                    
                    if success:
                        success_count += 1
                    else:
                        errors.append(f'Failed to save rating for item {rating["item_id"]}')
                        
                except Exception as e:
                    errors.append(f'Error processing rating for item {rating.get("item_id", "unknown")}: {str(e)}')
            
            if success_count > 0:
                message = f'Successfully submitted {success_count} rating(s)'
                if errors:
                    message += f', but encountered {len(errors)} error(s)'
                return jsonify({
                    'success': True, 
                    'message': message,
                    'submitted': success_count,
                    'errors': errors
                }), 200
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Failed to submit any ratings',
                    'errors': errors
                }), 400
        else:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# CUSTOMER-SPECIFIC API ENDPOINTS
# =============================================================================

@app.route('/api/user-ratings/<user_id>', methods=['GET'])
def get_user_ratings(user_id):
    """Get ratings for a specific user"""
    try:
        if USE_DATABASE:
            from src.models.database_models import RatingModel
            ratings = RatingModel.get_user_ratings(user_id)
            
            # Convert to proper format for frontend
            ratings_list = []
            for rating in ratings:
                rating_dict = {
                    'user_id': rating['user_id'],
                    'food_id': rating['item_id'],  # Use item_id from database
                    'rating': int(rating['rating']),
                    'created_at': rating.get('created_at', '').isoformat() if hasattr(rating.get('created_at', ''), 'isoformat') else str(rating.get('created_at', '')),
                    'comment': rating.get('comment', ''),
                    # Add food details
                    'item_name': rating.get('item_name', f'Food ID {rating["item_id"]}'),
                    'cuisine': rating.get('cuisine', ''),
                    'category': rating.get('category', ''),
                    'price': float(rating['price']) if rating.get('price') else None
                }
                ratings_list.append(rating_dict)
            
            return jsonify({'success': True, 'ratings': ratings_list}), 200
        else:
            # CSV fallback
            if RATINGS_CSV_PATH.exists():
                ratings_df = pd.read_csv(RATINGS_CSV_PATH)
                user_ratings = ratings_df[ratings_df['user_id'] == user_id]
                ratings_list = user_ratings.to_dict('records')
                return jsonify({'success': True, 'ratings': ratings_list}), 200
            else:
                return jsonify({'success': True, 'ratings': []}), 200
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/verify-password', methods=['POST'])
def verify_password():
    """Verify user's current password"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        
        if not all([user_id, password]):
            return jsonify({'success': False, 'message': 'User ID and password are required'}), 400
            
        if USE_DATABASE:
            from src.models.database_models import UserModel
            
            # Get user
            user = UserModel.get_user_by_id(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Verify password
            import bcrypt
            is_valid = bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
            
            return jsonify({'success': is_valid}), 200
        else:
            # CSV fallback
            if not USERS_CSV_PATH.exists():
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            users_df = pd.read_csv(USERS_CSV_PATH)
            user_row = users_df[users_df['user_id'] == user_id]
            
            if len(user_row) == 0:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Verify password
            import bcrypt
            stored_password = user_row.iloc[0]['password']
            is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
            
            return jsonify({'success': is_valid}), 200
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# MENU MANAGEMENT API ENDPOINTS
# =============================================================================

@app.route('/api/menu-items', methods=['GET'])
def get_menu_items():
    """Get all menu items"""
    try:
        if USE_DATABASE:
            from src.models.database_models import MenuModel
            menu_df = MenuModel.get_all_menu_items()
            
            if menu_df.empty:
                return jsonify({'success': True, 'items': []}), 200
            
            # Convert DataFrame to list of dictionaries
            items = []
            for _, row in menu_df.iterrows():
                item = {
                    'item_id': int(row['item_id']),
                    'item_name': row['item_name'],
                    'price': float(row['price']),
                    'cuisine': row.get('cuisine', ''),
                    'category': row.get('category', ''),
                    'image_url': row.get('image_url', ''),
                    'is_morning': bool(row.get('is_morning', False)),
                    'is_afternoon': bool(row.get('is_afternoon', False)),
                    'is_evening': bool(row.get('is_evening', False)),
                    'is_sunny': bool(row.get('is_sunny', False)),
                    'is_rainy': bool(row.get('is_rainy', False))
                }
                items.append(item)
            
            return jsonify({'success': True, 'items': items}), 200
        else:
            # CSV fallback
            if MENU_DATA_PREDICTED_PATH.exists():
                menu_df = pd.read_csv(MENU_DATA_PREDICTED_PATH)
                items = menu_df.to_dict('records')
                return jsonify({'success': True, 'items': items}), 200
            else:
                return jsonify({'success': True, 'items': []}), 200
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/menu-items', methods=['POST'])
def add_menu_item():
    """Add a new menu item with optional image"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
            # Convert boolean strings to actual booleans
            for key in ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']:
                if key in data:
                    data[key] = data[key].lower() == 'true'
        
        # Validate required fields
        required_fields = ['item_name', 'price', 'cuisine', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        image_url = None
        
        # Handle image upload if present
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Generate unique filename
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    
                    # Save the file
                    file.save(file_path)
                    
                    # Validate it's actually an image
                    if validate_image(file_path):
                        image_url = f"/static/uploads/{unique_filename}"
                    else:
                        os.remove(file_path)  # Remove invalid file
                        return jsonify({'success': False, 'message': 'Invalid image file'}), 400
                else:
                    return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        if USE_DATABASE:
            from src.models.database_models import MenuModel
            
            # Get the next available item_id
            menu_df = MenuModel.get_all_menu_items()
            next_id = int(menu_df['item_id'].max() + 1) if not menu_df.empty else 1
            
            # Add the menu item with image
            success = MenuModel.add_menu_item(
                item_id=next_id,
                item_name=data['item_name'],
                price=float(data['price']),
                cuisine=data['cuisine'],
                category=data['category'],
                image_url=image_url,
                is_morning=data.get('is_morning', False),
                is_afternoon=data.get('is_afternoon', False),
                is_evening=data.get('is_evening', False),
                is_sunny=data.get('is_sunny', False),
                is_rainy=data.get('is_rainy', False)
            )
            
            if success:
                return jsonify({'success': True, 'message': 'Menu item added successfully', 'item_id': next_id}), 201
            else:
                return jsonify({'success': False, 'message': 'Failed to add menu item'}), 500
        else:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/menu-items/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    """Update an existing menu item with optional image upload"""
    try:
        # Handle both JSON and multipart form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.json or {}
        
        # Validate required fields
        required_fields = ['item_name', 'price', 'cuisine', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        if USE_DATABASE:
            from src.models.database_models import MenuModel
            
            # Get existing menu item to preserve image if no new one is uploaded
            existing_item = MenuModel.get_menu_item_by_id(item_id)
            if not existing_item:
                return jsonify({'success': False, 'message': 'Menu item not found'}), 404
            
            # Handle image upload if present
            image_url = existing_item.get('image_url')  # Keep existing image by default
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        # Validate image
                        if validate_image(file):
                            filename = secure_filename(file.filename)
                            # Create unique filename to avoid conflicts
                            timestamp = str(int(time.time()))
                            filename = f"{timestamp}_{filename}"
                            
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            file.save(file_path)
                            image_url = f"/static/uploads/{filename}"
                            
                            # Optionally delete old image file
                            if existing_item.get('image_url') and existing_item['image_url'].startswith('/static/uploads/'):
                                old_file_path = os.path.join(app.static_folder, 'uploads', os.path.basename(existing_item['image_url']))
                                try:
                                    if os.path.exists(old_file_path):
                                        os.remove(old_file_path)
                                except Exception as e:
                                    print(f"Warning: Could not delete old image file: {e}")
                        else:
                            return jsonify({'success': False, 'message': 'Invalid image file'}), 400
                    else:
                        return jsonify({'success': False, 'message': 'Invalid file type. Please upload an image file.'}), 400
            
            # Convert checkbox values to boolean
            bool_fields = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
            tags = {}
            for field in bool_fields:
                tags[field] = data.get(field) in ['true', 'True', '1', 'on', True]
            
            # Update the menu item
            success = MenuModel.add_menu_item(  # add_menu_item handles both insert and update
                item_id=item_id,
                item_name=data['item_name'],
                price=float(data['price']),
                cuisine=data['cuisine'],
                category=data['category'],
                image_url=image_url,  # Use new image or preserve existing
                **tags
            )
            
            if success:
                return jsonify({'success': True, 'message': 'Menu item updated successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to update menu item'}), 500
        else:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/menu-items/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Delete a menu item"""
    try:
        if USE_DATABASE:
            from src.models.database_models import MenuModel
            
            success = MenuModel.delete_menu_item(item_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Menu item deleted successfully'}), 200
            else:
                return jsonify({'success': False, 'message': 'Menu item not found'}), 404
        else:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Cart and Order Routes
@app.route('/cart')
def cart():
    """Serve the cart page"""
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    """Serve the checkout page"""
    return render_template('checkout.html')

@app.route('/my-orders')
def my_orders():
    """Serve the my orders page"""
    return render_template('my-orders.html')

# Order API Endpoints
@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'customer_name', 'customer_email', 'cart_items', 'total_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Create order
        order_id = OrderModel.create_order(
            user_id=data['user_id'],
            customer_name=data['customer_name'],
            customer_email=data['customer_email'],
            cart_items=data['cart_items'],
            total_amount=data['total_amount'],
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes', '')
        )
        
        return jsonify({
            'success': True, 
            'message': 'Order created successfully',
            'order_id': order_id
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        order_df = OrderModel.get_order_by_id(order_id)
        
        if order_df.empty:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Convert to list of dictionaries
        order_data = order_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'order': order_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/user/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Get orders for a specific user"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        limit = request.args.get('limit', 20, type=int)
        orders_df = OrderModel.get_user_orders(user_id, limit)
        
        if orders_df.empty:
            return jsonify({
                'success': True,
                'orders': [],
                'message': 'No orders found'
            }), 200
        
        # Convert to list of dictionaries
        orders_data = orders_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'orders': orders_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        success = OrderModel.update_order_status(order_id, 'cancelled')
        
        if success:
            return jsonify({'success': True, 'message': 'Order cancelled successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        data = request.get_json()
        status = data.get('status')
        
        if not status:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        success = OrderModel.update_order_status(order_id, status)
        
        if success:
            return jsonify({'success': True, 'message': 'Order status updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/all', methods=['GET'])
def get_all_orders():
    """Get all orders (staff only)"""
    try:
        if not USE_DATABASE:
            return jsonify({'success': False, 'message': 'Database not enabled'}), 500
        
        from src.models.database_models import OrderModel
        
        limit = request.args.get('limit', 100, type=int)
        orders_df = OrderModel.get_all_orders(limit)
        
        if orders_df.empty:
            return jsonify({
                'success': True,
                'orders': [],
                'message': 'No orders found'
            }), 200
        
        # Convert to list of dictionaries
        orders_data = orders_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'orders': orders_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
