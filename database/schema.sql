-- Food Recommendation System Database Schema
-- MySQL Database Setup for XAMPP

-- Create database
CREATE DATABASE IF NOT EXISTS food_recommendation_db;
USE food_recommendation_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for better performance
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Create ratings table
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id INT NOT NULL,
    rating DECIMAL(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate ratings for same user-item pair
    UNIQUE KEY unique_user_item (user_id, item_id),
    
    -- Indexes for better performance
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_rating (rating),
    INDEX idx_date (date)
);

-- Sample data insertion (optional)
-- INSERT INTO users (user_id, name, email) VALUES 
-- ('sample001', 'Sample User', 'sample@example.com');

-- INSERT INTO ratings (user_id, item_id, rating, date) VALUES 
-- ('sample001', 1, 4.5, '2025-08-14');

-- Show tables
SHOW TABLES;

-- Show table structures
DESCRIBE users;
DESCRIBE ratings;
