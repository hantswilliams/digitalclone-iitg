#!/usr/bin/env python3
"""
Test the current KDTalker client implementation
"""
import sys
import os
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from dotenv import load_dotenv
load_dotenv()

from app.services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig

def test_current_implementation():
    """Test the current KDTalker client implementation"""
    
    print("🧪 Testing current KDTalker client implementation...")
    
    # Initialize client
    client = KDTalkerClient()
    
    # Test health check
    print("\n1. Testing health check...")
    health = client.health_check()
    print(f"Health check result: {health}")
    
    if health['status'] != 'healthy':
        print("❌ Health check failed, stopping test")
        return
    
    # Test video generation
    print("\n2. Testing video generation...")
    
    # Use same files as the working debug script
    portrait_path = "test_files/hants.png"
    audio_path = "test_files/voice_joelsaltz.wav"
    output_path = "test_files/output_current_test.mp4"
    
    # Check if files exist
    if not os.path.exists(portrait_path):
        print(f"❌ Portrait file not found: {portrait_path}")
        return
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    try:
        # Use same config as debug script
        config = VideoGenerationConfig(
            driven_audio_type="upload",
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
        
        print("✅ Video generation successful!")
        print(f"Result: {result}")
        
        # Check output file
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📁 Output file size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        else:
            print("❌ Output file not found")
            
    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_implementation()
