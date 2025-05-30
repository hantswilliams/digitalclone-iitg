#!/usr/bin/env python3
"""
Comprehensive test script for Job Schema (Stage 3)
Tests job creation, updates, progress tracking, and step management
"""
import requests
import json
import time
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "username": f"jobtest_user_{int(time.time())}",  # Make username unique
    "email": f"jobtest_{int(time.time())}@example.com", 
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "Job",
    "last_name": "Tester",
    "department": "Engineering",
    "title": "Test Engineer",
    "role": "faculty"
}

def print_status(message, success=True):
    """Print formatted status message"""
    prefix = "✅" if success else "❌"
    print(f"{prefix} {message}")

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def register_and_login():
    """Register test user and get JWT token"""
    print_section("Authentication Setup")
    
    # Register user
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=TEST_USER)
        if response.status_code == 201:
            print_status("User registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            print_status("User already exists, continuing with login")
        else:
            print_status(f"Registration failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Registration error: {e}", False)
        return None
    
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
            print_status("Login successful")
            return token
        else:
            print_status(f"Login failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Login error: {e}", False)
        return None

def test_job_creation(token):
    """Test job creation endpoint"""
    print_section("Job Creation Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Create basic voice clone job
    job_data = {
        "title": "Test Voice Clone Job",
        "description": "Testing voice cloning job creation",
        "job_type": "voice_clone",
        "priority": "normal",
        "parameters": {
            "voice_sample_id": "placeholder",
            "text": "Hello, this is a test voice clone.",
            "language": "en"
        },
        "estimated_duration": 300
    }
    
    try:
        response = requests.post(f"{API_BASE}/jobs/", json=job_data, headers=headers)
        
        if response.status_code == 201:
            job = response.json()["job"]
            print_status(f"Voice clone job created (ID: {job['id']})")
            return job
        else:
            print_status(f"Job creation failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Job creation error: {e}", False)
        return None

def test_job_listing(token):
    """Test job listing with filters"""
    print_section("Job Listing Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: List all jobs
    try:
        response = requests.get(f"{API_BASE}/jobs/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            pagination = data.get("pagination", {})
            print_status(f"Retrieved {len(jobs)} jobs (Total: {pagination.get('total', 0)})")
        else:
            print_status(f"Job listing failed: {response.text}", False)
    except Exception as e:
        print_status(f"Job listing error: {e}", False)
    
    # Test 2: Filter by job type
    try:
        response = requests.get(f"{API_BASE}/jobs/?job_type=voice_clone", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            print_status(f"Voice clone jobs found: {len(jobs)}")
        else:
            print_status(f"Filtered job listing failed: {response.text}", False)
    except Exception as e:
        print_status(f"Filtered job listing error: {e}", False)
    
    # Test 3: Filter by status
    try:
        response = requests.get(f"{API_BASE}/jobs/?status=pending", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            print_status(f"Pending jobs found: {len(jobs)}")
        else:
            print_status(f"Status filtered listing failed: {response.text}", False)
    except Exception as e:
        print_status(f"Status filtered listing error: {e}", False)

def test_job_details(token, job_id):
    """Test getting job details"""
    print_section("Job Details Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/jobs/{job_id}", headers=headers)
        
        if response.status_code == 200:
            job = response.json()["job"]
            print_status(f"Job details retrieved (Status: {job['status']})")
            print(f"   - Title: {job['title']}")
            print(f"   - Type: {job['job_type']}")
            print(f"   - Progress: {job['progress_percentage']}%")
            print(f"   - Steps: {len(job.get('steps', []))}")
            return job
        else:
            print_status(f"Job details failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Job details error: {e}", False)
        return None

def test_job_updates(token, job_id):
    """Test job updates"""
    print_section("Job Update Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Update job priority
    update_data = {
        "priority": "high",
        "description": "Updated description for testing"
    }
    
    try:
        response = requests.put(f"{API_BASE}/jobs/{job_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            job = response.json()["job"]
            print_status(f"Job updated (Priority: {job['priority']})")
        else:
            print_status(f"Job update failed: {response.text}", False)
    except Exception as e:
        print_status(f"Job update error: {e}", False)

def test_create_multiple_jobs(token):
    """Create multiple jobs of different types for testing"""
    print_section("Multiple Job Creation")
    
    headers = {"Authorization": f"Bearer {token}"}
    job_types = [
        {
            "title": "TTS Test Job",
            "job_type": "text_to_speech",
            "priority": "normal",
            "parameters": {"text": "Test TTS generation"}
        },
        {
            "title": "Video Generation Job", 
            "job_type": "video_generation",
            "priority": "high",
            "parameters": {"style": "professional"}
        },
        {
            "title": "Full Pipeline Job",
            "job_type": "full_pipeline", 
            "priority": "low",
            "parameters": {"mode": "complete"}
        }
    ]
    
    created_jobs = []
    
    for job_data in job_types:
        try:
            response = requests.post(f"{API_BASE}/jobs/", json=job_data, headers=headers)
            
            if response.status_code == 201:
                job = response.json()["job"]
                created_jobs.append(job)
                print_status(f"{job_data['job_type']} job created (ID: {job['id']})")
            else:
                print_status(f"Failed to create {job_data['job_type']} job: {response.text}", False)
        except Exception as e:
            print_status(f"Error creating {job_data['job_type']} job: {e}", False)
    
    return created_jobs

def test_job_cancellation(token, job_id):
    """Test job cancellation"""
    print_section("Job Cancellation Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_BASE}/jobs/{job_id}/cancel", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Job cancelled: {data.get('message', 'Success')}")
        else:
            print_status(f"Job cancellation failed: {response.text}", False)
    except Exception as e:
        print_status(f"Job cancellation error: {e}", False)

def test_pagination(token):
    """Test job listing pagination"""
    print_section("Pagination Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different page sizes
    for per_page in [2, 5, 10]:
        try:
            response = requests.get(f"{API_BASE}/jobs/?page=1&per_page={per_page}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get("pagination", {})
                print_status(f"Page 1 with {per_page} items: {len(data.get('jobs', []))} jobs returned")
                print(f"   - Total pages: {pagination.get('pages', 0)}")
                print(f"   - Total items: {pagination.get('total', 0)}")
            else:
                print_status(f"Pagination test failed: {response.text}", False)
        except Exception as e:
            print_status(f"Pagination error: {e}", False)

def test_error_cases(token):
    """Test error handling"""
    print_section("Error Handling Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Invalid job type
    invalid_job = {
        "title": "Invalid Job",
        "job_type": "invalid_type",
        "priority": "normal"
    }
    
    try:
        response = requests.post(f"{API_BASE}/jobs/", json=invalid_job, headers=headers)
        
        if response.status_code == 400:
            print_status("Invalid job type properly rejected")
        else:
            print_status(f"Invalid job type should be rejected: {response.status_code}", False)
    except Exception as e:
        print_status(f"Error test failed: {e}", False)
    
    # Test 2: Missing required fields
    incomplete_job = {
        "title": "Incomplete Job"
        # Missing job_type and priority
    }
    
    try:
        response = requests.post(f"{API_BASE}/jobs/", json=incomplete_job, headers=headers)
        
        if response.status_code == 400:
            print_status("Incomplete job data properly rejected")
        else:
            print_status(f"Incomplete job should be rejected: {response.status_code}", False)
    except Exception as e:
        print_status(f"Incomplete job test failed: {e}", False)
    
    # Test 3: Non-existent job
    try:
        response = requests.get(f"{API_BASE}/jobs/99999", headers=headers)
        
        if response.status_code == 404:
            print_status("Non-existent job properly returns 404")
        else:
            print_status(f"Non-existent job should return 404: {response.status_code}", False)
    except Exception as e:
        print_status(f"Non-existent job test failed: {e}", False)

def main():
    """Run comprehensive job schema tests"""
    print_section("Stage 3: Job Schema Comprehensive Testing")
    print(f"Testing against: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Authentication
    token = register_and_login()
    if not token:
        print_status("Authentication failed, cannot continue", False)
        return
    
    # Step 2: Create initial job
    job = test_job_creation(token)
    if not job:
        print_status("Initial job creation failed", False)
        return
    
    job_id = job["id"]
    
    # Step 3: Test job listing
    test_job_listing(token)
    
    # Step 4: Test job details
    test_job_details(token, job_id)
    
    # Step 5: Test job updates
    test_job_updates(token, job_id)
    
    # Step 6: Create multiple jobs
    additional_jobs = test_create_multiple_jobs(token)
    
    # Step 7: Test pagination
    test_pagination(token)
    
    # Step 8: Test job cancellation (use one of the additional jobs)
    if additional_jobs:
        test_job_cancellation(token, additional_jobs[0]["id"])
    
    # Step 9: Test error cases
    test_error_cases(token)
    
    # Final summary
    print_section("Test Summary")
    print_status("Stage 3 (Job Schema) comprehensive testing completed")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show final job count
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/jobs/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            total_jobs = data.get("pagination", {}).get("total", 0)
            print_status(f"Total jobs in system: {total_jobs}")
    except:
        pass

if __name__ == "__main__":
    main()
