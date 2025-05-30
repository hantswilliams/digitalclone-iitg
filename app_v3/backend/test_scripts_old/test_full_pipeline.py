#!/usr/bin/env python3
"""
Test script to verify the full video generation pipeline with enhanced logging
"""
import requests
import json
import time
import os
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:5001"  # Adjust if different
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"

def register_test_user():
    """Register a test user if it doesn't exist"""
    print("👤 Registering test user...")
    
    register_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "role": "student"  # Try different role values
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/auth/register", json=register_data)
        print(f"📊 Registration response: {response.status_code}")
        
        if response.status_code == 201:
            print(f"✅ Test user registered successfully")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print(f"ℹ️ Test user already exists")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            # Try with a different role
            register_data["role"] = "STUDENT"
            response = requests.post(f"{BACKEND_URL}/api/auth/register", json=register_data)
            print(f"📊 Registration retry response: {response.status_code}")
            if response.status_code == 201:
                print(f"✅ Test user registered successfully with STUDENT role")
                return True
            return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

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

def get_user_assets(token):
    """Get user's assets to find portrait and voice assets"""
    print("📁 Getting user assets...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/assets/", headers=headers)
        if response.status_code == 200:
            assets = response.json().get('assets', [])
            print(f"✅ Found {len(assets)} assets")
            
            # Find portrait and voice assets
            portrait_assets = [a for a in assets if a.get('asset_type') == 'portrait' and a.get('status') == 'ready']
            voice_assets = [a for a in assets if a.get('asset_type') == 'voice_sample' and a.get('status') == 'ready']
            
            print(f"🖼️ Portrait assets: {len(portrait_assets)}")
            print(f"🎵 Voice assets: {len(voice_assets)}")
            
            for asset in portrait_assets[:3]:  # Show first 3
                print(f"  - Portrait: {asset.get('id')} - {asset.get('original_filename')}")
            
            for asset in voice_assets[:3]:  # Show first 3
                print(f"  - Voice: {asset.get('id')} - {asset.get('original_filename')}")
            
            return portrait_assets, voice_assets
        else:
            print(f"❌ Failed to get assets: {response.status_code} - {response.text}")
            return [], []
    except Exception as e:
        print(f"❌ Error getting assets: {e}")
        return [], []

def create_video_job(token, portrait_asset_id, voice_asset_id, script):
    """Create a full pipeline video generation job"""
    print("🎬 Creating full pipeline video generation job...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    job_data = {
        "title": "Test Video Generation",
        "description": "Testing full pipeline with enhanced logging",
        "job_type": "full_pipeline",
        "priority": "normal",
        "parameters": {
            "portrait_asset_id": portrait_asset_id,
            "voice_asset_id": voice_asset_id,
            "script": script,
            "output_format": "mp4",
            "test_mode": True,
            "enhanced_logging": True
        },
        "asset_ids": [portrait_asset_id, voice_asset_id]
    }
    
    print(f"📤 Job data: {json.dumps(job_data, indent=2)}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/jobs/", json=job_data, headers=headers)
        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response data: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            job = response.json().get('job')
            job_id = job.get('id')
            print(f"✅ Job created successfully with ID: {job_id}")
            return job_id
        else:
            print(f"❌ Job creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating job: {e}")
        return None

def monitor_job(token, job_id, max_wait_time=600):
    """Monitor job progress"""
    print(f"👀 Monitoring job {job_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BACKEND_URL}/api/jobs/{job_id}", headers=headers)
            if response.status_code == 200:
                job = response.json().get('job')
                status = job.get('status')
                progress = job.get('progress', 0)
                message = job.get('status_message', 'No message')
                
                print(f"📊 Job {job_id}: {status} ({progress}%) - {message}")
                
                if status in ['completed', 'failed', 'cancelled']:
                    print(f"🏁 Job finished with status: {status}")
                    if status == 'completed':
                        print(f"🎉 Success! Job completed successfully")
                        # Print any output assets
                        if 'output_assets' in job:
                            for asset in job['output_assets']:
                                print(f"📁 Output asset: {asset.get('original_filename')} ({asset.get('id')})")
                    elif status == 'failed':
                        print(f"❌ Job failed: {job.get('error_message', 'Unknown error')}")
                    return job
                
                time.sleep(10)  # Wait 10 seconds before next check
            else:
                print(f"❌ Error checking job status: {response.status_code}")
                time.sleep(10)
        except Exception as e:
            print(f"❌ Error monitoring job: {e}")
            time.sleep(10)
    
    print(f"⏰ Timeout reached after {max_wait_time} seconds")
    return None

def main():
    print("🎬 ================== VIDEO GENERATION PIPELINE TEST ==================")
    
    # Test script
    test_script = """
    Hello! This is a test of our video generation pipeline. 
    I'm testing the integration between text-to-speech and video generation.
    This should create a talking avatar video with this exact speech.
    Let's see how well our system performs with enhanced logging!
    """
    
    print(f"📝 Test script: {test_script.strip()}")
    
    # Step 0: Register test user if needed
    register_test_user()
    
    # Step 1: Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Step 2: Get user assets
    portrait_assets, voice_assets = get_user_assets(token)
    if not portrait_assets or not voice_assets:
        print("❌ Need at least one portrait and one voice asset")
        return
    
    # Use first available assets
    portrait_asset = portrait_assets[0]
    voice_asset = voice_assets[0]
    
    print(f"🖼️ Using portrait asset: {portrait_asset['id']} - {portrait_asset['original_filename']}")
    print(f"🎵 Using voice asset: {voice_asset['id']} - {voice_asset['original_filename']}")
    
    # Step 3: Create video generation job
    job_id = create_video_job(token, portrait_asset['id'], voice_asset['id'], test_script)
    if not job_id:
        print("❌ Cannot proceed without job creation")
        return
    
    # Step 4: Monitor job progress
    final_job = monitor_job(token, job_id)
    
    print("🎬 ================== TEST COMPLETED ==================")
    if final_job and final_job.get('status') == 'completed':
        print("🎉 SUCCESS: Video generation pipeline completed successfully!")
    else:
        print("❌ FAILED: Video generation pipeline did not complete successfully")

if __name__ == "__main__":
    main()
