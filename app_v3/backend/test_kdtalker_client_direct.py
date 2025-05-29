#!/usr/bin/env python3
"""
Test the KDTalker client directly
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

from app.services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig

def test_kdtalker_client():
    """Test KDTalker client directly"""
    print("🧪 Testing KDTalker Client Direct Integration")
    print("=" * 50)
    
    try:
        # Initialize client
        client = KDTalkerClient()
        print("✅ KDTalker client initialized")
        
        # Test health check
        health = client.health_check()
        print(f"Health check: {health['status']}")
        if health['status'] != 'healthy':
            print(f"❌ Health check failed: {health.get('error')}")
            return False
        
        # Test file paths
        portrait_path = Path("test_files/hants.png")
        audio_path = Path("test_files/voice_joelsaltz.wav")
        
        if not portrait_path.exists():
            print(f"❌ Portrait not found: {portrait_path}")
            return False
        if not audio_path.exists():
            print(f"❌ Audio not found: {audio_path}")
            return False
        
        print(f"✅ Input files found")
        
        # Test video generation
        config = VideoGenerationConfig(
            driven_audio_type='upload',
            smoothed_pitch=0.8,
            smoothed_yaw=0.8,
            smoothed_roll=0.8,
            smoothed_t=0.8
        )
        
        output_path = Path("test_files/client_test_output.mp4")
        
        print(f"🎬 Generating video...")
        result = client.generate_video(
            portrait_path=portrait_path,
            audio_path=audio_path,
            output_path=output_path,
            config=config
        )
        
        print(f"✅ Generation complete!")
        print(f"Status: {result.get('status')}")
        print(f"Video path: {result.get('video_path')}")
        print(f"File size: {result.get('file_size')} bytes")
        print(f"Generation time: {result.get('generation_time'):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kdtalker_client()
    if success:
        print("\n🎉 KDTalker client test PASSED!")
    else:
        print("\n❌ KDTalker client test FAILED!")
