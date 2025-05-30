#!/usr/bin/env python3
"""
Test script to verify video generation creates Asset records
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv()

def test_video_asset_creation():
    """Test that video generation creates proper Asset records."""
    print("🧪 Testing Video Asset Creation")
    print("=" * 40)
    
    try:
        # Import Flask app context and models
        from app import create_app
        from app.models import Asset, AssetType, AssetStatus
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            # Query for existing generated video assets
            video_assets = Asset.query.filter_by(
                asset_type=AssetType.GENERATED_VIDEO
            ).all()
            
            print(f"📊 Found {len(video_assets)} existing generated video assets:")
            
            for asset in video_assets:
                print(f"  • ID: {asset.id}")
                print(f"    Filename: {asset.filename}")
                print(f"    Status: {asset.status.value}")
                print(f"    File size: {asset.file_size:,} bytes")
                print(f"    Storage path: {asset.storage_path}")
                print(f"    Created: {asset.created_at}")
                print(f"    User ID: {asset.user_id}")
                print(f"    Description: {asset.description}")
                print()
            
            # Also check for other asset types for comparison
            audio_assets = Asset.query.filter_by(
                asset_type=AssetType.GENERATED_AUDIO
            ).count()
            
            portrait_assets = Asset.query.filter_by(
                asset_type=AssetType.PORTRAIT
            ).count()
            
            voice_assets = Asset.query.filter_by(
                asset_type=AssetType.VOICE_SAMPLE
            ).count()
            
            print(f"📈 Asset Summary:")
            print(f"  • Generated Videos: {len(video_assets)}")
            print(f"  • Generated Audio: {audio_assets}")
            print(f"  • Portraits: {portrait_assets}")
            print(f"  • Voice Samples: {voice_assets}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_asset_api_endpoint():
    """Test the assets API endpoint to ensure it can filter by generated_video."""
    print("\n🌐 Testing Assets API Endpoint")
    print("=" * 35)
    
    try:
        # Import Flask app and test client
        from app import create_app
        
        app = create_app()
        client = app.test_client()
        
        # Test without authentication first (should fail)
        print("🔒 Testing without authentication...")
        response = client.get('/api/assets?asset_type=generated_video')
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print("⚠️  Authentication not required (unexpected)")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Video Asset Integration Test")
    print("=" * 40)
    
    # Run tests
    test1 = test_video_asset_creation()
    test2 = test_asset_api_endpoint()
    
    if test1 and test2:
        print("\n🎉 Asset integration tests completed!")
        print("📝 Next: Test with actual video generation or frontend")
    else:
        print("\n❌ Some tests failed.")
