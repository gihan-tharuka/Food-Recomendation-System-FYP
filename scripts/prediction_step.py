# prediction_step.py
import pandas as pd
import joblib

# Load Models
cuisine_model = joblib.load('cuisine_model.joblib')
category_model = joblib.load('category_model.joblib')  # NEW
tags_model = joblib.load('tags_model.joblib')

# Load raw minimal menu CSV
#menu_raw = pd.read_csv('/content/drive/MyDrive/DataSets02-ClassificationModel/Pre/menu_data_pre.csv')
menu_raw = pd.read_csv('data/Pre/menu_data_pre.csv')

# Predict
X_input = menu_raw[['item_name', 'price']]

pred_cuisine = cuisine_model.predict(X_input)
pred_category = category_model.predict(X_input)  # NEW
pred_tags = tags_model.predict(X_input)

# Add predictions to dataframe
menu_raw['cuisine'] = pred_cuisine
menu_raw['category'] = pred_category  # NEW
tag_columns = ['is_morning', 'is_afternoon', 'is_evening', 'is_sunny', 'is_rainy']
pred_tags_df = pd.DataFrame(pred_tags, columns=tag_columns)

# Final augmented menu
menu_full = pd.concat([menu_raw, pred_tags_df], axis=1)

# Save to CSV
#menu_full.to_csv('/content/drive/MyDrive/DataSets02-ClassificationModel/Post/Model-evaluation-testing/menu_data_predicted01.csv', index=False)
menu_full.to_csv('data/Post/menu_data_predicted01.csv', index=False)

print("✅ Predictions complete. menu_data_predicted01.csv is ready.")
