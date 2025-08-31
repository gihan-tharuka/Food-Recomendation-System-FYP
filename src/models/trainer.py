import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
import sys
sys.path.insert(0, str(project_root))

from config.settings import *

class ModelTrainer:
    def __init__(self):
        self.data_path = TRAINING_DATA_PATH
        self.models_dir = MODELS_DIR
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.results = {}
        
    def load_and_preprocess_data(self):
        """Load and preprocess the training data"""
        print("Loading training data...")
        
        # Load data using the correct path
        df = pd.read_csv(self.data_path)
        
        # --- FIX: Clean 'price' column ---
        df['price'] = df['price'].replace({'—': None, '–': None, '': None, '-': None})
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df.dropna(subset=['price'])
        df['price'] = df['price'].astype(float)
        
        # Handle missing descriptions (to avoid errors for TF-IDF)
        df['description'] = df['description'].fillna("")
        
        print(f"Dataset loaded successfully with {len(df)} records")
        
        # Features
        X = df[['item_name', 'description', 'price']]
        
        # Targets
        y_cuisine = df['cuisine']
        y_category = df['category']
        y_tags = df[['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']]
        
        # Filter out tag columns with only one unique class
        y_tags_filtered = y_tags.loc[:, y_tags.nunique() > 1]
        
        return X, y_cuisine, y_category, y_tags_filtered
    
    def create_preprocessor(self):
        """Create the feature preprocessing pipeline"""
        # Preprocessor: TF-IDF for item_name + description, scaling for price
        preprocessor = ColumnTransformer([
            ('name_tfidf', TfidfVectorizer(), 'item_name'),
            ('desc_tfidf', TfidfVectorizer(), 'description'),
            ('price_scaler', StandardScaler(), ['price'])
        ])
        return preprocessor
    
    def train_cuisine_model(self, X_train, X_test, y_cuisine_train, y_cuisine_test, preprocessor):
        """Train the cuisine classification model"""
        print("Training cuisine model...")
        
        cuisine_pipeline = Pipeline([
            ('features', preprocessor),
            ('clf', LogisticRegression(max_iter=1000))
        ])
        
        param_grid_cuisine = {
            'clf__C': [0.1, 1, 10],
            'clf__penalty': ['l2'] # l1 and elasticnet require different solvers
        }
        
        grid_search_cuisine = GridSearchCV(cuisine_pipeline, param_grid_cuisine, cv=5, scoring='accuracy')
        grid_search_cuisine.fit(X_train, y_cuisine_train)
        
        cuisine_pipeline = grid_search_cuisine.best_estimator_ # Use the best model
        y_cuisine_pred = cuisine_pipeline.predict(X_test)
        
        # Store results
        cuisine_accuracy = accuracy_score(y_cuisine_test, y_cuisine_pred)
        self.results['cuisine'] = {
            'accuracy': cuisine_accuracy,
            'best_params': grid_search_cuisine.best_params_,
            'classification_report': classification_report(y_cuisine_test, y_cuisine_pred, output_dict=True)
        }
        
        print(f"🍽️ Cuisine Classification Results:")
        print(f"Accuracy: {cuisine_accuracy:.4f}")
        print(f"Best parameters: {grid_search_cuisine.best_params_}")
        
        # Save model
        model_path = self.models_dir / "cuisine_model.joblib"
        joblib.dump(cuisine_pipeline, model_path)
        print(f"Cuisine model saved to: {model_path}")
        
        return cuisine_pipeline
    
    def train_category_model(self, X_train, X_test, y_category_train, y_category_test, preprocessor):
        """Train the category classification model"""
        print("Training category model...")
        
        category_pipeline = Pipeline([
            ('features', preprocessor),
            ('clf', LogisticRegression(max_iter=1000))
        ])
        
        param_grid_category = {
            'clf__C': [0.1, 1, 10],
            'clf__penalty': ['l2']
        }
        
        grid_search_category = GridSearchCV(category_pipeline, param_grid_category, cv=5, scoring='accuracy')
        grid_search_category.fit(X_train, y_category_train)
        
        category_pipeline = grid_search_category.best_estimator_ # Use the best model
        y_category_pred = category_pipeline.predict(X_test)
        
        # Store results
        category_accuracy = accuracy_score(y_category_test, y_category_pred)
        self.results['category'] = {
            'accuracy': category_accuracy,
            'best_params': grid_search_category.best_params_,
            'classification_report': classification_report(y_category_test, y_category_pred, output_dict=True)
        }
        
        print(f"📂 Category Classification Results:")
        print(f"Accuracy: {category_accuracy:.4f}")
        print(f"Best parameters: {grid_search_category.best_params_}")
        
        # Save model
        model_path = self.models_dir / "category_model.joblib"
        joblib.dump(category_pipeline, model_path)
        print(f"Category model saved to: {model_path}")
        
        return category_pipeline
    
    def train_tags_model(self, X_train, X_test, y_tags_train, y_tags_test, preprocessor, y_tags_filtered):
        """Train the multi-label tag prediction model"""
        print("Training tags model...")
        
        tags_pipeline = Pipeline([
            ('features', preprocessor),
            ('clf', MultiOutputClassifier(LogisticRegression(max_iter=1000)))
        ])
        
        param_grid_tags = {
            'clf__estimator__C': [0.1, 1, 10],
            'clf__estimator__penalty': ['l2']
        }
        
        grid_search_tags = GridSearchCV(tags_pipeline, param_grid_tags, cv=5, scoring='accuracy')
        grid_search_tags.fit(X_train, y_tags_train)
        
        tags_pipeline = grid_search_tags.best_estimator_ # Use the best model
        y_tags_pred = tags_pipeline.predict(X_test)
        y_tags_prob = tags_pipeline.predict_proba(X_test)  # list of arrays
        
        # Convert list of arrays to single array
        y_tags_prob_array = np.vstack([prob[:, 1] for prob in y_tags_prob]).T
        
        print(f"🏷️ Tag Prediction Results:")
        tag_accuracies = []
        for i, col in enumerate(y_tags_filtered.columns):
            accuracy = accuracy_score(y_tags_test[col], y_tags_pred[:, i])
            tag_accuracies.append(accuracy)
            print(f"  {col}: {accuracy:.4f}")
        
        # Filter y_tags_test and y_tags_prob_array to exclude columns with only one unique class in y_tags_test
        cols_to_include = y_tags_test.columns[y_tags_test.nunique() > 1]
        y_tags_test_filtered_roc = y_tags_test[cols_to_include]
        y_tags_prob_array_filtered_roc = y_tags_prob_array[:, y_tags_test.nunique() > 1]
        
        # Compute ROC AUC
        macro_roc_auc = roc_auc_score(y_tags_test_filtered_roc, y_tags_prob_array_filtered_roc, average='macro')
        micro_roc_auc = roc_auc_score(y_tags_test_filtered_roc, y_tags_prob_array_filtered_roc, average='micro')
        
        # Store results
        self.results['tags'] = {
            'tag_accuracies': dict(zip(y_tags_filtered.columns, tag_accuracies)),
            'macro_roc_auc': macro_roc_auc,
            'micro_roc_auc': micro_roc_auc,
            'best_params': grid_search_tags.best_params_
        }
        
        print(f"Macro ROC AUC: {macro_roc_auc:.4f}")
        print(f"Micro ROC AUC: {micro_roc_auc:.4f}")
        print(f"Best parameters: {grid_search_tags.best_params_}")
        
        # Save model
        model_path = self.models_dir / "tags_model.joblib"
        joblib.dump(tags_pipeline, model_path)
        print(f"Tags model saved to: {model_path}")
        
        return tags_pipeline
    
    def train_all_models(self):
        """Train all models and return results"""
        try:
            print("=" * 60)
            print("🚀 Starting Model Training Process")
            print("=" * 60)
            
            # Load and preprocess data
            X, y_cuisine, y_category, y_tags_filtered = self.load_and_preprocess_data()
            
            # Train/Test Split
            print("Splitting data...")
            X_train, X_test, y_cuisine_train, y_cuisine_test = train_test_split(X, y_cuisine, test_size=0.2, random_state=42)
            _, _, y_category_train, y_category_test = train_test_split(X, y_category, test_size=0.2, random_state=42)
            _, _, y_tags_train, y_tags_test = train_test_split(X, y_tags_filtered, test_size=0.2, random_state=42)
            
            # Create preprocessor
            preprocessor = self.create_preprocessor()
            
            # Train individual models
            print("\n" + "=" * 40)
            self.train_cuisine_model(X_train, X_test, y_cuisine_train, y_cuisine_test, preprocessor)
            
            print("\n" + "=" * 40)
            self.train_category_model(X_train, X_test, y_category_train, y_category_test, preprocessor)
            
            print("\n" + "=" * 40)
            self.train_tags_model(X_train, X_test, y_tags_train, y_tags_test, preprocessor, y_tags_filtered)
            
            print("\n" + "=" * 60)
            print("✅ All models trained successfully!")
            print("=" * 60)
            
            # Print summary
            self.print_training_summary()
            
            return self.results
            
        except Exception as e:
            print(f"❌ Error during training: {str(e)}")
            raise e
    
    def print_training_summary(self):
        """Print a summary of training results"""
        print("\n📊 TRAINING SUMMARY")
        print("-" * 40)
        
        if 'cuisine' in self.results:
            print(f"🍽️  Cuisine Model Accuracy: {self.results['cuisine']['accuracy']:.4f}")
        
        if 'category' in self.results:
            print(f"📂 Category Model Accuracy: {self.results['category']['accuracy']:.4f}")
        
        if 'tags' in self.results:
            print(f"🏷️  Tags Model Macro ROC AUC: {self.results['tags']['macro_roc_auc']:.4f}")
            print(f"🏷️  Tags Model Micro ROC AUC: {self.results['tags']['micro_roc_auc']:.4f}")
        
        print(f"💾 Models saved to: {self.models_dir}")
        print("-" * 40)

# For backward compatibility and testing
if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all_models()