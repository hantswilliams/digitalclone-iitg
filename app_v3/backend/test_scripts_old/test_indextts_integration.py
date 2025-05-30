#!/usr/bin/env python3
"""
Test script for IndexTTS integration in the backend.
"""

import sys
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.tts import IndexTTSClient

def test_indextts_client():
    """Test the IndexTTS client functionality."""
    try:
        print("🔧 Initializing IndexTTS client...")
        # Client will read HF token from environment variables
        client = IndexTTSClient()
        
        print("✅ Configuration validation...")
        config_result = client.validate_configuration()
        print(f"   Valid: {config_result['valid']}")
        print(f"   Issues: {config_result['issues']}")
        
        print("🏥 Health check...")
        health_result = client.health_check()
        print(f"   Status: {health_result['status']}")
        print(f"   Space: {health_result.get('space_name', 'Unknown')}")
        
        if health_result['status'] == 'healthy':
            print("🎤 Testing speech generation...")
            
            # Use the test voice file
            voice_file = '/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice.wav'
            
            if os.path.exists(voice_file):
                print(f"   Using voice file: {voice_file}")
                
                audio_data = client.generate_speech(
                    text="This is a test of the IndexTTS integration in our backend system.",
                    speaker_audio=voice_file
                )
                
                print(f"✅ Generated audio: {len(audio_data)} bytes")
                
                # Save test output
                output_file = '/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_indexTTS_output.wav'
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                print(f"   Saved to: {output_file}")
                
            else:
                print(f"   ⚠️ Voice file not found: {voice_file}")
        
        print("✅ IndexTTS integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ IndexTTS test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_indextts_client()
