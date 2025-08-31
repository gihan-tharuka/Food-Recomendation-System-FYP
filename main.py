#!/usr/bin/env python3
"""
Main entry point for the Food Recommendation System
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.trainer import ModelTrainer
from src.models.predictor import ModelPredictor
from src.utils.helpers import validate_data_files, create_directory_structure, get_model_info

def main():
    """Main application entry point"""
    print("🍽️  Food Recommendation System")
    print("=" * 50)
    
    try:
        # Create directory structure
        create_directory_structure()
        
        # Validate data files
        validate_data_files()
        
        print("\n📊 Available commands:")
        print("1. train - Train all models")
        print("2. predict - Generate predictions for menu items")
        print("3. recommend - Start recommendation engine")
        print("4. info - Show model information")
        print("5. exit - Exit application")
        
        while True:
            command = input("\n🔤 Enter command: ").strip().lower()
            
            if command == "train":
                print("\n🔄 Training models...")
                trainer = ModelTrainer()
                trainer.train_all_models()
                
            elif command == "predict":
                print("\n🔮 Generating predictions...")
                predictor = ModelPredictor()
                results = predictor.predict_and_save()
                print(f"✅ Processed {len(results)} menu items")
                
            elif command == "recommend":
                print("\n🎯 Starting recommendation engine...")
                from src.models.recommender import run_recommender_system
                run_recommender_system()
                
            elif command == "info":
                print("\n📋 Model Information:")
                model_info = get_model_info()
                for name, info in model_info.items():
                    status = "✅ Exists" if info['exists'] else "❌ Missing"
                    size = f"{info['size']} bytes" if info['exists'] else "N/A"
                    print(f"  {name.capitalize()}: {status} ({size})")
                    
            elif command == "exit":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid command. Please try again.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
