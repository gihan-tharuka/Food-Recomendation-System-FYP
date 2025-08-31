-- Add comment column to ratings table
USE food_recommendation_db;

-- Add comment column to ratings table
ALTER TABLE ratings ADD COLUMN comment TEXT DEFAULT NULL;

-- Show the updated table structure
DESCRIBE ratings;
