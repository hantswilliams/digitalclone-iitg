#!/usr/bin/env python3
"""
Quick test for LLM service functionality
"""
import sys
import json
import requests
import time
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def quick_llm_test():
    """Quick test of LLM service endpoints"""
    print("🧠 Quick LLM Service Test")
    print("=" * 50)
    
    BASE_URL = "http://localhost:5001"
    
    # Admin credentials
    admin_credentials = {
        "email": "admin@voiceclone.edu",
        "password": "AdminPass123"
    }
    
    session = requests.Session()
    
    # Test 1: Authentication
    print("\n📋 Test 1: Authentication")
    try:
        response = session.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['access_token']
            session.headers.update({'Authorization': f'Bearer {token}'})
            print("✅ PASS - Authentication successful")
        else:
            print(f"❌ FAIL - Authentication failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Authentication error: {str(e)}")
        return False
    
    # Test 2: Script Generation Request
    print("\n📋 Test 2: Script Generation Request")
    try:
        script_request = {
            "prompt": "Create a short introduction about artificial intelligence",
            "topic": "AI Basics",
            "target_audience": "beginners",
            "duration_minutes": 2,
            "style": "educational",
            "title": "AI Introduction Script",
            "description": "Brief intro to AI concepts",
            "priority": "normal"
        }
        
        response = session.post(f"{BASE_URL}/api/generate/script", json=script_request)
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data['job_id']
            print(f"✅ PASS - Script generation job created (ID: {job_id})")
            
            # Quick status check
            time.sleep(2)
            job_response = session.get(f"{BASE_URL}/api/jobs/{job_id}")
            if job_response.status_code == 200:
                job_data = job_response.json()
                job_status = job_data['job']  # Job data is nested under 'job' key
                print(f"   Job Status: {job_status['status']}")
                print(f"   Job Type: {job_status['job_type']}")
                print("✅ PASS - Job created and trackable")
            else:
                print(f"⚠️  Warning: Could not check job status")
                
        else:
            print(f"❌ FAIL - Script generation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Script generation error: {str(e)}")
        return False
    
    # Test 3: Validation Check
    print("\n📋 Test 3: Request Validation")
    try:
        # Test missing prompt
        invalid_request = {"topic": "Test"}
        response = session.post(f"{BASE_URL}/api/generate/script", json=invalid_request)
        if response.status_code == 400:
            print("✅ PASS - Proper validation for missing prompt")
        else:
            print(f"❌ FAIL - Expected 400, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ FAIL - Validation test error: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Quick LLM test completed successfully!")
    return True

if __name__ == "__main__":
    success = quick_llm_test()
    sys.exit(0 if success else 1)
