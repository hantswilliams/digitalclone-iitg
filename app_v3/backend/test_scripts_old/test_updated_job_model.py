#!/usr/bin/env python3
"""
Test script to verify the updated Job model with service_metadata and timing fields
"""
import os
import sys
from datetime import datetime
import json

# Add the backend directory to the Python path
backend_dir = os.path.dirname(__file__)
app_dir = os.path.join(backend_dir, '..', 'app')
sys.path.insert(0, os.path.join(backend_dir, '..'))

from app import create_app
from app.extensions import db
from app.models import User, Job, JobType, JobStatus

def test_updated_job_model():
    """Test the updated Job model with new fields"""
    print("🧪 Testing updated Job model...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get the admin user
            admin_user = User.query.filter_by(email="admin@voiceclone.edu").first()
            if not admin_user:
                print("❌ Admin user not found!")
                return False
            
            # Create sample service metadata (simulating HuggingFace metadata)
            sample_metadata = {
                "indextts": {
                    "model_name": "amphion/text_to_speech",
                    "model_type": "TTS",
                    "huggingface_url": "https://huggingface.co/amphion/text_to_speech",
                    "library_name": "transformers",
                    "pipeline_tag": "text-to-speech",
                    "language": ["en"],
                    "license": "mit",
                    "tags": ["tts", "speech-synthesis"],
                    "model_size": "1.2GB",
                    "supported_formats": ["wav", "mp3"],
                    "sample_rate": 22050,
                    "created_at": datetime.now().isoformat()
                },
                "kdtalker": {
                    "model_name": "KDTalker/KDTalker",
                    "model_type": "Video Generation",
                    "huggingface_url": "https://huggingface.co/KDTalker/KDTalker",
                    "library_name": "diffusers",
                    "pipeline_tag": "video-generation",
                    "language": ["en"],
                    "license": "apache-2.0",
                    "tags": ["video-generation", "talking-head", "avatar"],
                    "model_size": "3.4GB",
                    "supported_formats": ["mp4", "avi"],
                    "fps": 25,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            # Create a new job with metadata
            print("📝 Creating test job...")
            job = Job(
                title="Test Video Generation with Metadata",
                job_type=JobType.FULL_PIPELINE,
                user_id=admin_user.id,
                description="Testing job with service metadata and timing fields",
                parameters={
                    "text": "Hello, this is a test video generation.",
                    "voice_file": "test_voice.wav",
                    "image_file": "test_image.jpg"
                }
            )
            
            # Add the job to get an ID
            db.session.add(job)
            db.session.flush()
            
            # Test the new service metadata functionality
            print("🔧 Adding service metadata...")
            job.update_service_metadata(sample_metadata)
            
            # Simulate job processing with timing
            print("⏱️  Simulating job processing...")
            job.mark_started()
            db.session.commit()
            
            # Simulate some processing time
            import time
            time.sleep(0.1)  # Small delay to simulate processing
            
            # Mark as completed with results
            results = {
                "output_video_path": "test_output.mp4",
                "processing_steps": ["voice_synthesis", "video_generation"],
                "quality_metrics": {
                    "audio_quality": 0.95,
                    "video_quality": 0.88
                }
            }
            
            job.mark_completed(results)
            db.session.commit()
            
            # Test the to_dict method with details
            print("📊 Testing job serialization...")
            job_dict = job.to_dict(include_details=True)
            
            # Verify all fields are present
            expected_fields = [
                'id', 'title', 'description', 'job_type', 'status', 'priority',
                'progress_percentage', 'created_at', 'updated_at', 'celery_task_id',
                'parameters', 'results', 'error_info', 'service_metadata',
                'started_at', 'completed_at', 'actual_start_time', 'actual_end_time',
                'total_processing_time', 'duration', 'estimated_duration'
            ]
            
            print("✅ Job created successfully!")
            print(f"📋 Job ID: {job.id}")
            print(f"📊 Status: {job.status.value}")
            processing_time_str = f"{job.total_processing_time:.3f}" if job.total_processing_time else "0.000"
            print(f"⏱️  Total processing time: {processing_time_str} seconds")
            print(f"📝 Service metadata keys: {list(job.service_metadata.keys()) if job.service_metadata else 'None'}")
            
            # Check if all expected fields are in the dictionary
            missing_fields = [field for field in expected_fields if field not in job_dict]
            if missing_fields:
                print(f"⚠️  Missing fields in job dictionary: {missing_fields}")
            else:
                print("✅ All expected fields present in job dictionary!")
            
            # Print sample of the metadata for verification
            if job.service_metadata:
                print("\n📋 Sample service metadata:")
                print(json.dumps(job.service_metadata, indent=2, default=str)[:500] + "...")
            
            # Test querying jobs with metadata
            print("\n🔍 Testing job queries...")
            jobs_with_metadata = Job.query.filter(Job.service_metadata.isnot(None)).all()
            print(f"📊 Jobs with service metadata: {len(jobs_with_metadata)}")
            
            # Test specific metadata queries (if supported by SQLite JSON functions)
            try:
                # This might not work in all SQLite versions, but let's try
                indextts_jobs = Job.query.filter(Job.service_metadata.contains('"indextts"')).all()
                print(f"🎤 Jobs with IndexTTS metadata: {len(indextts_jobs)}")
            except Exception as e:
                print(f"ℹ️  JSON query not supported in this SQLite version: {str(e)[:100]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_timing_precision():
    """Test the precision of timing measurements"""
    print("\n⏱️  Testing timing precision...")
    
    app = create_app()
    
    with app.app_context():
        try:
            admin_user = User.query.filter_by(email="admin@voiceclone.edu").first()
            
            # Create a job for timing testing
            job = Job(
                title="Timing Precision Test",
                job_type=JobType.TEXT_TO_SPEECH,
                user_id=admin_user.id
            )
            
            db.session.add(job)
            db.session.flush()
            
            # Record start time
            start_time = datetime.now()
            job.mark_started()
            
            # Simulate processing
            import time
            processing_time = 0.5  # 500ms
            time.sleep(processing_time)
            
            # Record end time
            end_time = datetime.now()
            job.mark_completed()
            
            db.session.commit()
            
            # Calculate expected vs actual timing
            expected_time = (end_time - start_time).total_seconds()
            recorded_time = job.total_processing_time
            
            print(f"📊 Expected processing time: {expected_time:.3f}s")
            recorded_time_str = f"{recorded_time:.3f}" if recorded_time else "0.000"
            print(f"📊 Recorded processing time: {recorded_time_str}s")
            difference = abs(expected_time - (recorded_time or 0))
            print(f"📊 Difference: {difference:.3f}s")
            
            # Check if timing is reasonably accurate (within 50ms)
            if recorded_time and abs(expected_time - recorded_time) < 0.05:
                print("✅ Timing precision test passed!")
                return True
            elif not recorded_time:
                print("⚠️  Timing precision test failed - no timing recorded")
                return False
            else:
                print("⚠️  Timing precision test failed - large difference detected")
                return False
                
        except Exception as e:
            print(f"❌ Timing test failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Testing updated Job model with metadata and timing fields\n")
    
    # Run tests
    test1_success = test_updated_job_model()
    test2_success = test_timing_precision()
    
    print(f"\n📊 Test Results:")
    print(f"   Job Model Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Timing Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Job model is ready for production.")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    sys.exit(0 if (test1_success and test2_success) else 1)
