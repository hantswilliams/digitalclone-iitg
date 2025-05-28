#!/usr/bin/env python3
"""
Debug script to test Zyphra TTS functionality using Gradio client
"""

import os
import sys
import logging

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
from gradio_client import Client

## print HF_API_TOKEN
print(f"HF_API_TOKEN: {os.getenv('HF_API_TOKEN')}")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_gradio_zyphra():
    """Test Zyphra TTS using the Gradio client approach"""
    try:
        from gradio_client import Client, handle_file
        
        print("=== Zyphra TTS Gradio Client Test ===")
        
        # Initialize client
        print("Connecting to Zyphra TTS Gradio Space...")
        client = Client("hants/VoiceClone-TTS", hf_token='')
        print("✓ Connected successfully")

        # Check if test voice file exists
        voice_file_path = "/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice.wav"
        if not os.path.exists(voice_file_path):
            print(f"⚠ Warning: Voice file not found at {voice_file_path}")
            print("Using a remote sample audio file instead...")
            voice_file = handle_file('https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav')
        else:
            print(f"✓ Using local voice file: {voice_file_path}")
            voice_file = handle_file(voice_file_path)
        
        # Generate audio
        print("Generating speech with voice cloning...")
        result = client.predict(
            model_choice="Zyphra/Zonos-v0.1-transformer",
            text="Hello my name is Bob",
            language="en-us",
            speaker_audio=voice_file,
            prefix_audio=handle_file('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice.wav'),
            e1=1,          # Happiness
            e2=0.05,       # Sadness
            e3=0.05,       # Disgust
            e4=0.05,       # Fear
            e5=0.05,       # Surprise
            e6=0.05,       # Anger
            e7=0.1,        # Other
            e8=0.2,        # Neutral
            vq_single=0.78,      # Voice Clarity
            fmax=24000,          # Frequency Max (Hz)
            pitch_std=45,        # Pitch Variation
            speaking_rate=15,    # Speaking Rate
            dnsmos_ovrl=4,       # Voice Quality
            speaker_noised=False, # Denoise Speaker
            cfg_scale=2,         # Guidance Scale
            min_p=0.15,          # Min P (Randomness)
            seed=420,            # Seed
            randomize_seed=True, # Randomize Seed
            unconditional_keys=["emotion"], # Unconditional Keys
            api_name="/generate_audio"
        )
        
        # Result should be a tuple: (generated_audio_filepath, seed)
        if result and len(result) >= 1:
            generated_audio_path = result[0]
            seed_used = result[1] if len(result) > 1 else "unknown"
            
            print(f"✓ Speech generation successful!")
            print(f"Generated audio file: {generated_audio_path}")
            print(f"Seed used: {seed_used}")
            
            # Check if file exists and get size
            if hasattr(generated_audio_path, 'name'):
                actual_path = generated_audio_path.name
            else:
                actual_path = str(generated_audio_path)
                
            if os.path.exists(actual_path):
                file_size = os.path.getsize(actual_path)
                print(f"Generated file size: {file_size} bytes")
            
            return True, result
        else:
            print("❌ No result returned from generation")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during TTS generation: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    success, result = test_gradio_zyphra()
    if success:
        print("\n🎉 Zyphra TTS test completed successfully!")
    else:
        print("\n💥 Zyphra TTS test failed!")

if __name__ == "__main__":
    main()
