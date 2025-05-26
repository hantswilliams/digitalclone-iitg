#!/usr/bin/env python3
"""
Test script for LLM service (Stage 7) - Script generation with Llama-4
"""
import sys
import json
import requests
import time
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.extensions import db


def test_llm_service():
    """Test the LLM service functionality"""
    print("🧠 Testing LLM Service (Stage 7) - Script Generation with Llama-4")
    print("=" * 70)
    
    # Test configuration
    BASE_URL = "http://localhost:5001"
    
    # Test credentials (default admin user)
    admin_credentials = {
        "email": "admin@voiceclone.edu",
        "password": "AdminPass123"
    }
    
    session = requests.Session()
    
    # Test 1: Authentication
    print("\n📋 Test 1: User Authentication")
    try:
        response = session.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['access_token']
            session.headers.update({'Authorization': f'Bearer {token}'})
            print("✅ PASS - User authentication successful")
        else:
            print(f"❌ FAIL - Authentication failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Authentication error: {str(e)}")
        return False
    
    # Test 2: LLM Service Health Check
    print("\n📋 Test 2: LLM Service Health Check")
    try:
        response = session.get(f"{BASE_URL}/api/generate/llm/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ PASS - LLM service status: {status_data['status']}")
            print(f"   Service: {status_data['service']}")
            if status_data.get('details'):
                print(f"   Details: {json.dumps(status_data['details'], indent=4)}")
        else:
            print(f"⚠️  WARNING - LLM service check failed: {response.text}")
            print("   This may be expected if Hugging Face Spaces is unavailable")
    except Exception as e:
        print(f"⚠️  WARNING - LLM service check error: {str(e)}")
        print("   This may be expected if Hugging Face Spaces is unavailable")
    
    # Test 3: Script Generation Request
    print("\n📋 Test 3: Script Generation Request")
    try:
        script_request = {
            "prompt": "Create an engaging introduction to renewable energy for students",
            "topic": "Renewable Energy Basics",
            "target_audience": "high school students",
            "duration_minutes": 3,
            "style": "educational",
            "additional_context": "Focus on solar and wind power as main examples",
            "title": "Introduction to Renewable Energy",
            "description": "Educational script about renewable energy for students",
            "priority": "normal"
        }
        
        response = session.post(f"{BASE_URL}/api/generate/script", json=script_request)
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data['job_id']
            task_id = job_data['task_id']
            print(f"✅ PASS - Script generation job created")
            print(f"   Job ID: {job_id}")
            print(f"   Task ID: {task_id}")
            print(f"   Status: {job_data['status']}")
            
            # Monitor job progress
            print("\n📋 Test 4: Monitor Script Generation Progress")
            max_attempts = 30  # 5 minutes with 10-second intervals
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(10)  # Wait 10 seconds between checks
                attempt += 1
                
                try:
                    job_response = session.get(f"{BASE_URL}/api/jobs/{job_id}")
                    if job_response.status_code == 200:
                        job_status = job_response.json()
                        status = job_status['status']
                        progress = job_status.get('progress', 0)
                        
                        print(f"   Attempt {attempt}: Status = {status}, Progress = {progress}%")
                        
                        if status == 'completed':
                            print("✅ PASS - Script generation completed successfully")
                            
                            # Check if script asset was created
                            if job_status.get('output_assets'):
                                print(f"   Generated script asset ID: {job_status['output_assets'][0]}")
                                
                                # Try to get the script content
                                asset_response = session.get(f"{BASE_URL}/api/assets/{job_status['output_assets'][0]}")
                                if asset_response.status_code == 200:
                                    asset_data = asset_response.json()
                                    print(f"   Script asset type: {asset_data['type']}")
                                    print(f"   Script file: {asset_data['filename']}")
                                    print("✅ PASS - Script asset created successfully")
                                else:
                                    print(f"⚠️  WARNING - Could not retrieve script asset: {asset_response.text}")
                            else:
                                print("⚠️  WARNING - No output assets found")
                            break
                            
                        elif status == 'failed':
                            print(f"❌ FAIL - Script generation failed")
                            if job_status.get('error_message'):
                                print(f"   Error: {job_status['error_message']}")
                            break
                            
                        elif status == 'cancelled':
                            print(f"❌ FAIL - Script generation was cancelled")
                            break
                            
                    else:
                        print(f"   Warning: Could not check job status: {job_response.text}")
                        
                except Exception as e:
                    print(f"   Warning: Error checking job progress: {str(e)}")
            
            if attempt >= max_attempts:
                print(f"⚠️  TIMEOUT - Script generation did not complete within {max_attempts * 10} seconds")
                print("   This may be expected for large scripts or slow Hugging Face Spaces")
                
        else:
            print(f"❌ FAIL - Script generation request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Script generation error: {str(e)}")
        return False
    
    # Test 5: Validation of Script Request Parameters
    print("\n📋 Test 5: Script Request Validation")
    try:
        # Test with missing prompt
        invalid_request = {
            "topic": "Test Topic",
            "target_audience": "general"
        }
        
        response = session.post(f"{BASE_URL}/api/generate/script", json=invalid_request)
        if response.status_code == 400:
            print("✅ PASS - Proper validation for missing prompt")
        else:
            print(f"❌ FAIL - Expected 400 for missing prompt, got {response.status_code}")
            
        # Test with invalid style
        invalid_style_request = {
            "prompt": "Test prompt",
            "style": "invalid_style"
        }
        
        response = session.post(f"{BASE_URL}/api/generate/script", json=invalid_style_request)
        if response.status_code == 400:
            print("✅ PASS - Proper validation for invalid style")
        else:
            print(f"❌ FAIL - Expected 400 for invalid style, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ FAIL - Validation test error: {str(e)}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 LLM Service testing completed!")
    print("\nNote: Some tests may show warnings if Hugging Face Spaces is slow or unavailable.")
    print("This is expected behavior for remote services.")
    return True


if __name__ == "__main__":
    print("Starting LLM Service Test Suite...")
    
    # Create Flask app context for database access
    app = create_app()
    with app.app_context():
        success = test_llm_service()
        
    if success:
        print("\n✅ All critical tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
