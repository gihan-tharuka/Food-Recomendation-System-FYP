-- Add role field to users table
USE food_recommendation_db;

-- Add role column to users table
ALTER TABLE users ADD COLUMN role ENUM('customer', 'staff') DEFAULT 'customer';

-- Create index for role field
CREATE INDEX idx_role ON users(role);

-- Update existing users to have customer role by default
UPDATE users SET role = 'customer' WHERE role IS NULL;

-- Create a staff user for testing (optional)
-- INSERT INTO users (user_id, name, email, password_hash, role) 
-- VALUES ('staff001', 'Restaurant Staff', 'staff@restaurant.com', '$2b$12$example_hash', 'staff');

-- Show updated table structure
DESCRIBE users;
