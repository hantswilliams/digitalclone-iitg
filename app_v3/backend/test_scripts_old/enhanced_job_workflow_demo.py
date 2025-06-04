#!/usr/bin/env python3
"""
Example of how to update task functions to capture and store service metadata and timing information.

This script demonstrates the pattern to follow when updating existing task functions
to use the new Job model fields for metadata and timing tracking.
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
from app.services.video.kdtalker_client import KDTalkerClient
from app.services.tts.indextts_client import IndexTTSClient


def example_video_generation_task_with_metadata(job_id: int, portrait_asset_id: int, audio_asset_id: int):
    """
    Example of an updated video generation task that captures metadata and timing.
    
    This shows the pattern to follow when updating existing task functions.
    """
    print(f"🎬 Starting enhanced video generation task for job {job_id}")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get job and mark as started (this will set actual_start_time)
            job = Job.query.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            print(f"⏰ Marking job as started...")
            job.mark_started()  # This now sets actual_start_time and status
            db.session.commit()
            
            # Initialize service metadata dictionary
            service_metadata = {}
            
            # === TTS PHASE ===
            print(f"🎤 Starting TTS phase...")
            
            # Initialize IndexTTS client and capture metadata
            indextts_client = IndexTTSClient()
            
            # Get HuggingFace metadata for IndexTTS
            indextts_metadata = indextts_client.get_space_metadata()
            print(f"📊 Captured IndexTTS metadata: {list(indextts_metadata.keys())}")
            
            # Store IndexTTS metadata
            service_metadata['indextts'] = {
                'service_info': indextts_metadata,
                'model_details': {
                    'space_name': indextts_client.space_name,
                    'model_type': 'Text-to-Speech',
                    'voice_cloning': True,
                    'model_family': 'IndexTTS'
                },
                'usage_timestamp': datetime.now().isoformat(),
                'phase': 'text_to_speech'
            }
            
            # Update job with TTS metadata (incremental updates)
            job.update_service_metadata(service_metadata)
            db.session.commit()
            print(f"💾 Updated job with IndexTTS metadata")
            
            # === VIDEO GENERATION PHASE ===
            print(f"🎥 Starting video generation phase...")
            
            # Initialize KDTalker client and capture metadata
            kdtalker_client = KDTalkerClient()
            
            # Get HuggingFace metadata for KDTalker
            kdtalker_metadata = kdtalker_client.get_space_metadata()
            print(f"📊 Captured KDTalker metadata: {list(kdtalker_metadata.keys())}")
            
            # Store KDTalker metadata
            service_metadata['kdtalker'] = {
                'service_info': kdtalker_metadata,
                'model_details': {
                    'space_name': kdtalker_client.space_name,
                    'model_type': 'Video Generation',
                    'talking_head': True,
                    'model_family': 'KDTalker'
                },
                'usage_timestamp': datetime.now().isoformat(),
                'phase': 'video_generation'
            }
            
            # Update job with KDTalker metadata
            job.update_service_metadata(service_metadata)
            db.session.commit()
            print(f"💾 Updated job with KDTalker metadata")
            
            # === SIMULATION ===
            # In a real implementation, you would call the actual services here
            print(f"⚙️  Simulating video generation processing...")
            import time
            time.sleep(1)  # Simulate processing time
            
            # === COMPLETION ===
            print(f"✅ Marking job as completed...")
            
            # Create comprehensive results
            results = {
                'status': 'success',
                'output_video_path': f'/path/to/output/video_{job_id}.mp4',
                'processing_summary': {
                    'phases_completed': ['text_to_speech', 'video_generation'],
                    'services_used': list(service_metadata.keys()),
                    'total_phases': 2
                },
                'quality_metrics': {
                    'tts_quality': 0.95,
                    'video_quality': 0.88,
                    'lip_sync_score': 0.92
                },
                'file_info': {
                    'output_format': 'mp4',
                    'duration_seconds': 30,
                    'resolution': '1024x1024',
                    'fps': 25
                }
            }
            
            # Mark job as completed (this will set actual_end_time and calculate total_processing_time)
            job.mark_completed(results)
            db.session.commit()
            
            # Display final job state
            print(f"\n📊 Final Job State:")
            print(f"   Status: {job.status.value}")
            print(f"   Total processing time: {job.total_processing_time:.3f} seconds")
            print(f"   Services used: {list(job.service_metadata.keys()) if job.service_metadata else 'None'}")
            print(f"   Start time: {job.actual_start_time}")
            print(f"   End time: {job.actual_end_time}")
            
            return True
            
        except Exception as e:
            print(f"❌ Task failed: {str(e)}")
            
            # Mark job as failed with timing
            job = Job.query.get(job_id)
            if job:
                error_info = {
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                }
                job.mark_failed(error_info)
                db.session.commit()
            
            return False


def test_metadata_integration():
    """Test the metadata integration with a real job"""
    print("🧪 Testing metadata integration...")
    
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(email="admin@voiceclone.edu").first()
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        # Create a test job
        job = Job(
            title="Enhanced Video Generation Test",
            job_type=JobType.FULL_PIPELINE,
            user_id=admin_user.id,
            description="Testing enhanced job workflow with metadata capture",
            parameters={
                "text": "Hello, this is a test of the enhanced video generation system.",
                "portrait_asset_id": 1,
                "audio_asset_id": 2
            }
        )
        
        db.session.add(job)
        db.session.flush()
        
        print(f"📝 Created test job {job.id}")
        
        # Run the enhanced task
        success = example_video_generation_task_with_metadata(job.id, 1, 2)
        
        if success:
            # Verify the metadata was stored correctly
            updated_job = Job.query.get(job.id)
            job_dict = updated_job.to_dict(include_details=True)
            
            print(f"\n✅ Test completed successfully!")
            print(f"📊 Job metadata keys: {list(job_dict.get('service_metadata', {}).keys())}")
            print(f"⏱️  Timing captured: {bool(job_dict.get('total_processing_time'))}")
            
            # Save detailed results for inspection
            output_file = os.path.join(os.path.dirname(__file__), '..', 'test_files', 'enhanced_job_test_results.json')
            with open(output_file, 'w') as f:
                json.dump(job_dict, f, indent=2, default=str)
            print(f"📄 Detailed results saved to: {output_file}")
            
            return True
        else:
            print("❌ Test failed!")
            return False


if __name__ == "__main__":
    print("🚀 Enhanced Job Workflow Demonstration\n")
    
    success = test_metadata_integration()
    
    if success:
        print("\n🎉 Enhanced job workflow test completed successfully!")
        print("\nKey improvements demonstrated:")
        print("  ✅ Automatic timing capture (actual_start_time, actual_end_time, total_processing_time)")
        print("  ✅ HuggingFace metadata capture from IndexTTS and KDTalker")
        print("  ✅ Incremental metadata updates during processing")
        print("  ✅ Comprehensive error handling with timing")
        print("  ✅ Enhanced job serialization with all new fields")
        print("\nNext steps:")
        print("  1. Update existing task functions to follow this pattern")
        print("  2. Update frontend to display the new metadata and timing info")
        print("  3. Add analytics dashboard for service usage tracking")
    else:
        print("\n❌ Test failed - please check the output above for errors")
    
    sys.exit(0 if success else 1)
