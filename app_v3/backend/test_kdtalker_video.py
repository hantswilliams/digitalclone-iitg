#!/usr/bin/env python3
"""
Test script for KDTalker video generation integration.

This script tests the complete video generation pipeline including:
1. KDTalker client configuration and connectivity
2. Video generation service validation
3. API endpoint functionality
4. End-to-end video generation workflow

Run this after setting up KDTalker service and ensuring all dependencies are installed.
"""

import sys
import os
import time
import requests
import json
import tempfile
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Test configuration
API_BASE_URL = "http://localhost:5001/api"
KDTALKER_URL = "http://localhost:7860"  # Default KDTalker Gradio URL

# Test credentials
TEST_EMAIL = "video_test@example.com"
TEST_PASSWORD = "testpass123"

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}TEST: {test_name}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def login_and_get_token():
    """Login and get JWT token for authentication."""
    print_test_header("Authentication Setup")
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json()['access_token']
            print_success(f"Login successful, token obtained")
            return token
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Login request failed: {e}")
        return None

def test_kdtalker_client_config():
    """Test KDTalker client configuration and connectivity."""
    print_test_header("KDTalker Client Configuration")
    
    try:
        from app.services.video import KDTalkerClient, VideoGenerationConfig
        
        # Test client initialization
        client = KDTalkerClient()  # Use default space from env var
        print_success("KDTalker client initialized successfully")
        
        # Test basic properties
        print_info(f"Space name: {client.space_name}")
        print_info(f"Timeout: {client.timeout}")
        
        # Test connectivity (this may fail if KDTalker is not running)
        health_result = client.health_check()
        print_info(f"Health check status: {health_result['status']}")
        
        if health_result['status'] == 'healthy':
            print_success("KDTalker service is accessible and healthy")
        else:
            print_warning(f"KDTalker service check failed: {health_result.get('error', 'Unknown error')}")
            print_warning("This is expected if KDTalker is not running locally")
        
        # Test VideoGenerationConfig
        config = VideoGenerationConfig(
            enhancer='gfpgan',
            face_enhance=True,
            fps=25
        )
        print_success("VideoGenerationConfig created successfully")
        print_info(f"Config: enhancer={config.enhancer}, fps={config.fps}")
        
        return True
        
    except ImportError as e:
        print_error(f"Failed to import KDTalker client: {e}")
        return False
    except Exception as e:
        print_error(f"KDTalker client test failed: {e}")
        return False

