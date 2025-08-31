import pandas as pd

# Load the menu data
df = pd.read_csv('data/DB/SpiciaMenu.csv')

# Analyze cuisine-category distribution
cuisine_categories = df.groupby('cuisine')['category'].unique()

print('Cuisine Categories Analysis:')
print('='*60)

all_categories = set()
international_categories = set()

for cuisine, categories in cuisine_categories.items():
    categories_list = sorted(list(categories))
    print(f'{cuisine}: {categories_list} ({len(categories_list)} categories)')
    
    all_categories.update(categories_list)
    if cuisine == 'International':
        international_categories.update(categories_list)

print('\n' + '='*60)
print(f'All unique categories: {sorted(list(all_categories))}')
print(f'International categories: {sorted(list(international_categories))}')

print('\n' + '='*60)
print('Cuisines with limited categories (<=3):')
for cuisine, categories in cuisine_categories.items():
    if len(categories) <= 3:
        missing_from_international = international_categories - set(categories)
        print(f'{cuisine}: {sorted(list(categories))} - Missing from International: {sorted(list(missing_from_international))}')
