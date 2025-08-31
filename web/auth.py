"""
Authentication middleware for the Food Recommendation System
"""

from functools import wraps
from flask import request, jsonify, redirect, url_for, session
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import USE_DATABASE, USERS_CSV_PATH

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For API routes, check for user_id in request
        if request.is_json and request.json:
            user_id = request.json.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            # Verify user exists
            if USE_DATABASE:
                try:
                    from src.models.database_models import UserModel
                    if not UserModel.user_exists(user_id):
                        return jsonify({'success': False, 'message': 'Invalid user ID'}), 401
                except Exception:
                    return jsonify({'success': False, 'message': 'Database error'}), 500
            else:
                # Fallback to CSV
                if not USERS_CSV_PATH.exists():
                    return jsonify({'success': False, 'message': 'User not found'}), 404
                
                users_df = pd.read_csv(USERS_CSV_PATH)
                if users_df[users_df['user_id'] == user_id].empty:
                    return jsonify({'success': False, 'message': 'Invalid user ID'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def check_user_exists(user_id):
    """Check if a user exists in the database"""
    if USE_DATABASE:
        try:
            from src.models.database_models import UserModel
            return UserModel.user_exists(user_id)
        except Exception:
            # Fallback to CSV
            pass
    
    # CSV fallback
    if not USERS_CSV_PATH.exists():
        return False
    
    try:
        users_df = pd.read_csv(USERS_CSV_PATH)
        return not users_df[users_df['user_id'] == user_id].empty
    except Exception:
        return False

def get_user_info(user_id):
    """Get user information from the database"""
    if USE_DATABASE:
        try:
            from src.models.database_models import UserModel
            return UserModel.get_user_by_id(user_id)
        except Exception:
            # Fallback to CSV
            pass
    
    # CSV fallback
    if not USERS_CSV_PATH.exists():
        return None
    
    try:
        users_df = pd.read_csv(USERS_CSV_PATH)
        user_row = users_df[users_df['user_id'] == user_id]
        if user_row.empty:
            return None
        
        user_data = user_row.iloc[0]
        return {
            'user_id': user_id,
            'name': user_data['name'],
            'email': user_data['email']
        }
    except Exception:
        return None
