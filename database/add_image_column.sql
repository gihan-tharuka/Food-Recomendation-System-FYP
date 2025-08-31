-- Add image_url column to menu_items table
ALTER TABLE menu_items ADD COLUMN image_url VARCHAR(500) DEFAULT NULL;