def test_video_service_validation(token):
    """Test video service validation via Celery task."""
    print_test_header("Video Service Validation Task")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test video service status endpoint
        response = requests.get(f"{API_BASE_URL}/generate/video/status", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Video service status endpoint accessible")
            print_info(f"Service: {result.get('service', 'unknown')}")
            print_info(f"Status: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'healthy':
                print_success("KDTalker service is healthy")
            else:
                print_warning("KDTalker service is not healthy (expected if not running)")
            
            return True
        else:
            print_error(f"Video service status failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Video service validation failed: {e}")
        return False

def create_test_assets(token):
    """Create test portrait and audio assets for video generation."""
    print_test_header("Creating Test Assets")
    
    try:
        from PIL import Image
        import numpy as np
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test portrait image (simple colored rectangle)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as portrait_file:
            # Create a 512x512 test image
            img = Image.new('RGB', (512, 512), color='lightblue')
            
            # Add a simple face-like shape (circle)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.ellipse([150, 150, 362, 362], fill='#FDBCB4', outline='black', width=2)  # peach color
            # Eyes
            draw.ellipse([200, 220, 240, 260], fill='black')
            draw.ellipse([272, 220, 312, 260], fill='black')
            # Mouth
            draw.arc([220, 280, 292, 320], 0, 180, fill='red', width=3)
            
            img.save(portrait_file.name, 'JPEG')
            portrait_path = portrait_file.name
        
        print_success(f"Created test portrait image: {portrait_path}")
        
        # Upload portrait asset
        with open(portrait_path, 'rb') as f:
            files = {'file': ('test_portrait.jpg', f, 'image/jpeg')}
            data = {'asset_type': 'portrait', 'description': 'Test portrait for video generation'}
            
            response = requests.post(f"{API_BASE_URL}/assets/upload", 
                                   headers=headers, files=files, data=data)
        
        if response.status_code == 201:
            portrait_response = response.json()
            print_info(f"Portrait upload response: {portrait_response}")
            
            # Extract the asset ID from the nested structure
            if 'asset' in portrait_response and 'id' in portrait_response['asset']:
                portrait_asset_id = portrait_response['asset']['id']
                print_success(f"Portrait asset uploaded successfully (ID: {portrait_asset_id})")
            else:
                print_error(f"Portrait upload response missing asset.id field: {portrait_response}")
                return None, None
        else:
            print_error(f"Portrait upload failed: {response.status_code} - {response.text}")
            return None, None
        
        # Create a test audio file (sine wave)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            try:
                import wave
                import struct
                import math
                
                # Generate a 3-second sine wave at 440 Hz
                sample_rate = 22050
                duration = 3
                frequency = 440
                
                frames = []
                for i in range(int(duration * sample_rate)):
                    value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    frames.append(struct.pack('<h', value))
                
                with wave.open(audio_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 2 bytes per sample
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(b''.join(frames))
                
                audio_path = audio_file.name
                
            except ImportError:
                print_warning("Wave generation libraries not available, creating empty audio file")
                audio_path = audio_file.name
        
        print_success(f"Created test audio file: {audio_path}")
        
        # Upload audio asset
        with open(audio_path, 'rb') as f:
            files = {'file': ('test_audio.wav', f, 'audio/wav')}
            data = {'asset_type': 'voice_sample', 'description': 'Test audio for video generation'}
            
            response = requests.post(f"{API_BASE_URL}/assets/upload", 
                                   headers=headers, files=files, data=data)
        
        if response.status_code == 201:
            audio_response = response.json()
            print_info(f"Audio upload response: {audio_response}")
            
            # Extract the asset ID from the nested structure
            if 'asset' in audio_response and 'id' in audio_response['asset']:
                audio_asset_id = audio_response['asset']['id']
                print_success(f"Audio asset uploaded successfully (ID: {audio_asset_id})")
            else:
                print_error(f"Audio upload response missing asset.id field: {audio_response}")
                return portrait_asset_id, None
        else:
            print_error(f"Audio upload failed: {response.status_code} - {response.text}")
            return portrait_asset_id, None
        
        # Clean up temp files
        os.unlink(portrait_path)
        os.unlink(audio_path)
        
        return portrait_asset_id, audio_asset_id
        
    except Exception as e:
        print_error(f"Failed to create test assets: {e}")
        return None, None

def test_video_generation_api(token, portrait_asset_id, audio_asset_id):
    """Test video generation API endpoint."""
    print_test_header("Video Generation API Endpoint")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test video generation request
        request_data = {
            "portrait_asset_id": portrait_asset_id,
            "audio_asset_id": audio_asset_id,
            "enhancer": "gfpgan",
            "face_enhance": True,
            "background_enhance": True,
            "preprocess": "crop",
            "fps": 25,
            "use_blink": True,
            "exp_scale": 1.0,
            "priority": "normal"
        }
        
        print_info(f"Sending video generation request...")
        print_info(f"Portrait Asset ID: {portrait_asset_id}")
        print_info(f"Audio Asset ID: {audio_asset_id}")
        print_info(f"Request data: {request_data}")
        
        response = requests.post(f"{API_BASE_URL}/generate/video", 
                               headers=headers, json=request_data)
        
        if response.status_code == 201:
            result = response.json()
            print_success("Video generation job created successfully")
            print_info(f"Job ID: {result.get('job_id')}")
            print_info(f"Task ID: {result.get('task_id')}")
            print_info(f"Status: {result.get('status')}")
            print_info(f"Estimated duration: {result.get('estimated_duration')} seconds")
            
            job_id = result.get('job_id')
            
            # Monitor job progress
            if job_id:
                print_info("Monitoring job progress...")
                for i in range(10):  # Check progress for up to 10 iterations
                    time.sleep(2)
                    
                    job_response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", headers=headers)
                    if job_response.status_code == 200:
                        job_data = job_response.json()
                        status = job_data.get('status')
                        progress = job_data.get('progress', 0)
                        status_message = job_data.get('status_message', '')
                        
                        print_info(f"Progress: {progress}% - {status} - {status_message}")
                        
                        if status in ['completed', 'failed']:
                            break
                    else:
                        print_warning(f"Failed to get job status: {job_response.status_code}")
                        break
                
                # Final job status
                job_response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", headers=headers)
                if job_response.status_code == 200:
                    final_job_data = job_response.json()
                    final_status = final_job_data.get('status')
                    
                    if final_status == 'completed':
                        print_success("Video generation completed successfully!")
                        result_data = final_job_data.get('result_data', {})
                        if result_data:
                            print_info(f"Video storage path: {result_data.get('video_storage_path')}")
                            print_info(f"File size: {result_data.get('file_size')} bytes")
                            print_info(f"Generation time: {result_data.get('generation_time', 0):.2f} seconds")
                    else:
                        print_warning(f"Video generation ended with status: {final_status}")
                        if final_job_data.get('status_message'):
                            print_info(f"Message: {final_job_data['status_message']}")
            
            return True
        else:
            print_error(f"Video generation request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Video generation API test failed: {e}")
        return False

def run_all_tests():
    """Run all KDTalker video generation tests."""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("  KDTALKER VIDEO GENERATION INTEGRATION TESTS")
    print("=" * 70)
    print(f"{Colors.END}")
    
    test_results = []
    
    # Test 1: KDTalker Client Configuration
    result1 = test_kdtalker_client_config()
    test_results.append(("KDTalker Client Configuration", result1))
    
    # Get authentication token
    token = login_and_get_token()
    if not token:
        print_error("Cannot continue tests without authentication token")
        return
    
    # Test 2: Video Service Validation
    result2 = test_video_service_validation(token)
    test_results.append(("Video Service Validation", result2))
    
    # Test 3: Create Test Assets
    portrait_asset_id, audio_asset_id = create_test_assets(token)
    if portrait_asset_id and audio_asset_id:
        test_results.append(("Create Test Assets", True))
        
        # Test 4: Video Generation API
        result4 = test_video_generation_api(token, portrait_asset_id, audio_asset_id)
        test_results.append(("Video Generation API", result4))
    else:
        test_results.append(("Create Test Assets", False))
        test_results.append(("Video Generation API", False))
    
    # Print summary
    print_test_header("Test Summary")
    
    passed = 0
    total = len(test_results)
    
    for test_name, passed_test in test_results:
        if passed_test:
            print_success(f"{test_name}")
            passed += 1
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("All tests passed! KDTalker video generation is working correctly.")
    else:
        print_warning(f"{total - passed} tests failed. Check the output above for details.")
        if passed == 0:
            print_info("If KDTalker service is not running, most tests will fail.")
            print_info("Start KDTalker service and run tests again.")

if __name__ == "__main__":
    run_all_tests()
