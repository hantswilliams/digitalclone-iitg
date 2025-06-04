#!/usr/bin/env python3
"""
Focused test script for the get_space_metadata function of IndexTTS client.

This script specifically tests the get_space_metadata function with various
scenarios including valid spaces, invalid spaces, and error handling.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tts.indextts_client import IndexTTSClient, IndexTTSAPIError


def test_get_space_metadata_basic():
    """Test basic get_space_metadata functionality."""
    print("🔍 Testing basic get_space_metadata functionality...")
    
    try:
        # Initialize client with default space
        client = IndexTTSClient()
        print(f"   Using space: {client.space_name}")
        
        # Call get_space_metadata
        metadata = client.get_space_metadata()
        
        # Validate response structure
        assert isinstance(metadata, dict), "Metadata should be a dictionary"
        assert 'space_name' in metadata, "Metadata should include space_name"
        assert 'space_url' in metadata, "Metadata should include space_url"
        assert 'metadata_available' in metadata, "Metadata should include metadata_available flag"
        
        print("   ✅ Basic structure validation passed")
        
        # If metadata is available, validate additional fields
        if metadata.get('metadata_available', False):
            expected_fields = ['space_id', 'author', 'created_at', 'sdk']
            for field in expected_fields:
                assert field in metadata, f"Metadata should include {field}"
            print("   ✅ Extended structure validation passed")
            
            # Validate runtime information if present
            if 'runtime' in metadata:
                runtime = metadata['runtime']
                assert isinstance(runtime, dict), "Runtime should be a dictionary"
                assert 'stage' in runtime, "Runtime should include stage"
                assert 'hardware' in runtime, "Runtime should include hardware"
                print("   ✅ Runtime structure validation passed")
        
        print("✅ Basic get_space_metadata test passed")
        return metadata
        
    except Exception as e:
        print(f"❌ Basic get_space_metadata test failed: {str(e)}")
        raise


def test_get_space_metadata_without_hf_api():
    """Test get_space_metadata when HfApi is not available."""
    print("\n🔍 Testing get_space_metadata without HfApi...")
    
    try:
        # Create client
        client = IndexTTSClient()
        
        # Temporarily disable HfApi
        original_hf_api = client.hf_api
        client.hf_api = None
        
        # Call get_space_metadata
        metadata = client.get_space_metadata()
        
        # Should return error metadata
        assert isinstance(metadata, dict), "Should return dictionary"
        assert 'error' in metadata, "Should include error field"
        assert metadata['error'] == 'HfApi not available', "Should have correct error message"
        assert metadata['metadata_available'] == False, "Should mark metadata as not available"
        
        # Restore original HfApi
        client.hf_api = original_hf_api
        
        print("✅ get_space_metadata without HfApi test passed")
        return metadata
        
    except Exception as e:
        print(f"❌ get_space_metadata without HfApi test failed: {str(e)}")
        raise


def test_get_space_metadata_with_invalid_space():
    """Test get_space_metadata with an invalid space name."""
    print("\n🔍 Testing get_space_metadata with invalid space...")
    
    try:
        # Create client with invalid space name
        # Note: This might fail during client initialization, so we'll test differently
        client = IndexTTSClient(space_name="hants/IndexTTS")  # Use valid space first
        
        # Temporarily change space name to invalid one
        original_space_name = client.space_name
        client.space_name = "invalid/nonexistent-space-12345"
        
        # Call get_space_metadata
        metadata = client.get_space_metadata()
        
        # Should return error metadata
        assert isinstance(metadata, dict), "Should return dictionary"
        assert 'error' in metadata, "Should include error field"
        assert metadata['metadata_available'] == False, "Should mark metadata as not available"
        
        # Restore original space name
        client.space_name = original_space_name
        
        print("✅ get_space_metadata with invalid space test passed")
        return metadata
        
    except Exception as e:
        print(f"❌ get_space_metadata with invalid space test failed: {str(e)}")
        raise


def test_get_space_metadata_performance():
    """Test get_space_metadata performance and caching behavior."""
    print("\n🔍 Testing get_space_metadata performance...")
    
    try:
        client = IndexTTSClient()
        
        # Measure performance of multiple calls
        times = []
        for i in range(3):
            start_time = datetime.now()
            metadata = client.get_space_metadata()
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            times.append(duration)
            print(f"   Call {i+1}: {duration:.3f} seconds")
        
        avg_time = sum(times) / len(times)
        print(f"   Average time: {avg_time:.3f} seconds")
        
        # Performance should be reasonable (under 2 seconds per call)
        assert avg_time < 2.0, f"Performance too slow: {avg_time:.3f}s average"
        
        print("✅ get_space_metadata performance test passed")
        return {'average_time': avg_time, 'times': times}
        
    except Exception as e:
        print(f"❌ get_space_metadata performance test failed: {str(e)}")
        raise


def test_get_space_metadata_return_values():
    """Test get_space_metadata return values in detail."""
    print("\n🔍 Testing get_space_metadata return values...")
    
    try:
        client = IndexTTSClient()
        metadata = client.get_space_metadata()
        
        print(f"   Space Name: {metadata.get('space_name', 'N/A')}")
        print(f"   Space URL: {metadata.get('space_url', 'N/A')}")
        print(f"   Metadata Available: {metadata.get('metadata_available', False)}")
        
        if metadata.get('metadata_available', False):
            print(f"   Author: {metadata.get('author', 'N/A')}")
            print(f"   SDK: {metadata.get('sdk', 'N/A')}")
            print(f"   Created: {metadata.get('created_at', 'N/A')}")
            print(f"   Modified: {metadata.get('last_modified', 'N/A')}")
            print(f"   Likes: {metadata.get('likes', 0)}")
            
            if 'runtime' in metadata:
                runtime = metadata['runtime']
                print(f"   Hardware: {runtime.get('hardware_friendly', runtime.get('hardware', 'N/A'))}")
                print(f"   Stage: {runtime.get('stage', 'N/A')}")
        
        # Validate URL format
        space_url = metadata.get('space_url', '')
        expected_url = f"https://huggingface.co/spaces/{metadata.get('space_name', '')}"
        assert space_url == expected_url, f"URL format incorrect: {space_url} vs {expected_url}"
        
        print("✅ get_space_metadata return values test passed")
        return metadata
        
    except Exception as e:
        print(f"❌ get_space_metadata return values test failed: {str(e)}")
        raise


def main():
    """Run all get_space_metadata tests."""
    print("=" * 60)
    print(" IndexTTS get_space_metadata Function Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    results = {}
    all_passed = True
    
    # Test 1: Basic functionality
    try:
        results['basic'] = test_get_space_metadata_basic()
    except Exception as e:
        results['basic'] = {'error': str(e)}
        all_passed = False
    
    # Test 2: Without HfApi
    try:
        results['without_hf_api'] = test_get_space_metadata_without_hf_api()
    except Exception as e:
        results['without_hf_api'] = {'error': str(e)}
        all_passed = False
    
    # Test 3: Invalid space
    try:
        results['invalid_space'] = test_get_space_metadata_with_invalid_space()
    except Exception as e:
        results['invalid_space'] = {'error': str(e)}
        all_passed = False
    
    # Test 4: Performance
    try:
        results['performance'] = test_get_space_metadata_performance()
    except Exception as e:
        results['performance'] = {'error': str(e)}
        all_passed = False
    
    # Test 5: Return values
    try:
        results['return_values'] = test_get_space_metadata_return_values()
    except Exception as e:
        results['return_values'] = {'error': str(e)}
        all_passed = False
    
    # Save results
    try:
        output_file = '/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/get_space_metadata_test_results.json'
        test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_script': __file__,
            'all_passed': all_passed,
            'results': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📄 Test results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Failed to save test results: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print(" Test Summary")
    print("=" * 60)
    
    if all_passed:
        print("🎉 All get_space_metadata tests passed!")
    else:
        print("⚠️  Some get_space_metadata tests failed")
        
    print(f"Test completed at: {datetime.now()}")


if __name__ == "__main__":
    main()
