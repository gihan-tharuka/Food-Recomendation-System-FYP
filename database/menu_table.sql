-- Menu table for storing menu items with predictions
USE food_recommendation_db;

-- Drop existing table if it exists
DROP TABLE IF EXISTS menu_items;

-- Create menu items table with simplified columns
CREATE TABLE IF NOT EXISTS menu_items (
    item_id INT PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    cuisine VARCHAR(100),
    category VARCHAR(100),
    
    -- Context tags (only the ones you requested)
    is_morning BOOLEAN DEFAULT FALSE,
    is_afternoon BOOLEAN DEFAULT FALSE,
    is_evening BOOLEAN DEFAULT FALSE,
    is_sunny BOOLEAN DEFAULT FALSE,
    is_rainy BOOLEAN DEFAULT FALSE,
    
    -- Indexes for better performance
    INDEX idx_item_name (item_name),
    INDEX idx_cuisine (cuisine),
    INDEX idx_category (category),
    INDEX idx_price (price)
);

-- Show the table structure
DESCRIBE menu_items;
