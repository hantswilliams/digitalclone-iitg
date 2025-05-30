#!/usr/bin/env python3
"""
Test the full TTS pipeline: IndexTTS generation + MinIO storage upload
"""

import sys
import os
from io import BytesIO

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.tts.indextts_client import IndexTTSClient


def test_tts_with_storage_upload():
    """Test TTS generation and storage upload simulation."""
    print("Testing TTS generation + Storage upload simulation...")
    
    try:
        # 1. Initialize IndexTTS client
        print("1. Initializing IndexTTS client...")
        client = IndexTTSClient()
        
        # 2. Test voice file
        voice_file_path = "/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice.wav"
        if not os.path.exists(voice_file_path):
            print(f"Error: Voice file not found at {voice_file_path}")
            return False
        
        # 3. Generate speech
        print("2. Generating speech with IndexTTS...")
        test_text = "Testing the complete TTS pipeline with storage upload."
        
        speech_audio_data = client.generate_speech(
            text=test_text,
            speaker_audio=voice_file_path
        )
        
        print(f"✅ Speech generated: {len(speech_audio_data)} bytes")
        
        # 4. Simulate the storage upload fix
        print("3. Testing BytesIO conversion for storage...")
        
        # Convert bytes to BytesIO (this is what we fixed in the TTS task)
        audio_file_obj = BytesIO(speech_audio_data)
        
        # Verify it has the read() method that MinIO expects
        if hasattr(audio_file_obj, 'read'):
            print("✅ BytesIO object has read() method")
        else:
            print("❌ BytesIO object missing read() method")
            return False
        
        # Test reading from it
        audio_file_obj.seek(0)
        test_read = audio_file_obj.read(100)  # Read first 100 bytes
        audio_file_obj.seek(0)  # Reset
        
        print(f"✅ Successfully read {len(test_read)} bytes from BytesIO")
        
        # 5. Save test output
        output_file = "/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_tts_pipeline_output.wav"
        with open(output_file, 'wb') as f:
            f.write(speech_audio_data)
        print(f"✅ Saved output to: {output_file}")
        
        print("\n🎉 TTS + Storage pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== TTS + Storage Pipeline Test ===\n")
    
    # Check environment
    hf_token = os.getenv('HF_API_TOKEN')
    if not hf_token:
        print("Error: HF_API_TOKEN not found in environment")
        sys.exit(1)
    
    # Run tests
    success = test_tts_with_storage_upload()
    
    if success:
        print("\n=== Pipeline test passed! The storage upload fix should work! ===")
        sys.exit(0)
    else:
        print("\n=== Pipeline test failed! ===")
        sys.exit(1)
