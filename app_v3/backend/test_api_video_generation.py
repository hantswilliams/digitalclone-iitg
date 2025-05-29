#!/usr/bin/env python3
"""
Test full end-to-end video generation through the API
Tests the complete workflow: API request -> Celery task -> KDTalker -> MinIO -> Asset creation
"""

import requests
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_video_generation():
    """Test complete video generation workflow through API"""
    
    # API configuration
    BASE_URL = "http://localhost:5001"
    
    print("=== API Video Generation Test ===")
    
    # Step 1: Check API health
    print("\n1. Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Step 1.5: Register and login to get authentication token
    print("\n1.5. Setting up authentication...")
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "faculty"
    }
    
    # Try to register user (may already exist)
    try:
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user, timeout=10)
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        elif register_response.status_code == 409:
            print("✅ User already exists, continuing with login")
        else:
            print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Login to get tokens
    try:
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get("access_token")
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Login error: {e}")
        return
    
    # Set up headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get available assets (portraits and audio)
    print("\n2. Getting available assets...")
    try:
        assets_response = requests.get(f"{BASE_URL}/api/assets", headers=headers, timeout=10)
        if assets_response.status_code == 200:
            response_data = assets_response.json()
            print(f"Assets response: {response_data}")
            
            # Handle different possible response formats
            if isinstance(response_data, dict) and 'assets' in response_data:
                assets = response_data['assets']
            elif isinstance(response_data, list):
                assets = response_data
            else:
                assets = []
            
            portraits = [a for a in assets if a.get('type') == 'portrait']
            audio_files = [a for a in assets if a.get('type') == 'generated_audio']
            
            print(f"Found {len(portraits)} portraits and {len(audio_files)} audio files")
            
            if not portraits:
                print("❌ No portraits available for testing")
                return
            if not audio_files:
                print("❌ No audio files available for testing")
                return
                
            # Use first available assets
            test_portrait = portraits[0]
            test_audio = audio_files[0]
            print(f"Using portrait: {test_portrait['filename']}")
            print(f"Using audio: {test_audio['filename']}")
            
        else:
            print(f"❌ Failed to get assets: {assets_response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get assets: {e}")
        return
    
    # Step 3: Submit video generation request
    print("\n3. Submitting video generation request...")
    video_request = {
        "portrait_id": test_portrait['id'],
        "audio_id": test_audio['id'],
        "service": "kdtalker"
    }
    
    try:
        generate_response = requests.post(
            f"{BASE_URL}/api/generate/video",
            json=video_request,
            headers=headers,
            timeout=10
        )
        
        if generate_response.status_code == 200:
            result = generate_response.json()
            task_id = result.get('task_id')
            print(f"✅ Video generation started, task_id: {task_id}")
        else:
            print(f"❌ Failed to start video generation: {generate_response.status_code}")
            print(f"Response: {generate_response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to submit video generation request: {e}")
        return
    
    # Step 4: Monitor task progress
    print("\n4. Monitoring task progress...")
    max_wait = 180  # 3 minutes max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status", headers=headers, timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                state = status.get('state', 'UNKNOWN')
                
                if state == 'PENDING':
                    print("⏳ Task is pending...")
                elif state == 'STARTED':
                    print("🔄 Task is running...")
                elif state == 'SUCCESS':
                    print("✅ Task completed successfully!")
                    result = status.get('result', {})
                    asset_id = result.get('asset_id')
                    if asset_id:
                        print(f"Created asset with ID: {asset_id}")
                    break
                elif state == 'FAILURE':
                    print("❌ Task failed!")
                    error = status.get('result', {})
                    print(f"Error: {error}")
                    return
                else:
                    print(f"Task state: {state}")
            else:
                print(f"Failed to get task status: {status_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error checking task status: {e}")
        
        time.sleep(5)  # Wait 5 seconds before checking again
    else:
        print("❌ Task timed out after 3 minutes")
        return
    
    # Step 5: Verify asset was created
    print("\n5. Verifying generated video asset...")
    try:
        assets_response = requests.get(f"{BASE_URL}/api/assets", headers=headers, timeout=10)
        if assets_response.status_code == 200:
            assets = assets_response.json()
            video_assets = [a for a in assets if a['type'] == 'generated_video']
            
            # Find our newly created asset
            new_asset = None
            for asset in video_assets:
                if asset['id'] == asset_id:
                    new_asset = asset
                    break
            
            if new_asset:
                print(f"✅ Video asset created successfully!")
                print(f"   - ID: {new_asset['id']}")
                print(f"   - Filename: {new_asset['filename']}")
                print(f"   - File size: {new_asset.get('file_size', 'unknown')} bytes")
                print(f"   - Created: {new_asset['created_at']}")
                
                # Check if file exists in MinIO
                if 'file_path' in new_asset:
                    print(f"   - Storage path: {new_asset['file_path']}")
                
            else:
                print(f"❌ Could not find video asset with ID {asset_id}")
        else:
            print(f"❌ Failed to verify assets: {assets_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to verify assets: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_api_video_generation()
