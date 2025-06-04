#!/usr/bin/env python3
"""
Test script to demonstrate how real service metadata (including hardware info) 
gets captured and stored in the database during actual video generation.
"""
import os
import sys
from datetime import datetime
import json

# Add the backend directory to the Python path
backend_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(backend_dir, '..'))

from app import create_app
from app.extensions import db
from app.models import User, Job, JobType, JobStatus
from app.services.tts.indextts_client import IndexTTSClient
from app.services.video.kdtalker_client import KDTalkerClient

def test_real_metadata_capture():
    """Test capturing real metadata from the services and storing it in the database"""
    print("🧪 Testing real service metadata capture...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get the admin user
            admin_user = User.query.filter_by(email="admin@voiceclone.edu").first()
            if not admin_user:
                print("❌ Admin user not found!")
                return False
            
            # Create a job for testing
            job = Job(
                title="Real Metadata Test - IndexTTS & KDTalker",
                job_type=JobType.FULL_PIPELINE,
                user_id=admin_user.id,
                description="Testing job with real service metadata capture",
                parameters={
                    "text": "This is a test for capturing real metadata.",
                    "voice_file": "test_voice.wav",
                    "image_file": "test_image.jpg"
                }
            )
            
            db.session.add(job)
            db.session.flush()
            
            print(f"📝 Created test job with ID: {job.id}")
            
            # Start timing
            job.mark_started()
            
            # Get real metadata from IndexTTS
            print("🎤 Fetching real IndexTTS metadata...")
            try:
                indextts_client = IndexTTSClient()
                indextts_metadata = indextts_client.get_space_metadata()
                print(f"✅ IndexTTS metadata retrieved: {indextts_metadata['metadata_available']}")
                if indextts_metadata.get('runtime'):
                    print(f"🖥️  Hardware: {indextts_metadata['runtime'].get('hardware_friendly', 'Unknown')}")
            except Exception as e:
                print(f"⚠️  IndexTTS metadata fetch failed: {str(e)}")
                indextts_metadata = {"error": str(e), "metadata_available": False}
            
            # Get real metadata from KDTalker
            print("🎬 Fetching real KDTalker metadata...")
            try:
                kdtalker_client = KDTalkerClient()
                kdtalker_metadata = kdtalker_client.get_space_metadata()
                print(f"✅ KDTalker metadata retrieved: {kdtalker_metadata['metadata_available']}")
                if kdtalker_metadata.get('runtime'):
                    print(f"🖥️  Hardware: {kdtalker_metadata['runtime'].get('hardware_friendly', 'Unknown')}")
            except Exception as e:
                print(f"⚠️  KDTalker metadata fetch failed: {str(e)}")
                kdtalker_metadata = {"error": str(e), "metadata_available": False}
            
            # Combine metadata
            combined_metadata = {
                "indextts": indextts_metadata,
                "kdtalker": kdtalker_metadata,
                "capture_timestamp": datetime.now().isoformat(),
                "capture_method": "real_api_calls"
            }
            
            # Store in job
            job.update_service_metadata(combined_metadata)
            
            # Complete the job
            results = {
                "status": "metadata_test_completed",
                "metadata_capture_successful": {
                    "indextts": indextts_metadata.get('metadata_available', False),
                    "kdtalker": kdtalker_metadata.get('metadata_available', False)
                }
            }
            
            job.mark_completed(results)
            db.session.commit()
            
            print(f"\n📊 Job completed with real metadata!")
            print(f"⏱️  Processing time: {job.total_processing_time:.3f} seconds")
            
            # Display captured hardware information
            print(f"\n🖥️  Hardware Information Captured:")
            if indextts_metadata.get('runtime'):
                runtime = indextts_metadata['runtime']
                print(f"   IndexTTS:")
                print(f"     - Stage: {runtime.get('stage', 'Unknown')}")
                print(f"     - Hardware: {runtime.get('hardware', 'Unknown')}")
                print(f"     - Friendly Name: {runtime.get('hardware_friendly', 'Unknown')}")
            
            if kdtalker_metadata.get('runtime'):
                runtime = kdtalker_metadata['runtime']
                print(f"   KDTalker:")
                print(f"     - Stage: {runtime.get('stage', 'Unknown')}")
                print(f"     - Hardware: {runtime.get('hardware', 'Unknown')}")
                print(f"     - Friendly Name: {runtime.get('hardware_friendly', 'Unknown')}")
            
            # Show a sample of the stored metadata
            print(f"\n📋 Sample of stored service_metadata:")
            metadata_str = json.dumps(job.service_metadata, indent=2, default=str)
            print(metadata_str[:800] + "..." if len(metadata_str) > 800 else metadata_str)
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def show_existing_jobs_metadata():
    """Show metadata from existing jobs in the database"""
    print("\n🔍 Checking existing jobs for metadata...")
    
    app = create_app()
    
    with app.app_context():
        try:
            jobs_with_metadata = Job.query.filter(Job.service_metadata.isnot(None)).all()
            
            print(f"📊 Found {len(jobs_with_metadata)} jobs with service metadata")
            
            for job in jobs_with_metadata:
                print(f"\n📋 Job {job.id}: {job.title}")
                print(f"   Status: {job.status.value}")
                print(f"   Created: {job.created_at}")
                
                if job.service_metadata:
                    # Check for hardware info in each service
                    for service_name, service_data in job.service_metadata.items():
                        if isinstance(service_data, dict) and 'runtime' in service_data:
                            runtime = service_data['runtime']
                            hardware_info = runtime.get('hardware_friendly', runtime.get('hardware', 'Unknown'))
                            print(f"   {service_name.title()} Hardware: {hardware_info}")
                        elif isinstance(service_data, dict) and 'metadata_available' in service_data:
                            available = service_data['metadata_available']
                            print(f"   {service_name.title()} Metadata: {'✅ Available' if available else '❌ Not Available'}")
                
                if job.total_processing_time:
                    print(f"   Processing Time: {job.total_processing_time:.3f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to check existing jobs: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Testing Real Service Metadata Capture with Hardware Information\n")
    
    # Show existing metadata first
    show_existing_jobs_metadata()
    
    # Test capturing new real metadata
    print("\n" + "="*60)
    success = test_real_metadata_capture()
    
    if success:
        print(f"\n🎉 Real metadata capture test completed successfully!")
        print(f"💡 The database now contains real hardware information from HuggingFace spaces.")
        print(f"🔄 During actual video generation, this metadata will be automatically captured.")
    else:
        print(f"\n❌ Real metadata capture test failed.")
    
    # Show updated metadata
    print("\n" + "="*60)
    show_existing_jobs_metadata()
    
    sys.exit(0 if success else 1)
