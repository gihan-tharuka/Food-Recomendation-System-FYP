import pandas as pd
import numpy as np
from pulp import LpProblem, LpVariable, LpMinimize, LpBinary, lpSum, LpStatus
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
from pathlib import Path
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class FoodRecommender:
    """
    Food recommendation system using collaborative filtering and optimization with SHAP explanations
    """
    
    def __init__(self):
        # Set data file paths
        project_root = Path(__file__).parent.parent.parent
        self.users_csv = os.path.join(project_root, "data", "DB", "users.csv")
        self.ratings_csv = os.path.join(project_root, "data", "DB", "ratings_shap_test.csv")  # Use SHAP test ratings for compatibility
        self.menu_csv = os.path.join(project_root, "data", "DB", "SpiciaMenu.csv")
        
        # Load data once during initialization
        self.users = pd.read_csv(self.users_csv)
        self.ratings = pd.read_csv(self.ratings_csv)
        self.menu = pd.read_csv(self.menu_csv)
        
        # Prepare user-item matrix for collaborative filtering
        self.user_item_matrix = self.ratings.pivot(index='user_id', columns='item_id', values='rating').fillna(0)
        self.user_similarity = cosine_similarity(self.user_item_matrix)
        self.user_item_matrix_np = self.user_item_matrix.values
        self.user_similarity_np = self.user_similarity
        
        # Initialize SHAP explainer
        self.shap_explainer = None
        self.feature_names = None
        self._prepare_shap_model()
    
    def _extract_base_item_name(self, item_name):
        """
        Extract the base item name by removing size indicators.
        Handles multiple formats:
        - Dash format: "Dish Name - Small", "Dish Name - Large", etc.
        - Bracket format: "Dish Name (S)", "Dish Name (R)", "Dish Name (L)", "Dish Name (M)"
        - Also handles variations like "Dish Name(S)" without space
        
        Args:
            item_name (str): Original item name
            
        Returns:
            str: Base item name without size indicators
        """
        # Remove various size indicators
        patterns = [
            r'\s*-\s*(Small|Large|Medium|Regular|Mini|XL|Extra\s*Large).*$',  # Dash format
            r'\s*\([SRLMX]\).*$',  # Bracket format with common size letters
            r'\([SRLMX]\)',  # Bracket format without trailing content
            r'\s*\((Small|Large|Medium|Regular|Mini)\).*$',  # Full words in brackets
        ]
        
        result = item_name
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        return result.strip()
    
    def _extract_dish_type(self, item_name):
        """
        Extract the dish type/family to identify similar dishes.
        This helps group similar items like different types of soups, chicken dishes, etc.
        
        Args:
            item_name (str): Original item name
            
        Returns:
            str: Dish type/family identifier
        """
        # Convert to lowercase for comparison
        name_lower = item_name.lower()
        
        # Define dish type patterns - order matters (more specific first)
        dish_patterns = [
            # Specific soup types
            (r'sweet corn soup', 'sweet_corn_soup'),
            (r'tom yum', 'tom_yum_soup'),
            (r'mee hoon soup', 'mee_hoon_soup'),
            (r'seafood soup', 'seafood_soup'),
            (r'cream of', 'cream_soup'),
            
            # General soup category
            (r'soup', 'soup'),
            
            # Chicken preparations by cooking method/style
            (r'hot garlic chicken', 'hot_garlic_chicken'),
            (r'chilli chicken', 'chilli_chicken'),
            (r'pepper chicken', 'pepper_chicken'),
            (r'devilled chicken', 'devilled_chicken'),
            (r'lemon chicken', 'lemon_chicken'),
            (r'sweet and sour chicken', 'sweet_sour_chicken'),
            (r'spicy chicken', 'spicy_chicken'),
            (r'dry.*chilli chicken', 'dry_chilli_chicken'),
            (r'manchurian chicken', 'manchurian_chicken'),
            (r'cashew.*chicken|chicken.*cashew', 'cashew_chicken'),
            (r'hot batter chicken', 'hot_batter_chicken'),
            (r'roast chicken', 'roast_chicken'),
            
            # Other protein-specific dishes
            (r'beef', 'beef_dish'),
            (r'pork', 'pork_dish'),
            (r'prawn|shrimp', 'prawn_dish'),
            (r'fish', 'fish_dish'),
            (r'crab', 'crab_dish'),
            (r'seafood', 'seafood_dish'),
            
            # Vegetarian dishes by main ingredient
            (r'mushroom', 'mushroom_dish'),
            (r'baby corn', 'baby_corn_dish'),
            (r'kang kung', 'kang_kung_dish'),
            (r'string beans', 'string_beans_dish'),
            (r'mixed vegetables', 'mixed_veg_dish'),
            (r'potato', 'potato_dish'),
            
            # Rice preparations
            (r'fried rice', 'fried_rice'),
            (r'rice', 'rice_dish'),
            
            # Noodle preparations
            (r'fried noodles|chow mein', 'fried_noodles'),
            (r'noodles', 'noodle_dish'),
            
            # Egg preparations
            (r'omelette', 'omelette'),
            (r'fried egg', 'fried_egg'),
            
            # Curry types
            (r'curry', 'curry'),
            
            # Salads
            (r'salad', 'salad'),
            
            # Desserts
            (r'ice cream', 'ice_cream'),
            (r'cake', 'cake'),
            (r'pudding', 'pudding'),
            
            # Beverages
            (r'tea', 'tea'),
            (r'coffee', 'coffee'),
            (r'juice', 'juice'),
            (r'shake|smoothie', 'shake'),
        ]
        
        # Check each pattern
        for pattern, dish_type in dish_patterns:
            if re.search(pattern, name_lower):
                return dish_type
        
        # If no specific pattern matches, use the first word as dish type
        first_word = name_lower.split()[0] if name_lower.split() else 'unknown'
        return f'generic_{first_word}'
    
    def _prepare_shap_model(self):
        """Prepare a surrogate model for SHAP explanations"""
        try:
            print("🔧 Preparing SHAP model...")
            # Create features for SHAP model
            features_data = []
            target_data = []
            
            for _, rating_row in self.ratings.iterrows():
                user_id = rating_row['user_id']
                item_id = rating_row['item_id']
                rating = rating_row['rating']
                
                # Get item features
                item_info = self.menu[self.menu['item_id'] == item_id]
                if item_info.empty:
                    continue
                    
                item_row = item_info.iloc[0]
                
                # Get user collaborative filtering features
                if user_id in self.user_item_matrix.index:
                    user_index = self.user_item_matrix.index.get_loc(user_id)
                    user_avg_rating = self.user_item_matrix.iloc[user_index].mean()
                    user_rating_count = (self.user_item_matrix.iloc[user_index] > 0).sum()
                else:
                    user_avg_rating = 3.0
                    user_rating_count = 0
                
                # Create feature vector
                features = [
                    float(item_row['price']),
                    float(item_row.get('is_morning', 0)),
                    float(item_row.get('is_afternoon', 0)),
                    float(item_row.get('is_evening', 0)),
                    float(item_row.get('is_sunny', 0)),
                    float(item_row.get('is_rainy', 0)),
                    float(item_row.get('is_cloudy', 0)),  # This column doesn't exist in menu but needed for consistency
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
                
                features_data.append(features)
                target_data.append(rating)
            
            # Define feature names
            self.feature_names = [
                'price', 'is_morning', 'is_afternoon', 'is_evening',
                'is_sunny', 'is_rainy', 'is_cloudy', 'user_avg_rating',
                'user_rating_count', 'category_appetizer', 'category_main',
                'category_dessert', 'category_beverage', 'cuisine_italian',
                'cuisine_chinese', 'cuisine_indian', 'cuisine_mexican'
            ]
            
            print(f"📊 Collected {len(features_data)} feature samples")
            
            # Initialize default values in case of error
            self.surrogate_model = None
            self.shap_explainer = None
            
            if len(features_data) > 0:
                X = np.array(features_data)
                y = np.array(target_data)
                
                print(f"📈 Training surrogate model with {X.shape[0]} samples and {X.shape[1]} features")
                
                # Train surrogate model
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                self.surrogate_model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.surrogate_model.fit(X_train, y_train)
                
                print("✅ Surrogate model trained successfully")
                
                # Initialize SHAP explainer
                self.shap_explainer = shap.TreeExplainer(self.surrogate_model)
                print("✅ SHAP explainer initialized successfully")
                
            else:
                print("❌ No feature data available for SHAP model")
                
        except Exception as e:
            print(f"❌ Error preparing SHAP model: {str(e)}")
            import traceback
            traceback.print_exc()
            self.surrogate_model = None
            self.shap_explainer = None
    
    def _create_feature_vector(self, user_id, item_row, preferences):
        """Create feature vector for a specific user-item pair"""
        # Get user collaborative filtering features
        if user_id in self.user_item_matrix.index:
            user_index = self.user_item_matrix.index.get_loc(user_id)
            user_avg_rating = self.user_item_matrix.iloc[user_index].mean()
            user_rating_count = (self.user_item_matrix.iloc[user_index] > 0).sum()
        else:
            user_avg_rating = 3.0
            user_rating_count = 0
        
        # Get current context
        current_time = preferences.get('time_of_day', 'morning')
        current_weather = preferences.get('weather', 'sunny')
        
        # Create feature vector
        features = [
            float(item_row['price']),
            1.0 if current_time == 'morning' else 0.0,
            1.0 if current_time == 'afternoon' else 0.0,
            1.0 if current_time == 'evening' else 0.0,
            1.0 if current_weather == 'sunny' else 0.0,
            1.0 if current_weather == 'rainy' else 0.0,
            1.0 if current_weather == 'cloudy' else 0.0,  # This maintains consistency even though menu doesn't have is_cloudy
            user_avg_rating,
            user_rating_count,
            1.0 if item_row['category'] == 'Appetizer' else 0.0,
            1.0 if item_row['category'] == 'Main Course' else 0.0,
            1.0 if item_row['category'] == 'Dessert' else 0.0,
            1.0 if item_row['category'] == 'Beverage' else 0.0,
            1.0 if item_row['cuisine'] == 'Italian' else 0.0,
            1.0 if item_row['cuisine'] == 'Chinese' else 0.0,
            1.0 if item_row['cuisine'] == 'Indian' else 0.0,
            1.0 if item_row['cuisine'] == 'Mexican' else 0.0,
        ]
        
        return np.array(features).reshape(1, -1)
    
    def get_shap_explanations(self, user_id, recommendations, preferences):
        """Generate SHAP explanations for recommendations"""
        if self.shap_explainer is None:
            return None
        
        try:
            explanations = []
            
            for rec in recommendations:
                item_id = rec['item_id']
                item_info = self.menu[self.menu['item_id'] == item_id]
                
                if item_info.empty:
                    continue
                
                item_row = item_info.iloc[0]
                
                # Create feature vector for this recommendation
                feature_vector = self._create_feature_vector(user_id, item_row, preferences)
                
                # Get SHAP values
                shap_values = self.shap_explainer.shap_values(feature_vector)
                
                # Create explanation dictionary
                explanation = {
                    'item_id': item_id,
                    'item_name': rec['item_name'],
                    'predicted_rating': float(self.surrogate_model.predict(feature_vector)[0]),
                    'base_value': float(self.shap_explainer.expected_value),
                    'shap_values': {},
                    'feature_contributions': {}
                }
                
                # Map SHAP values to feature names
                for i, feature_name in enumerate(self.feature_names):
                    shap_val = float(shap_values[0][i])
                    feature_val = float(feature_vector[0][i])
                    
                    explanation['shap_values'][feature_name] = shap_val
                    explanation['feature_contributions'][feature_name] = {
                        'value': feature_val,
                        'shap_contribution': shap_val,
                        'impact': 'positive' if shap_val > 0 else 'negative' if shap_val < 0 else 'neutral'
                    }
                
                # Sort features by absolute SHAP value contribution
                sorted_features = sorted(
                    explanation['feature_contributions'].items(),
                    key=lambda x: abs(x[1]['shap_contribution']),
                    reverse=True
                )
                
                explanation['top_contributing_features'] = [
                    {
                        'feature': feature,
                        'value': contrib['value'],
                        'shap_contribution': contrib['shap_contribution'],
                        'impact': contrib['impact']
                    }
                    for feature, contrib in sorted_features[:5]  # Top 5 features
                ]
                
                explanations.append(explanation)
            
            return explanations
            
        except Exception as e:
            print(f"Error generating SHAP explanations: {str(e)}")
            return None
    
    def get_available_cuisines(self):
        """Get list of available cuisines"""
        return self.menu['cuisine'].unique().tolist()
    
    def get_available_categories(self, cuisine=None):
        """Get list of available categories, optionally filtered by cuisine"""
        if cuisine:
            return self.menu[self.menu['cuisine'] == cuisine]['category'].unique().tolist()
        return self.menu['category'].unique().tolist()

    def get_categories_with_supplements(self, cuisine):
        """
        Get categories for a cuisine with international supplements for missing categories.
        
        Args:
            cuisine (str): The selected cuisine
            
        Returns:
            dict: {
                'native_categories': list of categories available in the cuisine,
                'supplemented_categories': list of categories from International cuisine,
                'warning_needed': bool indicating if supplements are being used,
                'total_categories': combined list of all available categories
            }
        """
        if not cuisine:
            return {
                'native_categories': [],
                'supplemented_categories': [],
                'warning_needed': False,
                'total_categories': []
            }
        
        # Get categories for the selected cuisine
        native_categories = self.menu[self.menu['cuisine'] == cuisine]['category'].unique().tolist()
        
        # Get categories for International cuisine
        international_categories = self.menu[self.menu['cuisine'] == 'International']['category'].unique().tolist()
        
        # Find categories that exist in International but not in the selected cuisine
        supplemented_categories = [cat for cat in international_categories if cat not in native_categories]
        
        # Determine if we need to show warning (if cuisine has ≤ 3 categories and supplements are available)
        warning_needed = len(native_categories) <= 3 and len(supplemented_categories) > 0
        
        # Combine all categories
        total_categories = sorted(native_categories + supplemented_categories)
        
        return {
            'native_categories': sorted(native_categories),
            'supplemented_categories': sorted(supplemented_categories),
            'warning_needed': warning_needed,
            'total_categories': total_categories,
            'cuisine': cuisine
        }

    def generate_recommendations(self, user_id, preferences):
        """
        Generate food recommendations for a user based on preferences
        
        Returns:
            tuple: (recommendations_list, total_cost, shap_explanations)
        """
        try:
            # Extract preferences
            total_budget = preferences.get('budget', 5000)
            preferred_cuisine = preferences.get('cuisine', '')
            user_categories = preferences.get('categories', [])
            category_priority = preferences.get('category_priority', [])
            require_each_category = preferences.get('require_each_category', False)
            current_time = preferences.get('time_of_day', 'morning')
            current_weather = preferences.get('weather', 'sunny')
            
            # Prepare candidate menu items with intelligent cuisine mixing
            df = self.menu.copy()
            
            # Get cuisine category analysis
            cuisine_analysis = self.get_categories_with_supplements(preferred_cuisine)
            native_categories = cuisine_analysis['native_categories']
            
            # Separate categories into native and supplemented
            native_selected = [cat for cat in user_categories if cat in native_categories]
            supplemented_selected = [cat for cat in user_categories if cat not in native_categories]
            
            # Filter menu items intelligently
            filtered_items = []
            
            # Add items from the preferred cuisine for native categories
            if native_selected:
                native_items = df[(df['cuisine'] == preferred_cuisine) & (df['category'].isin(native_selected))]
                filtered_items.append(native_items)
            
            # Add items from International cuisine for supplemented categories
            if supplemented_selected:
                supplemented_items = df[(df['cuisine'] == 'International') & (df['category'].isin(supplemented_selected))]
                filtered_items.append(supplemented_items)
            
            # Combine all filtered items
            if filtered_items:
                df = pd.concat(filtered_items, ignore_index=True)
            else:
                df = pd.DataFrame()  # Empty dataframe if no valid items
            
            if df.empty:
                return [], 0, None
            
            # Add time and weather scores
            df['time_score'] = df[f'is_{current_time}'].astype(int)
            df['weather_score'] = df[f'is_{current_weather}'].astype(int)
            
            # Collaborative filtering prediction
            user_ratings = self.ratings[self.ratings['user_id'] == user_id]
            df = df.merge(user_ratings[['item_id', 'rating']], on='item_id', how='left')
            
            # Check if user exists in user_item_matrix
            if user_id not in self.user_item_matrix.index:
                # For new users, use average ratings
                df['predicted_rating'] = df.apply(lambda row: 
                    self.ratings[self.ratings['item_id'] == row['item_id']]['rating'].mean() 
                    if not pd.isna(row['rating']) else 3.0, axis=1)
            else:
                user_index = self.user_item_matrix.index.get_loc(user_id)
                predicted_ratings_list = []
                
                for index, row in df.iterrows():
                    item_id = row['item_id']
                    if pd.isna(row['rating']):
                        if item_id in self.user_item_matrix.columns:
                            item_index = self.user_item_matrix.columns.get_loc(item_id)
                            similar_users = self.user_similarity_np[user_index]
                            user_ratings_for_item = self.user_item_matrix_np[:, item_index]
                            pos_idx = np.where((similar_users > 0) & (user_ratings_for_item > 0))[0]
                            if len(pos_idx) > 0:
                                weighted_sum = np.sum(similar_users[pos_idx] * user_ratings_for_item[pos_idx])
                                sum_of_weights = np.sum(similar_users[pos_idx])
                                predicted_rating = weighted_sum / sum_of_weights
                            else:
                                predicted_rating = 3.0
                            predicted_ratings_list.append(predicted_rating)
                        else:
                            predicted_ratings_list.append(3.0)
                    else:
                        predicted_ratings_list.append(row['rating'])
                
                df['predicted_rating'] = predicted_ratings_list
            
            df['final_rating'] = df['rating'].combine_first(df['predicted_rating'])
            
            if df['final_rating'].notnull().any():
                df['final_rating'] = df['final_rating'].fillna(df['final_rating'].median())
            else:
                df['final_rating'] = df['final_rating'].fillna(3.0)
            
            # Compute relevance score
            df['relevance'] = df['final_rating'] + 0.5 * df['time_score'] + 0.5 * df['weather_score']
            item_ids = df['item_id'].tolist()
            
            if not item_ids:
                return [], 0, None
            
            # Linear Programming optimization
            prob = LpProblem('MenuRecommendation', LpMinimize)
            x = LpVariable.dicts('select', item_ids, cat=LpBinary)
            
            # Calculate budget and relevance
            budget_used = lpSum([x[i] * df.loc[df['item_id'] == i, 'price'].values[0] for i in item_ids])
            relevance_sum = lpSum([x[i] * df.loc[df['item_id'] == i, 'relevance'].values[0] for i in item_ids])
            
            # Objective function: maximize relevance while staying within budget
            prob += (-relevance_sum) + (total_budget - budget_used) * 0.02
            
            # Budget constraint
            prob += budget_used <= total_budget
            
            # Category requirements
            if require_each_category:
                for cat in user_categories:
                    category_items = df[df['category'] == cat]['item_id']
                    if len(category_items) > 0:
                        prob += lpSum([x[i] for i in category_items]) >= 1
            
            # Prevent multiple portion sizes of same dish
            # Remove size indicators: both dash format (- Small/Large/Medium/Regular) and bracket format (S/R/L/M)
            df['base_item_name'] = df['item_name'].apply(self._extract_base_item_name)
            
            for base_name in df['base_item_name'].unique():
                same_dish_ids = df[df['base_item_name'] == base_name]['item_id']
                if len(same_dish_ids) > 1:
                    # Debug: Print when multiple sizes are found for the same dish
                    dish_variants = df[df['base_item_name'] == base_name]['item_name'].tolist()
                    print(f"🍽️ Found multiple sizes for '{base_name}': {dish_variants}")
                    prob += lpSum([x[i] for i in same_dish_ids]) <= 1
            
            # Add diversity constraints to prevent too many similar dishes
            df['dish_type'] = df['item_name'].apply(self._extract_dish_type)
            
            # Limit the number of items from the same dish type family
            for dish_type in df['dish_type'].unique():
                same_type_ids = df[df['dish_type'] == dish_type]['item_id']
                if len(same_type_ids) > 1:
                    # Allow maximum 2 items from the same dish type family
                    # This prevents getting 3+ sweet corn soups or 3+ chicken dishes
                    max_same_type = min(2, len(same_type_ids))
                    prob += lpSum([x[i] for i in same_type_ids]) <= max_same_type
                    
                    # Debug: Print diversity constraint application
                    dish_variants = df[df['dish_type'] == dish_type]['item_name'].tolist()
                    if len(dish_variants) > 2:
                        print(f"🎯 Applying diversity constraint for '{dish_type}': max {max_same_type} from {dish_variants}")
            
            # Additional constraint: For categories with many similar items, encourage variety
            for category in user_categories:
                category_items = df[df['category'] == category]
                if len(category_items) > 0:
                    # Group by dish type within category
                    dish_types_in_category = category_items['dish_type'].unique()
                    
                    # If there are multiple dish types in this category, encourage selecting from different types
                    if len(dish_types_in_category) > 2:
                        # Try to select from at least 2 different dish types if possible
                        for dish_type in dish_types_in_category:
                            type_items_in_cat = category_items[category_items['dish_type'] == dish_type]['item_id']
                            if len(type_items_in_cat) > 1:
                                # Prefer selecting at most 1 item per dish type when multiple types are available
                                prob += lpSum([x[i] for i in type_items_in_cat]) <= 1
            
            # Category priority allocation
            if category_priority:
                print(f"🎯 Applying category priority constraints...")
                priority_weights = {cat: len(category_priority) - idx for idx, cat in enumerate(category_priority)}
                priority_total = sum(priority_weights.values())
                
                print(f"   Priority weights: {priority_weights}")
                print(f"   Total weight: {priority_total}")
                
                # Apply much stronger priority constraints
                for cat, weight in priority_weights.items():
                    category_items = df[df['category'] == cat]['item_id']
                    if len(category_items) > 0:
                        # Calculate minimum and maximum budget allocation for this category
                        expected_proportion = weight / priority_total
                        priority_index = category_priority.index(cat)
                        
                        # Much stronger minimum allocation - higher priorities get more aggressive minimums
                        if priority_index == 0:  # Highest priority category
                            min_factor = 0.65  # At least 65% of expected
                        elif priority_index == 1:  # Second priority
                            min_factor = 0.55  # At least 55% of expected
                        else:  # Lower priorities
                            min_factor = 0.35  # At least 35% of expected
                            
                        min_allocation = total_budget * expected_proportion * min_factor
                        max_allocation = total_budget * expected_proportion * 1.3  # Tighter upper bound
                        
                        category_spending = lpSum([x[i] * df.loc[df['item_id'] == i, 'price'].values[0]
                                                 for i in category_items])
                        
                        # Strong minimum constraint: ensure higher priority categories get substantial budget
                        prob += category_spending >= min_allocation
                        
                        # Also add maximum constraint to prevent one category from dominating
                        prob += category_spending <= max_allocation
                        
                        print(f"   {cat} (priority {priority_index + 1}): "
                              f"expected {expected_proportion:.1%}, min ₹{min_allocation:.0f} ({min_factor*100:.0f}%), max ₹{max_allocation:.0f}")
                
                # Much stronger constraint: ensure strict priority ordering is respected
                # Higher priority categories should get significantly more than lower priority ones
                if len(category_priority) >= 2:
                    for i in range(len(category_priority) - 1):
                        higher_cat = category_priority[i]
                        lower_cat = category_priority[i + 1]
                        
                        higher_items = df[df['category'] == higher_cat]['item_id']
                        lower_items = df[df['category'] == lower_cat]['item_id']
                        
                        if len(higher_items) > 0 and len(lower_items) > 0:
                            higher_spending = lpSum([x[i] * df.loc[df['item_id'] == i, 'price'].values[0]
                                                   for i in higher_items])
                            lower_spending = lpSum([x[i] * df.loc[df['item_id'] == i, 'price'].values[0]
                                                  for i in lower_items])
                            
                            # Much stronger ordering: higher priority should get at least 110% of lower priority
                            prob += higher_spending >= lower_spending * 1.1
                            
                            print(f"   Strong priority ordering: {higher_cat} >= 110% of {lower_cat}")
                    
                    # Additional constraint: ensure top priority gets substantial share
                    top_priority_cat = category_priority[0]
                    top_priority_items = df[df['category'] == top_priority_cat]['item_id']
                    if len(top_priority_items) > 0:
                        top_priority_spending = lpSum([x[i] * df.loc[df['item_id'] == i, 'price'].values[0]
                                                     for i in top_priority_items])
                        # Top priority category should get at least 45% of total budget
                        prob += top_priority_spending >= total_budget * 0.45
                        print(f"   Top priority guarantee: {top_priority_cat} >= 45% of total budget")
            
            
            # Solve the optimization problem
            prob.solve()
            
             # If no optimal solution, return items sorted by relevance within budget
            if LpStatus[prob.status] != 'Optimal':
                print(f"⚠️ Optimization not optimal (status: {LpStatus[prob.status]}), using fallback selection with diversity and priority")
                df_sorted = df.sort_values('relevance', ascending=False)
                selected_items = []
                total_cost = 0
                selected_dish_types = {}  # Track selected dish types for diversity
                selected_base_names = set()  # Track selected base names to avoid duplicates
                category_spending = {}  # Track spending per category for priority respect
                
                # Initialize category spending tracking
                for cat in user_categories:
                    category_spending[cat] = 0
                
                # Calculate stronger target allocations if priority is specified
                priority_targets = {}
                if category_priority:
                    priority_weights = {cat: len(category_priority) - idx for idx, cat in enumerate(category_priority)}
                    priority_total = sum(priority_weights.values())
                    for cat, weight in priority_weights.items():
                        priority_index = category_priority.index(cat)
                        expected_proportion = weight / priority_total
                        
                        # Use stronger minimum targets matching the optimization constraints
                        if priority_index == 0:  # Highest priority category
                            min_factor = 0.65  # At least 65% of expected
                        elif priority_index == 1:  # Second priority
                            min_factor = 0.55  # At least 55% of expected
                        else:  # Lower priorities
                            min_factor = 0.35  # At least 35% of expected
                            
                        priority_targets[cat] = total_budget * expected_proportion * min_factor
                    
                    print(f"📊 Fallback strong priority targets: {priority_targets}")
                    
                    # Special target for top priority category (45% minimum)
                    top_priority_cat = category_priority[0]
                    top_priority_minimum = total_budget * 0.45
                    print(f"📊 Top priority minimum: {top_priority_cat} >= ₹{top_priority_minimum:.0f} (45%)")
                
                for _, item in df_sorted.iterrows():
                    # Check budget constraint
                    if total_cost + item['price'] > total_budget:
                        continue
                        
                    # Check if we already selected this exact dish (different size)
                    if item['base_item_name'] in selected_base_names:
                        continue
                        
                    # Check diversity constraint
                    dish_type = item['dish_type']
                    current_count = selected_dish_types.get(dish_type, 0)
                    
                    # Allow maximum 2 items from the same dish type
                    if current_count >= 2:
                        continue
                    
                    category = item['category']
                    
                    # Much stronger priority-aware selection
                    should_select = True
                    if category_priority and category in priority_targets:
                        current_cat_spending = category_spending.get(category, 0)
                        target_spending = priority_targets[category]
                        priority_index = category_priority.index(category)
                        
                        # Top priority category gets aggressive preference
                        if priority_index == 0:  # Highest priority
                            top_priority_minimum = total_budget * 0.45
                            if current_cat_spending < top_priority_minimum:
                                # Strongly prioritize top category until it reaches 45%
                                should_select = True
                            elif current_cat_spending > target_spending * 1.5:
                                should_select = False  # Don't over-allocate even for top priority
                        else:
                            # For lower priority categories, be much more restrictive
                            if current_cat_spending > target_spending * 1.1:
                                # Check if higher priority categories are significantly underrepresented
                                higher_priority_cats = category_priority[:priority_index]
                                higher_priority_under = any(
                                    category_spending.get(hcat, 0) < priority_targets.get(hcat, 0) * 0.9
                                    for hcat in higher_priority_cats
                                    if hcat in priority_targets
                                )
                                if higher_priority_under:
                                    should_select = False
                                    
                        # Additional check: ensure top priority dominance
                        if len(category_priority) >= 2 and priority_index > 0:
                            top_cat = category_priority[0]
                            top_spending = category_spending.get(top_cat, 0)
                            current_spending = current_cat_spending + item['price']
                            
                            # Enforce that higher priorities get more than lower priorities
                            required_ratio = 1.1  # 110% advantage for higher priority
                            if current_spending * required_ratio > top_spending:
                                should_select = False  # Would violate priority ordering
                    
                    if not should_select:
                        continue
                        
                    # If we have 1 item of this type and there are other dish types available,
                    # prefer selecting from different types first
                    if current_count >= 1 and len(selected_items) < 3:
                        # Check if there are items from other dish types still available within budget
                        other_types_available = False
                        for _, other_item in df_sorted.iterrows():
                            if (other_item['dish_type'] != dish_type and 
                                other_item['base_item_name'] not in selected_base_names and
                                total_cost + other_item['price'] <= total_budget and
                                selected_dish_types.get(other_item['dish_type'], 0) < 2):
                                other_types_available = True
                                break
                        
                        if other_types_available:
                            continue  # Skip this item to maintain diversity
                    
                    # Add the item
                    selected_items.append(item)
                    total_cost += item['price']
                    selected_base_names.add(item['base_item_name'])
                    selected_dish_types[dish_type] = current_count + 1
                    category_spending[category] = category_spending.get(category, 0) + item['price']
                    
                    print(f"📝 Selected: {item['item_name']} - ₹{item['price']} ({category}, type: {dish_type})")
                    
                    if len(selected_items) >= 8:  # Reasonable limit
                        break
                
                # Check if priority targets were met in fallback
                if category_priority:
                    print(f"📊 Fallback category allocation:")
                    for cat in category_priority:
                        spent = category_spending.get(cat, 0)
                        target = priority_targets.get(cat, 0)
                        percentage = (spent / total_cost * 100) if total_cost > 0 else 0
                        target_percentage = (target / total_budget * 100) if total_budget > 0 else 0
                        print(f"   {cat}: ₹{spent:.0f} ({percentage:.1f}%) vs target ₹{target:.0f} ({target_percentage:.1f}%)")
                        
                df_selected = pd.DataFrame(selected_items)
            else:
                # Get optimal solution
                selected_ids = [i for i in item_ids if x[i].varValue == 1]
                df_selected = df[df['item_id'].isin(selected_ids)].copy()
                total_cost = df_selected['price'].sum()
            
            if df_selected.empty:
                return [], 0, None
            
            # Prepare recommendations list
            recommendations = []
            for _, item in df_selected.iterrows():
                recommendations.append({
                    'item_id': int(item['item_id']),
                    'item_name': str(item['item_name']),
                    'description': str(item['description']),
                    'category': str(item['category']),
                    'price': float(item['price']),
                    'relevance': float(item['relevance']),
                    'rating': float(item['final_rating'])
                })
            
            # Generate SHAP explanations
            shap_explanations = self.get_shap_explanations(user_id, recommendations, preferences)
            
            return recommendations, float(total_cost), shap_explanations
            
        except Exception as e:
            print(f"Error in generate_recommendations: {str(e)}")
            return [], 0, None
    
    def get_user_ratings(self, user_id):
        """Get all ratings for a specific user"""
        user_ratings = self.ratings[self.ratings['user_id'] == user_id]
        ratings_list = []
        
        for _, rating in user_ratings.iterrows():
            # Get item details
            item_info = self.menu[self.menu['item_id'] == rating['item_id']]
            if not item_info.empty:
                item_details = item_info.iloc[0]
                ratings_list.append({
                    'item_id': int(rating['item_id']),
                    'item_name': str(item_details['item_name']),
                    'category': str(item_details['category']),
                    'cuisine': str(item_details['cuisine']),
                    'rating': int(rating['rating']),
                    'date': str(rating['date'])
                })
        
        return ratings_list
    
    def save_rating(self, user_id, item_id, rating):
        """Save a new rating (placeholder - would need database integration)"""
        try:
            # For now, just return True - in production this would save to database
            return True
        except Exception as e:
            print(f"Error saving rating: {str(e)}")
            return False
