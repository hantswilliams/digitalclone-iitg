#!/usr/bin/env python3
"""
Test video generation core logic without Celery
"""
import sys
import os
import tempfile
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from dotenv import load_dotenv
load_dotenv()

# Set up Flask app context
from app import create_app
app = create_app()

def test_video_generation_core_logic():
    """Test video generation core logic without Celery task overhead"""
    
    print("🧪 Testing video generation core logic...")
    
    with app.app_context():
        from app.models import Asset, User, Job, AssetType, AssetStatus
        from app.services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig
        from app.services.storage import storage_service
        from app.extensions import db
        from pathlib import Path
        
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
        
        # Test KDTalker client health
        print("\n2. Testing KDTalker client...")
        
        kdtalker_client = KDTalkerClient()
        health_check = kdtalker_client.health_check()
        
        if health_check['status'] != 'healthy':
            print(f"❌ KDTalker service unavailable: {health_check}")
            return
            
        print(f"✅ KDTalker service healthy: {health_check['response_time_ms']:.1f}ms")
        
        # Download assets for testing
        print("\n3. Downloading assets...")
        
        temp_dir = Path(f"/tmp/video_test_{os.getpid()}")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Download portrait image
            portrait_local_path = temp_dir / f"portrait_{portrait_asset.id}{Path(portrait_asset.filename).suffix}"
            storage_service.download_file(
                portrait_asset.storage_path,
                str(portrait_local_path)
            )
            print(f"✅ Downloaded portrait: {portrait_local_path}")
            
            # Download audio file
            audio_local_path = temp_dir / f"audio_{audio_asset.id}{Path(audio_asset.filename).suffix}"
            storage_service.download_file(
                audio_asset.storage_path,
                str(audio_local_path)
            )
            print(f"✅ Downloaded audio: {audio_local_path}")
            
            # Test video generation
            print("\n4. Testing video generation...")
            
            config = VideoGenerationConfig(
                driven_audio_type='upload',
                smoothed_pitch=0.8,
                smoothed_yaw=0.8,
                smoothed_roll=0.8,
                smoothed_t=0.8
            )
            
            # Generate output path
            output_filename = f"test_video_{os.getpid()}.mp4"
            output_local_path = temp_dir / output_filename
            
            # Generate video using KDTalker
            print("   Calling KDTalker...")
            generation_result = kdtalker_client.generate_video(
                portrait_path=portrait_local_path,
                audio_path=audio_local_path,
                output_path=output_local_path,
                config=config
            )
            
            print("✅ Video generation successful!")
            print(f"   Generation time: {generation_result.get('generation_time', 0):.2f} seconds")
            print(f"   File size: {generation_result.get('file_size', 0):,} bytes")
            print(f"   Output path: {generation_result.get('video_path')}")
            
            # Test storage upload
            print("\n5. Testing storage upload...")
            
            storage_path = f"test/videos/{audio_asset.user_id}/{output_filename}"
            upload_result = storage_service.upload_file(
                str(output_local_path),
                storage_path,
                content_type="video/mp4"
            )
            
            if upload_result.get('success'):
                print(f"✅ Video uploaded to storage: {storage_path}")
                
                # Test asset creation
                print("\n6. Testing asset creation...")
                
                video_file_size = Path(output_local_path).stat().st_size
                
                asset = Asset(
                    filename=output_filename,
                    original_filename=output_filename,
                    file_size=video_file_size,
                    mime_type='video/mp4',
                    file_extension='.mp4',
                    asset_type=AssetType.GENERATED_VIDEO,
                    status=AssetStatus.READY,
                    storage_path=storage_path,
                    storage_bucket=app.config.get('MINIO_BUCKET_NAME', 'voice-clone-assets'),
                    user_id=audio_asset.user_id,
                    description=f"Test generated video from portrait (asset {portrait_asset.id}) and audio (asset {audio_asset.id})"
                )
                
                db.session.add(asset)
                db.session.commit()
                
                print(f"✅ Asset created successfully: ID {asset.id}")
                print(f"   Filename: {asset.filename}")
                print(f"   Storage path: {asset.storage_path}")
                print(f"   File size: {asset.file_size:,} bytes")
                print(f"   Asset type: {asset.asset_type}")
                print(f"   Status: {asset.status}")
                
                print("\n🎉 Complete video generation workflow test successful!")
                
            else:
                print(f"❌ Storage upload failed: {upload_result}")
                
        finally:
            # Clean up temp files
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"\n🧹 Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temp directory: {e}")

if __name__ == "__main__":
    test_video_generation_core_logic()
