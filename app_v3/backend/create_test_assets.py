#!/usr/bin/env python3
"""
Create test assets for the test user to enable full pipeline testing
"""
import requests
import os
from pathlib import Path

# Configuration  
BACKEND_URL = "http://localhost:5001"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"

def get_auth_token():
    """Get JWT token for authentication"""
    print("🔑 Getting authentication token...")
    
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def upload_asset(token, file_path, asset_type, name, description):
    """Upload an asset file"""
    print(f"📤 Uploading {asset_type}: {name}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'asset_type': asset_type,
                'description': description
            }
            
            response = requests.post(f"{BACKEND_URL}/api/assets/upload", files=files, data=data, headers=headers)
            print(f"📊 Upload response: {response.status_code}")
            
            if response.status_code == 201:
                asset = response.json().get('asset')
                print(f"✅ Asset uploaded successfully: ID {asset['id']}")
                return asset
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def main():
    print("📁 ================== CREATING TEST ASSETS ==================")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return
    
    # Define test files
    portrait_file = "./test_files/hants.png"
    voice_file = "./test_files/voice_joelsaltz.wav"
    
    # Upload portrait asset
    portrait_asset = upload_asset(
        token,
        portrait_file,
        "portrait",
        "Test Portrait",
        "Test portrait image for video generation"
    )
    
    # Upload voice asset  
    voice_asset = upload_asset(
        token, 
        voice_file,
        "voice_sample",
        "Test Voice Sample",
        "Test voice sample for TTS cloning"
    )
    
    if portrait_asset and voice_asset:
        print("🎉 ================== ASSETS CREATED SUCCESSFULLY ==================")
        print(f"🖼️ Portrait Asset ID: {portrait_asset['id']}")
        print(f"🎵 Voice Asset ID: {voice_asset['id']}")
        print("✅ Ready to test full pipeline!")
    else:
        print("❌ Failed to create all required assets")

if __name__ == "__main__":
    main()
