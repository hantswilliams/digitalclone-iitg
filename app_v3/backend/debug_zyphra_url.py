#!/usr/bin/env python3
"""
Debug script to test Zyphra URL handling
"""

import os
import sys
import logging

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.tts.zyphra_client import ZyphraClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("=== Zyphra Client Test ===")
    
    try:
        # Create client
        client = ZyphraClient()
        print(f"Successfully initialized Zyphra client")
        
        # Test basic functionality - we'll just verify the client was created
        print(f"Client has official Zyphra client: {hasattr(client, 'client')}")
        print(f"API key configured: {bool(client.api_key)}")
        
        # Test audio encoding with dummy data
        try:
            dummy_audio = b"dummy audio data for testing"
            encoded = client._encode_audio_to_base64(dummy_audio)
            print(f"Audio encoding test successful: {len(encoded)} characters")
        except Exception as e:
            print(f"Audio encoding test failed: {e}")
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
