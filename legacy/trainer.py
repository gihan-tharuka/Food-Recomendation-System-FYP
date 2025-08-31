# trainer.py
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.multioutput import MultiOutputClassifier

# Load labeled training data
#df = pd.read_csv('/content/drive/MyDrive/DataSets02-ClassificationModel/Pre/labeled_menu.csv')
df = pd.read_csv('data/Pre/labeled_menu.csv')

# Features
X = df[['item_name', 'price']]

# Label targets
y_cuisine = df['cuisine']
y_category = df['category']  # NEW
y_tags = df[['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']]

# Feature Preprocessing: TF-IDF on item_name and scaling price
preprocessor = ColumnTransformer([
    ('name_tfidf', TfidfVectorizer(), 'item_name'),
    ('price_scaler', StandardScaler(), ['price'])
])

# --- Model 1: Cuisine classification ---
cuisine_pipeline = Pipeline([
    ('features', preprocessor),
    ('clf', LogisticRegression(max_iter=1000))
])
cuisine_pipeline.fit(X, y_cuisine)
joblib.dump(cuisine_pipeline, 'cuisine_model.joblib')


# --- Model 2: Category classification ---
category_pipeline = Pipeline([
    ('features', preprocessor),
    ('clf', LogisticRegression(max_iter=1000))
])
category_pipeline.fit(X, y_category)
joblib.dump(category_pipeline, 'category_model.joblib')


# --- Model 3: Tag prediction (multi-label)
tags_pipeline = Pipeline([
    ('features', preprocessor),
    ('clf', MultiOutputClassifier(LogisticRegression(max_iter=1000)))
])
tags_pipeline.fit(X, y_tags)
joblib.dump(tags_pipeline, 'tags_model.joblib')

print("✅ Models for cuisine, category, and tags trained and saved.")
