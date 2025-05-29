#!/usr/bin/env python3
"""
Complete Video Generation Workflow Test
Tests the full video generation workflow including:
1. User registration/authentication
2. Video job creation
3. Asset creation and MinIO storage
4. Asset retrieval via API
"""
import requests
import json
import time
import os
from pathlib import Path

# API configuration
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

# Test user data
TEST_USER = {
    "username": f"videotest_user_{int(time.time())}",
    "email": f"videotest_{int(time.time())}@example.com", 
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "Video",
    "last_name": "Tester",
    "department": "Engineering",
    "title": "Test Engineer",
    "role": "faculty"
}

def print_status(message, success=True, level="INFO"):
    """Print formatted status message"""
    if level == "HEADER":
        print(f"\n{'='*60}")
        print(f"🎬 {message}")
        print(f"{'='*60}")
    else:
        prefix = "✅" if success else "❌"
        print(f"{prefix} {message}")

def register_and_login():
    """Register test user and get JWT token"""
    print_status("Setting up authentication...", level="HEADER")
    
    # Register user
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=TEST_USER)
        if response.status_code == 201:
            print_status("User registered successfully")
        else:
            print_status(f"Registration failed: {response.text}", False)
            return None, None
    except Exception as e:
        print_status(f"Registration error: {e}", False)
        return None, None
    
    # Login
    try:
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_id = data.get("user_id")
            print_status("Login successful")
            print_status(f"User ID: {user_id}")
            return token, user_id
        else:
            print_status(f"Login failed: {response.text}", False)
            return None, None
    except Exception as e:
        print_status(f"Login error: {e}", False)
        return None, None

def upload_test_files(token):
    """Upload test image and audio files"""
    print_status("Uploading test files...", level="HEADER")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check if test files exist
    test_files_dir = Path(__file__).parent / "test_files"
    image_path = test_files_dir / "hants.png"
    audio_path = test_files_dir / "voice_joelsaltz.wav"
    
    if not image_path.exists():
        print_status(f"Test image not found: {image_path}", False)
        return None, None
    
    if not audio_path.exists():
        print_status(f"Test audio not found: {audio_path}", False)
        return None, None
    
    uploaded_assets = {}
    
    # Upload image
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/png')}
            data = {'asset_type': 'portrait_image'}
            
            response = requests.post(f"{API_BASE}/assets/upload", 
                                   files=files, data=data, headers=headers)
            
            if response.status_code == 201:
                asset_data = response.json()
                uploaded_assets['image'] = asset_data['asset']
                print_status(f"Image uploaded (ID: {asset_data['asset']['id']})")
            else:
                print_status(f"Image upload failed: {response.text}", False)
                return None, None
    except Exception as e:
        print_status(f"Image upload error: {e}", False)
        return None, None
    
    # Upload audio
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': (audio_path.name, f, 'audio/wav')}
            data = {'asset_type': 'generated_audio'}
            
            response = requests.post(f"{API_BASE}/assets/upload", 
                                   files=files, data=data, headers=headers)
            
            if response.status_code == 201:
                asset_data = response.json()
                uploaded_assets['audio'] = asset_data['asset']
                print_status(f"Audio uploaded (ID: {asset_data['asset']['id']})")
            else:
                print_status(f"Audio upload failed: {response.text}", False)
                return None, None
    except Exception as e:
        print_status(f"Audio upload error: {e}", False)
        return None, None
    
    return uploaded_assets['image'], uploaded_assets['audio']

def create_video_job(token, image_asset, audio_asset):
    """Create a video generation job"""
    print_status("Creating video generation job...", level="HEADER")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    job_data = {
        "title": "Test KDTalker Video Generation",
        "description": "Testing complete video generation workflow with Asset creation",
        "job_type": "video_generation",
        "priority": "normal",
        "parameters": {
            "image_asset_id": image_asset['id'],
            "audio_asset_id": audio_asset['id'],
            "driven_audio_type": "singing",
            "smoothed_pitch": True,
            "smoothed_yaw": True,
            "smoothed_roll": True,
            "smoothed_t": True
        },
        "estimated_duration": 60
    }
    
    try:
        response = requests.post(f"{API_BASE}/jobs/", json=job_data, headers=headers)
        
        if response.status_code == 201:
            job = response.json()["job"]
            print_status(f"Job created (ID: {job['id']})")
            print_status(f"Job status: {job['status']}")
            return job
        else:
            print_status(f"Job creation failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Job creation error: {e}", False)
        return None

