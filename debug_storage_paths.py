#!/usr/bin/env python3
"""Debug script to check asset storage paths"""

import sys
import os
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from app import create_app
from app.models import Asset, AssetType, AssetStatus

def debug_storage_paths():
    app = create_app()
    
    with app.app_context():
        # Check portrait asset 57 and voice asset 61
        portrait_asset = Asset.query.get(57)
        voice_asset = Asset.query.get(61)
        
        print("=== ASSET STORAGE PATHS ===")
        if portrait_asset:
            print(f"Portrait Asset 57:")
            print(f"  - storage_path: {portrait_asset.storage_path}")
            print(f"  - filename: {portrait_asset.filename}")
            print()
        
        if voice_asset:
            print(f"Voice Asset 61:")
            print(f"  - storage_path: {voice_asset.storage_path}")
            print(f"  - filename: {voice_asset.filename}")
            print()

if __name__ == "__main__":
    debug_storage_paths()
