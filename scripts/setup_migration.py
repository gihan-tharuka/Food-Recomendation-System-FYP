#!/usr/bin/env python3
"""
Setup script to migrate from old structure to new structure
"""

import shutil
import os
from pathlib import Path

def migrate_old_files():
    """Migrate old files to new structure"""
    project_root = Path(__file__).parent
    
    print("🔄 Migrating project structure...")
    
    # Create backup of old files
    backup_dir = project_root / "backup_old_structure"
    backup_dir.mkdir(exist_ok=True)
    
    old_files = {
        'trainer.py': 'src/models/trainer_old.py',
        'recommender.py': 'src/models/recommender_old.py', 
        'prediction_step.py': 'src/models/predictor_old.py'
    }
    
    # Backup old files
    for old_file, backup_path in old_files.items():
        old_path = project_root / old_file
        backup_full_path = backup_dir / backup_path
        backup_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if old_path.exists():
            print(f"📦 Backing up {old_file} to {backup_path}")
            shutil.copy2(old_path, backup_full_path)
    
    print("✅ Migration completed!")
    print("\n📋 Next steps:")
    print("1. Review the new structure in src/")
    print("2. Run: python main.py")
    print("3. Use 'train' command to retrain models with new structure")
    print("4. Test the new recommendation system")
    print("\n⚠️  Old files backed up to backup_old_structure/")

if __name__ == "__main__":
    migrate_old_files()
