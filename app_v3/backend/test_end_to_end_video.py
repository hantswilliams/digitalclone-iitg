#!/usr/bin/env python3
"""
End-to-end test of video generation through API
"""
import sys
import os
import time
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from dotenv import load_dotenv
load_dotenv()

# Set up Flask app context
from app import create_app
app = create_app()

def test_end_to_end_video_generation():
    """Test complete video generation workflow through API"""
    
    print("🧪 Testing end-to-end video generation workflow...")
    
    with app.app_context():
        from app.models import Asset, User, Job, AssetType, AssetStatus
        from app.extensions import db
        from app.tasks.video_tasks import generate_video
        
        # Find available assets
        print("\n1. Finding available assets...")
        
        # Find a ready portrait asset
        portrait_asset = Asset.query.filter_by(
            asset_type=AssetType.PORTRAIT,
            status=AssetStatus.READY
        ).first()
        
        # Find a ready audio asset  
        audio_asset = Asset.query.filter_by(
            asset_type=AssetType.VOICE_SAMPLE,
            status=AssetStatus.READY
        ).first()
        
        if not portrait_asset:
            print("❌ No ready portrait assets found")
            return
        if not audio_asset:
            print("❌ No ready audio assets found")
            return
            
        print(f"✅ Found portrait asset: {portrait_asset.filename} (ID: {portrait_asset.id})")
        print(f"✅ Found audio asset: {audio_asset.filename} (ID: {audio_asset.id})")
        
        # Create a test job
        print("\n2. Creating test job...")
        from app.models.job import JobType, JobStatus, JobPriority
        
        test_job = Job(
            title="End-to-end Video Generation Test",
            user_id=portrait_asset.user_id,
            job_type=JobType.VIDEO_GENERATION,
            status=JobStatus.PENDING,
            priority=JobPriority.NORMAL,
            parameters={
                'portrait_asset_id': portrait_asset.id,
                'audio_asset_id': audio_asset.id,
                'driven_audio_type': 'upload',
                'smoothed_pitch': 0.8,
                'smoothed_yaw': 0.8,
                'smoothed_roll': 0.8,
                'smoothed_t': 0.8
            }
        )
        
        db.session.add(test_job)
        db.session.commit()
        
        print(f"✅ Created test job: ID {test_job.id}")
        
        # Test the video generation task
        print("\n3. Testing video generation task...")
        try:
            # Call the task directly (synchronously for testing)
            result = generate_video(test_job.id, portrait_asset.id, audio_asset.id)
            
            print("✅ Video generation completed successfully!")
            print(f"Result: {result}")
            
            # Check if Asset was created
            generated_asset_id = result.get('generated_asset_id')
            if generated_asset_id:
                generated_asset = Asset.query.get(generated_asset_id)
                if generated_asset:
                    print(f"✅ Generated video asset created: {generated_asset.filename} (ID: {generated_asset.id})")
                    print(f"   Storage path: {generated_asset.storage_path}")
                    print(f"   File size: {generated_asset.file_size:,} bytes")
                    print(f"   Status: {generated_asset.status}")
                else:
                    print("❌ Generated asset not found in database")
            else:
                print("❌ No generated_asset_id in result")
                
        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_end_to_end_video_generation()
