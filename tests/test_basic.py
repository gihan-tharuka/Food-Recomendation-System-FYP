# Test utilities
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDataLoader(unittest.TestCase):
    """Test cases for DataLoader class"""
    
    def setUp(self):
        from src.data.data_loader import DataLoader
        self.data_loader = DataLoader()
    
    def test_load_menu_data(self):
        """Test loading menu data"""
        try:
            data = self.data_loader.load_menu_data()
            self.assertIsNotNone(data)
            self.assertIn('item_name', data.columns)
            self.assertIn('price', data.columns)
        except FileNotFoundError:
            self.skipTest("Menu data file not found")
    
    def test_load_users_data(self):
        """Test loading users data"""
        data = self.data_loader.load_users_data()
        self.assertIsNotNone(data)
        expected_columns = ['user_id', 'name', 'email']
        for col in expected_columns:
            self.assertIn(col, data.columns)

class TestModelTrainer(unittest.TestCase):
    """Test cases for ModelTrainer class"""
    
    def setUp(self):
        from src.models.trainer import ModelTrainer
        self.trainer = ModelTrainer()
    
    def test_preprocessor_creation(self):
        """Test preprocessor creation"""
        preprocessor = self.trainer._create_preprocessor()
        self.assertIsNotNone(preprocessor)

if __name__ == '__main__':
    unittest.main()
