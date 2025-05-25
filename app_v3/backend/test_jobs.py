#!/usr/bin/env python3
"""
Test script for job management API endpoints.
This script tests all job-related functionality including CRUD operations,
progress tracking, step management, and error handling.
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# Configuration
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

class JobTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_jobs = []
        self.created_assets = []
        self.access_token = None
        
    def authenticate(self):
        """Authenticate with the API and get access token"""
        test_name = "Authentication"
        try:
            # Try to register a test user first
            register_data = {
                "email": "testuser@example.com",
                "username": "testuser",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
                "department": "Engineering",
                "role": "faculty"
            }
            
            # Try registration (might fail if user exists)
            response = self.session.post(f"{API_BASE}/auth/register", json=register_data)
            
            if response.status_code not in [201, 409]:  # 409 = user already exists
                self.log_test(test_name, False, f"Registration failed with status: {response.status_code}")
                return False
            
            # Login with the test user
            login_data = {
                "email": "testuser@example.com",
                "password": "TestPassword123!"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                
                # Set authorization header for future requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                self.log_test(test_name, True, "Successfully authenticated")
                return True
            else:
                self.log_test(test_name, False, f"Login failed: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def create_test_asset(self):
        """Create a test asset for job testing"""
        try:
            # Create a simple test file content
            test_content = "This is a test script for job testing"
            
            # Prepare multipart form data
            from io import BytesIO
            files = {
                'file': ('test_script.txt', BytesIO(test_content.encode()), 'text/plain')
            }
            data = {
                'asset_type': 'script',
                'description': 'Test script for job testing'
            }
            
            # Remove Content-Type header to let requests handle multipart
            headers = self.session.headers.copy()
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            response = self.session.post(
                f"{API_BASE}/assets/upload", 
                files=files, 
                data=data,
                headers=headers
            )
            
            if response.status_code == 201:
                asset = response.json()['asset']
                self.created_assets.append(asset['id'])
                print(f"Created test asset: {asset['id']}")
                return asset['id']
            else:
                print(f"Failed to create test asset: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error creating test asset: {e}")
            return None
    
    def test_create_job(self):
        """Test job creation"""
        test_name = "Create Job"
        try:
            # First create a test asset
            asset_id = self.create_test_asset()
            if not asset_id:
                self.log_test(test_name, False, "Failed to create test asset")
                return None
                
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
            
            response = self.session.post(f"{API_BASE}/jobs/", json=job_data)
            
            if response.status_code == 201:
                response_data = response.json()
                job = response_data['job']  # Extract job from response wrapper
                self.created_jobs.append(job['id'])
                
                # Validate response structure
                required_fields = ['id', 'title', 'status', 'job_type', 'created_at', 'asset_ids']
                missing_fields = [field for field in required_fields if field not in job]
                
                if missing_fields:
                    self.log_test(test_name, False, f"Missing fields: {missing_fields}")
                    return None
                
                # Validate status is pending
                if job['status'] != 'pending':
                    self.log_test(test_name, False, f"Expected status 'pending', got '{job['status']}'")
                    return None
                    
                # Validate asset association
                if len(job['asset_ids']) != 1 or job['asset_ids'][0] != asset_id:
                    self.log_test(test_name, False, "Asset not properly associated")
                    return None
                
                self.log_test(test_name, True, f"Created job with ID: {job['id']}")
                return job['id']
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return None
    
    def test_get_job(self, job_id):
        """Test getting a specific job"""
        test_name = "Get Job Details"
        try:
            response = self.session.get(f"{API_BASE}/jobs/{job_id}")
            
            if response.status_code == 200:
                job = response.json()
                
                # Validate job structure
                required_fields = ['id', 'name', 'status', 'job_type', 'created_at', 'assets', 'steps']
                missing_fields = [field for field in required_fields if field not in job]
                
                if missing_fields:
                    self.log_test(test_name, False, f"Missing fields: {missing_fields}")
                    return False
                
                if job['id'] != job_id:
                    self.log_test(test_name, False, f"ID mismatch: expected {job_id}, got {job['id']}")
                    return False
                
                self.log_test(test_name, True, f"Retrieved job: {job['name']}")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_list_jobs(self):
        """Test listing jobs with pagination"""
        test_name = "List Jobs"
        try:
            # Test basic listing
            response = self.session.get(f"{API_BASE}/jobs/")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['jobs', 'pagination']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(test_name, False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate pagination structure
                pagination_fields = ['page', 'per_page', 'total', 'pages']
                missing_pagination = [field for field in pagination_fields if field not in data['pagination']]
                
                if missing_pagination:
                    self.log_test(test_name, False, f"Missing pagination fields: {missing_pagination}")
                    return False
                
                job_count = len(data['jobs'])
                total = data['pagination']['total']
                
                self.log_test(test_name, True, f"Listed {job_count} jobs, total: {total}")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_update_job(self, job_id):
        """Test updating job properties"""
        test_name = "Update Job"
        try:
            update_data = {
                "name": "Updated Test Job",
                "description": "Updated description for test job",
                "configuration": {
                    "voice_type": "female",
                    "quality": "medium",
                    "speed": 1.2
                }
            }
            
            response = self.session.put(f"{API_BASE}/jobs/{job_id}", json=update_data)
            
            if response.status_code == 200:
                job = response.json()
                
                # Validate updates were applied
                if job['name'] != update_data['name']:
                    self.log_test(test_name, False, f"Name not updated: expected '{update_data['name']}', got '{job['name']}'")
                    return False
                
                if job['description'] != update_data['description']:
                    self.log_test(test_name, False, f"Description not updated")
                    return False
                
                self.log_test(test_name, True, f"Updated job: {job['name']}")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_update_job_progress(self, job_id):
        """Test updating job progress"""
        test_name = "Update Job Progress"
        try:
            progress_data = {
                "status": "running",
                "progress": 45.5,
                "current_step": "Generating voice model",
                "estimated_completion": "2024-01-01T15:30:00Z"
            }
            
            response = self.session.put(f"{API_BASE}/jobs/{job_id}/progress", json=progress_data)
            
            if response.status_code == 200:
                job = response.json()
                
                # Validate progress updates
                if job['status'] != progress_data['status']:
                    self.log_test(test_name, False, f"Status not updated")
                    return False
                
                if abs(job['progress'] - progress_data['progress']) > 0.1:
                    self.log_test(test_name, False, f"Progress not updated correctly")
                    return False
                
                self.log_test(test_name, True, f"Progress updated: {job['progress']}% - {job['current_step']}")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_create_job_step(self, job_id):
        """Test creating a job step"""
        test_name = "Create Job Step"
        try:
            step_data = {
                "name": "Voice Model Training",
                "description": "Training the voice cloning model",
                "step_order": 1,
                "input_data": {
                    "audio_files": ["voice_sample_1.wav", "voice_sample_2.wav"],
                    "training_params": {
                        "epochs": 100,
                        "batch_size": 32
                    }
                }
            }
            
            response = self.session.post(f"{API_BASE}/jobs/{job_id}/steps", json=step_data)
            
            if response.status_code == 201:
                step = response.json()
                
                # Validate step structure
                required_fields = ['id', 'name', 'status', 'step_order', 'created_at']
                missing_fields = [field for field in required_fields if field not in step]
                
                if missing_fields:
                    self.log_test(test_name, False, f"Missing fields: {missing_fields}")
                    return None
                
                if step['status'] != 'pending':
                    self.log_test(test_name, False, f"Expected status 'pending', got '{step['status']}'")
                    return None
                
                self.log_test(test_name, True, f"Created step: {step['name']}")
                return step['id']
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return None
    
    def test_get_job_steps(self, job_id):
        """Test getting job steps"""
        test_name = "Get Job Steps"
        try:
            response = self.session.get(f"{API_BASE}/jobs/{job_id}/steps")
            
            if response.status_code == 200:
                steps = response.json()
                
                if not isinstance(steps, list):
                    self.log_test(test_name, False, "Response should be a list")
                    return False
                
                if len(steps) > 0:
                    # Validate step structure
                    step = steps[0]
                    required_fields = ['id', 'name', 'status', 'step_order']
                    missing_fields = [field for field in required_fields if field not in step]
                    
                    if missing_fields:
                        self.log_test(test_name, False, f"Missing step fields: {missing_fields}")
                        return False
                
                self.log_test(test_name, True, f"Retrieved {len(steps)} steps")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_cancel_job(self, job_id):
        """Test canceling a job"""
        test_name = "Cancel Job"
        try:
            response = self.session.post(f"{API_BASE}/jobs/{job_id}/cancel")
            
            if response.status_code == 200:
                job = response.json()
                
                if job['status'] != 'cancelled':
                    self.log_test(test_name, False, f"Expected status 'cancelled', got '{job['status']}'")
                    return False
                
                self.log_test(test_name, True, f"Job cancelled successfully")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_filter_jobs(self):
        """Test job filtering"""
        test_name = "Filter Jobs"
        try:
            # Test filtering by status
            response = self.session.get(f"{API_BASE}/jobs/?status=cancelled")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data['jobs']
                
                # Check that all returned jobs have cancelled status
                non_cancelled = [job for job in jobs if job['status'] != 'cancelled']
                
                if non_cancelled:
                    self.log_test(test_name, False, f"Found {len(non_cancelled)} non-cancelled jobs in filtered results")
                    return False
                
                self.log_test(test_name, True, f"Filter working: {len(jobs)} cancelled jobs")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def test_pagination(self):
        """Test pagination functionality"""
        test_name = "Pagination"
        try:
            # Test with specific page size
            response = self.session.get(f"{API_BASE}/jobs/?per_page=1&page=1")
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data['jobs']) > 1:
                    self.log_test(test_name, False, f"Expected 1 job per page, got {len(data['jobs'])}")
                    return False
                
                if data['pagination']['per_page'] != 1:
                    self.log_test(test_name, False, f"Pagination per_page incorrect")
                    return False
                
                self.log_test(test_name, True, "Pagination working correctly")
                return True
            else:
                self.log_test(test_name, False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Clean up jobs (this should also clean up associated steps due to cascade)
        for job_id in self.created_jobs:
            try:
                response = self.session.delete(f"{API_BASE}/jobs/{job_id}")
                if response.status_code in [200, 204, 404]:
                    print(f"   Deleted job {job_id}")
                else:
                    print(f"   Failed to delete job {job_id}: {response.status_code}")
            except Exception as e:
                print(f"   Error deleting job {job_id}: {e}")
        
        # Clean up assets
        for asset_id in self.created_assets:
            try:
                response = self.session.delete(f"{API_BASE}/assets/{asset_id}")
                if response.status_code in [200, 204, 404]:
                    print(f"   Deleted asset {asset_id}")
                else:
                    print(f"   Failed to delete asset {asset_id}: {response.status_code}")
            except Exception as e:
                print(f"   Error deleting asset {asset_id}: {e}")
    
    def run_all_tests(self):
        """Run all job management tests"""
        print("🚀 Starting Job Management API Tests")
        print("=" * 50)
        
        # First authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Test basic CRUD operations
        job_id = self.test_create_job()
        
        if job_id:
            self.test_get_job(job_id)
            self.test_update_job(job_id)
            self.test_update_job_progress(job_id)
            
            # Test step management
            step_id = self.test_create_job_step(job_id)
            if step_id:
                self.test_get_job_steps(job_id)
            
            # Test job cancellation
            self.test_cancel_job(job_id)
        
        # Test listing and filtering
        self.test_list_jobs()
        self.test_filter_jobs()
        self.test_pagination()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['test']}")
            if not result['success'] and result['details']:
                print(f"     {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return passed == total

def main():
    """Main function"""
    tester = JobTester()
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/jobs/", timeout=5)
        if response.status_code not in [200, 401, 403]:
            print(f"❌ Server connectivity check failed. Status: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server. Make sure the Flask app is running on http://localhost:5001. Error: {e}")
        sys.exit(1)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