def monitor_job_progress(token, job_id):
    """Monitor job progress until completion"""
    print_status("Monitoring job progress...", level="HEADER")
    
    headers = {"Authorization": f"Bearer {token}"}
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{API_BASE}/jobs/{job_id}", headers=headers)
            
            if response.status_code == 200:
                job = response.json()["job"]
                status = job['status']
                
                print_status(f"Job status: {status}")
                
                if status == 'completed':
                    print_status("Job completed successfully!")
                    return job
                elif status == 'failed':
                    print_status(f"Job failed: {job.get('error_message', 'Unknown error')}", False)
                    return job
                elif status in ['pending', 'running']:
                    print_status(f"Job {status}, waiting...")
                    time.sleep(10)
                else:
                    print_status(f"Unknown job status: {status}")
                    time.sleep(10)
            else:
                print_status(f"Failed to get job status: {response.text}", False)
                time.sleep(10)
                
        except Exception as e:
            print_status(f"Error checking job status: {e}", False)
            time.sleep(10)
    
    print_status("Job monitoring timed out", False)
    return None

def verify_generated_assets(token, job):
    """Verify that video assets were created and are accessible"""
    print_status("Verifying generated assets...", level="HEADER")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check job result for generated asset ID
    result_data = job.get('result_data', {})
    generated_asset_id = result_data.get('generated_asset_id')
    
    if not generated_asset_id:
        print_status("No generated asset ID found in job result", False)
        return False
    
    print_status(f"Generated asset ID: {generated_asset_id}")
    
    # Retrieve the asset details
    try:
        response = requests.get(f"{API_BASE}/assets/{generated_asset_id}", headers=headers)
        
        if response.status_code == 200:
            asset = response.json()["asset"]
            print_status(f"Asset retrieved: {asset['filename']}")
            print_status(f"Asset type: {asset['asset_type']}")
            print_status(f"Asset status: {asset['status']}")
            print_status(f"File size: {asset['file_size']} bytes")
            print_status(f"Storage path: {asset['storage_path']}")
            
            if asset['asset_type'] == 'generated_video':
                print_status("Asset type is correctly set to 'generated_video'")
            else:
                print_status(f"Unexpected asset type: {asset['asset_type']}", False)
                return False
                
            return True
        else:
            print_status(f"Failed to retrieve asset: {response.text}", False)
            return False
            
    except Exception as e:
        print_status(f"Error retrieving asset: {e}", False)
        return False

def list_user_assets(token, asset_type=None):
    """List all assets for the user"""
    print_status("Listing user assets...", level="HEADER")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    
    if asset_type:
        params['asset_type'] = asset_type
    
    try:
        response = requests.get(f"{API_BASE}/assets/", params=params, headers=headers)
        
        if response.status_code == 200:
            assets_data = response.json()
            assets = assets_data.get('assets', [])
            
            print_status(f"Found {len(assets)} assets")
            
            for asset in assets:
                print_status(f"  - {asset['filename']} ({asset['asset_type']}) - {asset['status']}")
                
            # Count generated videos specifically
            video_assets = [a for a in assets if a['asset_type'] == 'generated_video']
            print_status(f"Generated video assets: {len(video_assets)}")
            
            return assets
        else:
            print_status(f"Failed to list assets: {response.text}", False)
            return []
            
    except Exception as e:
        print_status(f"Error listing assets: {e}", False)
        return []

def main():
    """Run the complete video generation workflow test"""
    print_status("COMPLETE VIDEO GENERATION WORKFLOW TEST", level="HEADER")
    
    # Step 1: Authentication
    token, user_id = register_and_login()
    if not token:
        print_status("Authentication failed, cannot continue", False)
        return
    
    # Step 2: Upload test files
    image_asset, audio_asset = upload_test_files(token)
    if not image_asset or not audio_asset:
        print_status("File upload failed, cannot continue", False)
        return
    
    # Step 3: Create video generation job
    job = create_video_job(token, image_asset, audio_asset)
    if not job:
        print_status("Job creation failed, cannot continue", False)
        return
    
    # Step 4: Monitor job progress
    completed_job = monitor_job_progress(token, job['id'])
    if not completed_job or completed_job['status'] != 'completed':
        print_status("Job did not complete successfully", False)
        return
    
    # Step 5: Verify generated assets
    assets_verified = verify_generated_assets(token, completed_job)
    if not assets_verified:
        print_status("Asset verification failed", False)
        return
    
    # Step 6: List all user assets
    all_assets = list_user_assets(token)
    video_assets = list_user_assets(token, 'generated_video')
    
    # Final summary
    print_status("WORKFLOW TEST SUMMARY", level="HEADER")
    print_status("✅ User registration and authentication")
    print_status("✅ Test file upload (image and audio)")
    print_status("✅ Video generation job creation")
    print_status("✅ Job completion monitoring")
    print_status("✅ Generated video asset creation")
    print_status("✅ Asset retrieval and verification")
    print_status("✅ Asset listing functionality")
    print_status("")
    print_status("🎉 Complete video generation workflow test PASSED!")

if __name__ == "__main__":
    main()
