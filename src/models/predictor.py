import pandas as pd
import joblib
import os
from pathlib import Path
from config.settings import (
    MODELS_DIR, CUISINE_MODEL_PATH, CATEGORY_MODEL_PATH, TAGS_MODEL_PATH,
    PRE_DATA_DIR, POST_DATA_DIR
)

class ModelPredictor:
    """Class for making predictions using trained models"""
    
    def __init__(self):
        """Initialize the predictor by loading trained models"""
        self.cuisine_pipeline = None
        self.category_pipeline = None
        self.tags_pipeline = None
        self.load_models()
    
    def load_models(self):
        """Load the trained models from the models directory"""
        try:
            self.cuisine_pipeline = joblib.load(CUISINE_MODEL_PATH)
            self.category_pipeline = joblib.load(CATEGORY_MODEL_PATH)
            self.tags_pipeline = joblib.load(TAGS_MODEL_PATH)
            print("Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
            raise
    
    def predict_and_save(self, input_filename='Spicia-menu.csv', output_filename='Spicia-menu-predicted.csv'):
        """
        Predict cuisine, category and tags for menu items and save results
            
        Returns:
            DataFrame with predictions
        """
        # Load the input data
        input_path = PRE_DATA_DIR / input_filename
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df_in = pd.read_csv(input_path)
        print(f"Loaded {len(df_in)} items from {input_path}")
        
        # Prepare the input data for prediction. 
        # Add a placeholder for the 'description' column as the model was trained with it
        X_input = df_in[['item_name', 'price']].copy()
        X_input['description'] = ""  # Add empty description column
        X_input = X_input[['item_name', 'description', 'price']]  # Ensure column order matches training data
        
        # Make predictions
        print("Generating predictions...")
        df_in['pred_cuisine'] = self.cuisine_pipeline.predict(X_input)
        df_in['pred_category'] = self.category_pipeline.predict(X_input)
        
        # Tags prediction returns a numpy array
        tag_predictions = self.tags_pipeline.predict(X_input)
        
        # Based on the training code, the tag columns should be in this order
        original_tag_cols = ['is_morning', 'is_evening', 'is_sunny', 'is_rainy']
        
        # Create a DataFrame for tag predictions with appropriate column names
        df_tags_pred = pd.DataFrame(tag_predictions, columns=[f'pred_{col}' for col in original_tag_cols])
        
        # Merge the predictions back to the original input DataFrame
        result_df = pd.concat([df_in, df_tags_pred], axis=1)
        
        # Create output directory if it doesn't exist
        POST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save the predicted results to a CSV file
        output_path = POST_DATA_DIR / output_filename
        result_df.to_csv(output_path, index=False)
        
        print(f"Predictions saved to: {output_path}")
        print(f"Generated predictions for {len(result_df)} items")
        
        return result_df
    
    def predict_single_item(self, item_name, price, description=""):
        """
        Predict attributes for a single menu item
        
        Args:
            item_name: Name of the food item
            price: Price of the item
            description: Description of the item (optional)
            
        Returns:
            Dictionary with predictions
        """
        # Prepare input data
        X_input = pd.DataFrame({
            'item_name': [item_name],
            'description': [description],
            'price': [price]
        })
        
        # Make predictions
        pred_cuisine = self.cuisine_pipeline.predict(X_input)[0]
        pred_category = self.category_pipeline.predict(X_input)[0]
        tag_predictions = self.tags_pipeline.predict(X_input)[0]
        
        # Tag column names
        original_tag_cols = ['is_morning', 'is_evening', 'is_sunny', 'is_rainy']
        
        result = {
            'item_name': item_name,
            'price': price,
            'pred_cuisine': pred_cuisine,
            'pred_category': pred_category
        }
        
        # Add tag predictions
        for i, col in enumerate(original_tag_cols):
            result[f'pred_{col}'] = tag_predictions[i]
        
        return result