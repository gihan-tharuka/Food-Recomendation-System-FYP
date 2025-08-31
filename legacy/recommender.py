import pandas as pd
import os
import datetime
from uuid import uuid4


# --- Configuration ---
#MENU_CSV = '/content/drive/MyDrive/DataSets02/Post/menu_data_augmented19.csv'
# MENU_CSV = '/content/drive/MyDrive/DataSets02/Pre/labeled_menu.csv'
# RATINGS_CSV = '/content/drive/MyDrive/DataSets01/Version01/ratings.csv'
# USERS_CSV = '/content/drive/MyDrive/DataSets01/Version01/users.csv'
MENU_CSV = 'data/Pre/labeled_menu.csv'
RATINGS_CSV = 'data/DB/ratings.csv'
USERS_CSV = 'data/DB/users.csv'

# --- Step 1: Load Menu Data ---
menu = pd.read_csv(MENU_CSV)

# --- Step 2: Load or create Users Data ---
if os.path.exists(USERS_CSV):
    users_df = pd.read_csv(USERS_CSV)
else:
    users_df = pd.DataFrame(columns=['user_id', 'name', 'email'])

# --- Step 3: User registration or login ---
user_id = input("Enter your User ID (or leave blank to register): ").strip()

if not user_id:
    new_user_id = str(uuid4())
    name = input("Enter your name: ").strip()
    email = input("Enter your email: ").strip()
    new_user = {'user_id': new_user_id, 'name': name, 'email': email}
    users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
    users_df.to_csv(USERS_CSV, index=False)
    print(f"User registered. Your User ID is: {new_user_id}")
    user_id = new_user_id
else:
    if user_id not in users_df['user_id'].values:
        print("User ID not found. Registering a new user.")
        name = input("Enter your name: ").strip()
        email = input("Enter your email: ").strip()
        new_user = {'user_id': user_id, 'name': name, 'email': email}
        users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
        users_df.to_csv(USERS_CSV, index=False)
        print(f"User registered with ID: {user_id}")

# --- Step 4: Load ratings ---
if os.path.exists(RATINGS_CSV):
    ratings_df = pd.read_csv(RATINGS_CSV)
else:
    ratings_df = pd.DataFrame(columns=['user_id', 'item_id', 'rating', 'date'])

user_ratings_df = ratings_df[ratings_df['user_id'] == user_id]
user_ratings = dict(zip(user_ratings_df['item_id'], user_ratings_df['rating']))

# --- Step 5: User Preferences ---
print("\n--- User Preferences Setup ---")
try:
    total_budget = float(input("Enter your total budget (e.g., 50): ").strip())
except ValueError:
    total_budget = 50.0
    print("Invalid input. Using default budget: $50")

preferred_cuisine = input("Enter your preferred cuisine (e.g., Japanese): ").strip().title()

user_categories_input = input("Enter categories you want (comma-separated, e.g., food,drink,dessert): ").strip().lower()
user_categories = [cat.strip() for cat in user_categories_input.split(',') if cat.strip()]

category_priority_input = input("Enter category priority (comma-separated in order of importance): ").strip().lower()
category_priority = [cat.strip() for cat in category_priority_input.split(',') if cat.strip()]

require_each_input = input("Do you want at least one item from each category? (yes/no): ").strip().lower()
require_each_category = require_each_input in ['yes', 'y']

# --- Step 6: Context Input ---
print("\n--- Context Input ---")
current_time = input("Enter current time of day (morning/afternoon/evening): ").strip().lower()
if current_time not in ['morning', 'afternoon', 'evening']:
    print("Invalid input. Defaulting to 'morning'")
    current_time = 'morning'
time_col = f'is_{current_time}'

current_weather = input("Enter current weather (sunny/rainy/cold/hot): ").strip().lower()
if current_weather not in ['sunny', 'rainy', 'cold', 'hot']:
    print("Invalid input. Defaulting to 'sunny'")
    current_weather = 'sunny'
weather_col = f'is_{current_weather}'

