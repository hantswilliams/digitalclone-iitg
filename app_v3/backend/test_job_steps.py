#!/usr/bin/env python3
"""
Job Step Management Test - Demonstrating JobStep functionality
Tests creating and managing individual steps within jobs
"""
import requests
import json
import time

# API configuration
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_USER = {
    "username": f"steptest_user_{int(time.time())}",
    "email": f"steptest_{int(time.time())}@example.com", 
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "Step",
    "last_name": "Tester",
    "department": "Engineering",
    "title": "Test Engineer",
    "role": "faculty"
}

def print_status(message, success=True):
    """Print formatted status message"""
    prefix = "✅" if success else "❌"
    print(f"{prefix} {message}")

def register_and_login():
    """Register test user and get JWT token"""
    print("🔐 Setting up authentication...")
    
    # Register user
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=TEST_USER)
        if response.status_code == 201:
            print_status("User registered")
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

def create_test_job(token):
    """Create a test job for step management"""
    print("\n📋 Creating test job...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    job_data = {
        "title": "Full Pipeline Test Job",
        "description": "Testing job step management",
        "job_type": "full_pipeline",
        "priority": "normal",
        "parameters": {
            "mode": "complete",
            "steps": [
                "voice_clone",
                "text_to_speech", 
                "video_generation",
                "final_assembly"
            ]
        },
        "estimated_duration": 600
    }
    
    try:
        response = requests.post(f"{API_BASE}/jobs/", json=job_data, headers=headers)
        
        if response.status_code == 201:
            job = response.json()["job"]
            print_status(f"Job created (ID: {job['id']})")
            return job
        else:
            print_status(f"Job creation failed: {response.text}", False)
            return None
    except Exception as e:
        print_status(f"Job creation error: {e}", False)
        return None

def simulate_job_processing(token, job_id):
    """Simulate job processing with step updates"""
    print(f"\n⚙️ Simulating job processing for Job {job_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Define the steps for our pipeline
    steps = [
        {
            "name": "Voice Clone Preparation",
            "description": "Analyzing voice sample and preparing clone model",
            "estimated_duration": 120
        },
        {
            "name": "Text to Speech Generation", 
            "description": "Converting script text to speech using cloned voice",
            "estimated_duration": 180
        },
        {
            "name": "Video Generation",
            "description": "Creating talking head video with generated speech",
            "estimated_duration": 240
        },
        {
            "name": "Final Assembly",
            "description": "Combining elements and exporting final video",
            "estimated_duration": 60
        }
    ]
    
    # Process each step with progress updates
    total_duration = sum(step["estimated_duration"] for step in steps)
    elapsed_time = 0
    
    for i, step in enumerate(steps):
        print(f"\n  📝 Step {i+1}: {step['name']}")
        
        # Simulate step processing
        step_duration = step["estimated_duration"]
        progress_increments = 3  # Number of progress updates per step
        
        for j in range(progress_increments):
            # Calculate overall progress
            step_progress = (j + 1) / progress_increments
            overall_progress = (elapsed_time + (step_progress * step_duration)) / total_duration * 100
            
            # Update job progress
            try:
                progress_data = {
                    "progress_percentage": int(overall_progress),
                    "message": f"Processing {step['name']}: {int(step_progress * 100)}%"
                }
                response = requests.put(f"{API_BASE}/jobs/{job_id}/progress", 
                                       json=progress_data, headers=headers)
                
                if response.status_code == 200:
                    print(f"    🔄 Progress: {int(overall_progress)}% - {progress_data['message']}")
                else:
                    print_status(f"Progress update failed: {response.text}", False)
                    
            except Exception as e:
                print_status(f"Progress update error: {e}", False)
            
            # Small delay to simulate work
            time.sleep(0.3)
        
        elapsed_time += step_duration
        print_status(f"Step {i+1} completed")
    
    # Final progress update
    try:
        progress_data = {
            "progress_percentage": 100,
            "message": "Job completed successfully"
        }
        response = requests.put(f"{API_BASE}/jobs/{job_id}/progress", 
                               json=progress_data, headers=headers)
        
        if response.status_code == 200:
            print_status("🎉 Job processing simulation completed!")
        else:
            print_status(f"Final progress update failed: {response.text}", False)
            
    except Exception as e:
        print_status(f"Error with final progress update: {e}", False)

def check_final_job_status(token, job_id):
    """Check the final status of the processed job"""
    print(f"\n📊 Final job status check...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/jobs/{job_id}", headers=headers)
        
        if response.status_code == 200:
            job = response.json()["job"]
            print_status(f"Job Status: {job['status']}")
            print(f"    📈 Progress: {job['progress_percentage']}%")
            print(f"    ⏱️ Duration: {job.get('duration', 'N/A')} seconds")
            print(f"    📅 Created: {job['created_at']}")
            print(f"    ✅ Completed: {job.get('completed_at', 'N/A')}")
            
            if job.get('results'):
                print(f"    📁 Results: {job['results']}")
                
            if job.get('steps'):
                print(f"    📋 Steps: {len(job['steps'])} recorded")
        else:
            print_status(f"Failed to get job status: {response.text}", False)
            
    except Exception as e:
        print_status(f"Error checking job status: {e}", False)

def main():
    """Demonstrate job step management"""
    print("=" * 60)
    print("  Job Step Management Demonstration")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    
    # Step 1: Authentication
    token = register_and_login()
    if not token:
        print_status("Authentication failed, cannot continue", False)
        return
    
    # Step 2: Create test job
    job = create_test_job(token)
    if not job:
        print_status("Job creation failed", False)
        return
    
    job_id = job["id"]
    
    # Step 3: Simulate job processing with steps
    simulate_job_processing(token, job_id)
    
    # Step 4: Check final status
    check_final_job_status(token, job_id)
    
    print("\n" + "=" * 60)
    print_status("Job Step Management demonstration completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
