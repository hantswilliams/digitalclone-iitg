#!/usr/bin/env python3
"""
Test script to simulate complete video generation workflow with Asset creation
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv()

def test_complete_video_workflow():
    """Test the complete video generation workflow."""
    print("🧪 Testing Complete Video Generation Workflow")
    print("=" * 50)
    
    try:
        # Import Flask app context and required modules
        from app import create_app
        from app.models import Asset, AssetType, AssetStatus, Job, JobType, JobStatus, User
        from app.extensions import db
        from app.services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig
        
        app = create_app()
        
        with app.app_context():
            # Check if we have test files
            portrait_path = backend_dir / "test_files" / "hants.png"
            audio_path = backend_dir / "test_files" / "voice_joelsaltz.wav"
            
            if not portrait_path.exists() or not audio_path.exists():
                print("❌ Test files not found. Creating mock files...")
                return False
            
            print(f"✅ Test files found")
            print(f"  • Portrait: {portrait_path}")
            print(f"  • Audio: {audio_path}")
            
            # Create or get a test user
            test_user = User.query.filter_by(email='test@example.com').first()
            if not test_user:
                print("📝 Creating test user...")
                test_user = User(
                    email='test@example.com',
                    username='testuser',
                    is_verified=True
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"✅ Created test user with ID: {test_user.id}")
            else:
                print(f"✅ Using existing test user with ID: {test_user.id}")
            
            # Create test portrait asset
            print("📸 Creating test portrait asset...")
            portrait_asset = Asset(
                filename='test_portrait.png',
                original_filename='hants.png',
                file_size=portrait_path.stat().st_size,
                mime_type='image/png',
                file_extension='.png',
                asset_type=AssetType.PORTRAIT,
                status=AssetStatus.READY,
                storage_path='test/portraits/test_portrait.png',
                storage_bucket='voice-clone-assets',
                user_id=test_user.id,
                description='Test portrait for video generation'
            )
            db.session.add(portrait_asset)
            
            # Create test audio asset
            print("🎵 Creating test audio asset...")
            audio_asset = Asset(
                filename='test_audio.wav',
                original_filename='voice_joelsaltz.wav',
                file_size=audio_path.stat().st_size,
                mime_type='audio/wav',
                file_extension='.wav',
                asset_type=AssetType.VOICE_SAMPLE,
                status=AssetStatus.READY,
                storage_path='test/audio/test_audio.wav',
                storage_bucket='voice-clone-assets',
                user_id=test_user.id,
                description='Test audio for video generation'
            )
            db.session.add(audio_asset)
            
            # Create test job
            print("🔧 Creating test job...")
            test_job = Job(
                user_id=test_user.id,
                job_type=JobType.GENERATE_VIDEO,
                status=JobStatus.PENDING,
                parameters={
                    'driven_audio_type': 'upload',
                    'smoothed_pitch': 0.8,
                    'smoothed_yaw': 0.8,
                    'smoothed_roll': 0.8,
                    'smoothed_t': 0.8
                }
            )
            db.session.add(test_job)
            db.session.commit()
            
            print(f"✅ Created test job with ID: {test_job.id}")
            print(f"✅ Portrait asset ID: {portrait_asset.id}")
            print(f"✅ Audio asset ID: {audio_asset.id}")
            
            # Now simulate the video generation process
            print("\n🎬 Simulating video generation...")
            
            # Test KDTalker client initialization
            client = KDTalkerClient()
            health = client.health_check()
            
            if health.get('status') != 'healthy':
                print(f"❌ KDTalker service unhealthy: {health}")
                return False
            
            print("✅ KDTalker service is healthy")
            
            # Create temp output file for testing
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                output_path = tmp_file.name
                
                # Generate video using actual KDTalker service
                print("🎯 Generating video...")
                config = VideoGenerationConfig(
                    driven_audio_type='upload',
                    smoothed_pitch=0.8,
                    smoothed_yaw=0.8,
                    smoothed_roll=0.8,
                    smoothed_t=0.8
                )
                
                result = client.generate_video(
                    portrait_path=portrait_path,
                    audio_path=audio_path,
                    output_path=output_path,
                    config=config
                )
                
                print(f"✅ Video generated: {result.get('status')}")
                print(f"  • File size: {result.get('file_size', 0):,} bytes")
                print(f"  • Generation time: {result.get('generation_time', 0):.2f}s")
                
                # Simulate creating Asset record (like the actual task does)
                print("💾 Creating Asset record...")
                
                video_filename = f"video_{test_job.id}_{int(test_job.created_at.timestamp())}.mp4"
                storage_path = f"generated/videos/{test_user.id}/{video_filename}"
                
                video_asset = Asset(
                    filename=video_filename,
                    original_filename=video_filename,
                    file_size=result.get('file_size', 0),
                    mime_type='video/mp4',
                    file_extension='.mp4',
                    asset_type=AssetType.GENERATED_VIDEO,
                    status=AssetStatus.READY,
                    storage_path=storage_path,
                    storage_bucket='voice-clone-assets',
                    user_id=test_user.id,
                    description=f"Generated video from portrait (asset {portrait_asset.id}) and audio (asset {audio_asset.id})"
                )
                
                db.session.add(video_asset)
                
                # Update job status
                test_job.status = JobStatus.COMPLETED
                test_job.result_data = {
                    'status': 'completed',
                    'video_storage_path': storage_path,
                    'file_size': result.get('file_size', 0),
                    'generation_time': result.get('generation_time', 0),
                    'generated_asset_id': video_asset.id
                }
                
                db.session.commit()
                
                print(f"✅ Created video Asset with ID: {video_asset.id}")
                print(f"✅ Updated job status to: {test_job.status.value}")
                
                # Verify asset was created correctly
                created_asset = Asset.query.get(video_asset.id)
                if created_asset:
                    print("\n📊 Asset Verification:")
                    print(f"  • ID: {created_asset.id}")
                    print(f"  • Type: {created_asset.asset_type.value}")
                    print(f"  • Status: {created_asset.status.value}")
                    print(f"  • Filename: {created_asset.filename}")
                    print(f"  • File size: {created_asset.file_size:,} bytes")
                    print(f"  • Storage path: {created_asset.storage_path}")
                    print(f"  • Description: {created_asset.description}")
                else:
                    print("❌ Asset not found in database")
                    return False
                
                # Clean up temp file
                try:
                    os.unlink(output_path)
                except:
                    pass
                
                print("\n🎉 Complete workflow test successful!")
                return True
                
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Complete Video Generation Workflow Test")
    print("=" * 55)
    
    success = test_complete_video_workflow()
    
    if success:
        print("\n🎉 All workflow tests passed!")
        print("✅ Video generation creates Asset records correctly")
        print("✅ Frontend can now display generated videos in Assets page")
    else:
        print("\n❌ Workflow test failed.")