# --- Step 7: Filter Menu ---
filtered_menu = menu[
    (menu['cuisine'].str.lower() == preferred_cuisine.lower()) &
    (menu['category'].isin(user_categories))
]

# --- Step 8: Utility Calculation + XAI ---
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

    base_weight = priority_weights.get(category, 1)
    context_weight = contextual_boost if row.get(time_col, False) else 1.0
    weather_weight = weather_boost if row.get(weather_col, False) else 1.0
    rating = user_ratings.get(item_id)
    rating_weight = rating / max_rating if rating else 1.0

    value = price * base_weight * context_weight * weather_weight * rating_weight

    # Build Explanation
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

    items.append((price, value, item_id, item_name, category))

# --- Step 9: Select 1 Item per Category if Required ---
preselected = []
remaining_items = items.copy()
remaining_budget = total_budget

if require_each_category:
    for cat in user_categories:
        cat_items = [item for item in items if item[4] == cat]
        if cat_items:
            cheapest = min(cat_items, key=lambda x: x[0])
            if cheapest not in preselected:
                preselected.append(cheapest)
                remaining_budget -= cheapest[0]
                remaining_items.remove(cheapest)

# --- Step 10: Knapsack Algorithm ---
def knapsack(items, budget):
    n = len(items)
    dp = [[0]*(int(budget)+1) for _ in range(n+1)]
    for i in range(1, n+1):
        price, value, *_ = items[i-1]
        price = int(price)
        for w in range(int(budget)+1):
            if price <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w-price] + value)
            else:
                dp[i][w] = dp[i-1][w]
    w = int(budget)
    selected = []
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(items[i-1])
            w -= int(items[i-1][0])
    selected.reverse()
    return selected

selected_items = knapsack(remaining_items, remaining_budget)

# --- Step 11: Combine Final Selection ---
final_selection = preselected + selected_items

# --- Step 12: Print Recommendations w/ Explanations ---
total_cost = sum(item[0] for item in final_selection)
recommendations = {}
recommended_ids = []

print(f"\nUser Preferences:")
print(f"  User ID: {user_id}")
print(f"  Budget: ${total_budget}")
print(f"  Preferred cuisine: {preferred_cuisine}")
print(f"  Selected categories: {user_categories}")
print(f"  Category priority: {category_priority}")
print(f"  Require one per category: {require_each_category}")
print(f"  Time of Day: {current_time}")
print(f"  Weather: {current_weather}")

print(f"\n--- Recommended Items (Total Cost: ${total_cost:.2f}) ---")

for cat in category_priority:
    cat_items = [item for item in final_selection if item[4] == cat]
    if cat_items:
        print(f"\n{cat.capitalize()}:")
        for price, _, item_id, name, category in cat_items:
            print(f"  - {name} (${price:.2f})")
            print(f"    Why?: {explanations.get(item_id, 'No reasons available')}")
            recommended_ids.append(item_id)

# --- Step 13: Ratings ---
print("\nPlease rate the recommended items (1-5; press Enter to skip):")
today = datetime.datetime.now().strftime("%Y-%m-%d")
new_ratings = []

for item_id in recommended_ids:
    item_name = menu.loc[menu['item_id'] == item_id, 'item_name'].values[0]
    rating_input = input(f"Rate '{item_name}': ").strip()
    if rating_input.isdigit():
        rating = int(rating_input)
        if 1 <= rating <= 5:
            new_ratings.append({
                'user_id': user_id,
                'item_id': item_id,
                'rating': rating,
                'date': today
            })

# --- Step 14: Save Ratings ---
if new_ratings:
    new_ratings_df = pd.DataFrame(new_ratings)
    ratings_df = pd.concat([ratings_df, new_ratings_df], ignore_index=True)
    ratings_df.drop_duplicates(subset=['user_id', 'item_id'], keep='last', inplace=True)
    ratings_df.to_csv(RATINGS_CSV, index=False)
    print("\n✅ Your ratings have been saved. Thank you!")
else:
    print("\nNo ratings were provided.")
print("\nThank you for using the Recommender System! Goodbye!")