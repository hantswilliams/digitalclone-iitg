#!/usr/bin/env python3
"""
Test the video generation task directly
"""
import sys
import os
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from dotenv import load_dotenv
load_dotenv()

# Set up Flask app context
from app import create_app
app = create_app()

def test_video_generation_task():
    """Test video generation task components"""
    print("🧪 Testing video generation task components...")
    
    with app.app_context():
        # Test 1: Import components
        print("\n1. Testing imports...")
        try:
            from app.tasks.video_tasks import generate_video
            from app.services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig
            from app.models import Job, Asset, User, JobStatus, AssetType, AssetStatus
            from app.extensions import db
            print("✅ All imports successful")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return
        
        # Test 2: Check KDTalker client
        print("\n2. Testing KDTalker client directly...")
        try:
            client = KDTalkerClient()
            health = client.health_check()
            print(f"Health: {health['status']}")
            if health['status'] != 'healthy':
                print(f"❌ KDTalker not healthy: {health}")
                return
            print("✅ KDTalker client healthy")
        except Exception as e:
            print(f"❌ KDTalker client error: {e}")
            return
        
        # Test 3: Check database models
        print("\n3. Testing database models...")
        try:
            # Check if we have test assets
            portrait_assets = Asset.query.filter_by(asset_type=AssetType.PORTRAIT).first()
            audio_assets = Asset.query.filter_by(asset_type=AssetType.VOICE_SAMPLE).first()
            
            print(f"Portrait assets available: {Asset.query.filter_by(asset_type=AssetType.PORTRAIT).count()}")
            print(f"Audio assets available: {Asset.query.filter_by(asset_type=AssetType.VOICE_SAMPLE).count()}")
            print(f"Generated audio assets available: {Asset.query.filter_by(asset_type=AssetType.GENERATED_AUDIO).count()}")
            print(f"Generated video assets available: {Asset.query.filter_by(asset_type=AssetType.GENERATED_VIDEO).count()}")
            
            if portrait_assets:
                print(f"Sample portrait: {portrait_assets.filename} (status: {portrait_assets.status})")
            if audio_assets:
                print(f"Sample audio: {audio_assets.filename} (status: {audio_assets.status})")
                
            print("✅ Database models accessible")
        except Exception as e:
            print(f"❌ Database model error: {e}")
            return
        
        # Test 4: Check video generation config
        print("\n4. Testing video generation config...")
        try:
            config = VideoGenerationConfig()
            print(f"Default config: driven_audio_type={config.driven_audio_type}, smoothed_pitch={config.smoothed_pitch}")
            
            # Test custom config
            custom_config = VideoGenerationConfig(
                driven_audio_type="upload",
                smoothed_pitch=0.9,
                smoothed_yaw=0.7,
                smoothed_roll=0.8,
                smoothed_t=0.6
            )
            print(f"Custom config: {custom_config.driven_audio_type}, {custom_config.smoothed_pitch}")
            print("✅ Video generation config working")
        except Exception as e:
            print(f"❌ Config error: {e}")
            return
        
        print("\n✅ All video generation task components are working correctly")
        print("\nThe KDTalker implementation appears to be working. What specific error are you seeing?")

if __name__ == "__main__":
    test_video_generation_task()
