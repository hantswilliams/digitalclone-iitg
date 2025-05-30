#!/usr/bin/env python3
"""
Simple Job API Testing Script
Tests the core job management functionality we've implemented so far.
"""

import requests
import json
from io import BytesIO

# Configuration
API_BASE = "http://localhost:5001/api"

def test_job_workflow():
    """Test the complete job workflow"""
    print("🚀 Testing Job Management Workflow")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Register and authenticate
    print("\n1. Authentication...")
    
    # Register user
    register_data = {
        "username": "testuser_jobs",
        "email": "testjobs@example.com", 
        "password": "TestPass123",
        "confirm_password": "TestPass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = session.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code == 201:
        print("✅ User registration successful")
    else:
        print(f"⚠️  User already exists or registration failed: {response.status_code}")
    
    # Login
    login_data = {
        "email": "testjobs@example.com",
        "password": "TestPass123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        session.headers.update({
            'Authorization': f'Bearer {data["access_token"]}'
        })
        print("✅ Authentication successful")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return False
    
    # Step 2: Create an asset
    print("\n2. Creating test asset...")
    
    test_content = "This is a test script for job testing"
    files = {
        'file': ('test_script.txt', BytesIO(test_content.encode()), 'text/plain')
    }
    data = {
        'asset_type': 'script',
        'description': 'Test script for job testing'
    }
    
    # Remove Content-Type to let requests handle multipart
    headers = session.headers.copy()
    if 'Content-Type' in headers:
        del headers['Content-Type']
    
    response = session.post(f"{API_BASE}/assets/upload", files=files, data=data, headers=headers)
    
    if response.status_code == 201:
        asset_data = response.json()
        asset_id = asset_data['asset']['id']
        print(f"✅ Asset created successfully: {asset_id}")
    else:
        print(f"❌ Asset creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Step 3: Create a job
    print("\n3. Creating job...")
    
    job_data = {
        "title": "Test Voice Clone Job",
        "description": "Test job for voice cloning workflow",
        "job_type": "voice_clone",
        "parameters": {
            "voice_type": "male",
            "quality": "high",
            "speed": 1.0
        },
        "asset_ids": [asset_id]
    }
    
    response = session.post(f"{API_BASE}/jobs/", json=job_data)
    
    if response.status_code == 201:
        job_response = response.json()
        job = job_response['job']
        job_id = job['id']
        print(f"✅ Job created successfully: {job_id}")
        print(f"   Title: {job['title']}")
        print(f"   Status: {job['status']}")
        print(f"   Type: {job['job_type']}")
        print(f"   Asset IDs: {job.get('asset_ids', [])}")
    else:
        print(f"❌ Job creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Step 4: List jobs
    print("\n4. Listing jobs...")
    
    response = session.get(f"{API_BASE}/jobs/")
    if response.status_code == 200:
        jobs_data = response.json()
        print(f"✅ Listed {len(jobs_data['jobs'])} jobs")
        for job in jobs_data['jobs']:
            print(f"   Job {job['id']}: {job['title']} ({job['status']})")
    else:
        print(f"❌ Job listing failed: {response.status_code}")
    
    # Step 5: Get job details  
    print("\n5. Getting job details...")
    
    response = session.get(f"{API_BASE}/jobs/{job_id}")
    if response.status_code == 200:
        job_detail = response.json()
        job = job_detail.get('job', job_detail)  # Handle both response formats
        print(f"✅ Job details retrieved")
        print(f"   Title: {job['title']}")
        print(f"   Status: {job['status']}")
        print(f"   Progress: {job.get('progress_percentage', 0)}%")
        if 'asset_ids' in job:
            print(f"   Assets: {job['asset_ids']}")
    else:
        print(f"❌ Job details failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Step 6: Cleanup
    print("\n6. Cleanup...")
    
    # Delete asset
    response = session.delete(f"{API_BASE}/assets/{asset_id}")
    if response.status_code == 204:
        print(f"✅ Asset {asset_id} deleted")
    else:
        print(f"⚠️  Asset deletion: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 Job workflow test completed!")
    return True

if __name__ == "__main__":
    test_job_workflow()
