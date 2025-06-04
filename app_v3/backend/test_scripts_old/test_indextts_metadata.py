#!/usr/bin/env python3
"""
Test script for IndexTTS client and get_space_metadata function.

This script tests the IndexTTS client initialization, configuration validation,
health checks, and specifically focuses on the get_space_metadata functionality.
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


def print_separator(title: str = None):
    """Print a visual separator with optional title."""
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    else:
        print(f"{'─'*60}")


def pretty_print_dict(data: Dict, indent: int = 0):
    """Pretty print a dictionary with proper indentation."""
    spacing = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{spacing}{key}:")
            pretty_print_dict(value, indent + 1)
        elif isinstance(value, list):
            print(f"{spacing}{key}: {value}")
        else:
            print(f"{spacing}{key}: {value}")


def test_client_initialization():
    """Test IndexTTS client initialization."""
    print_separator("Testing IndexTTS Client Initialization")
    
    try:
        print("🔧 Initializing IndexTTS client...")
        client = IndexTTSClient()
        print("✅ Client initialized successfully")
        print(f"   Space Name: {client.space_name}")
        print(f"   Has HF Token: {bool(client.hf_token)}")
        print(f"   Has HF API: {bool(client.hf_api)}")
        return client
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("   Please install required packages: pip install gradio_client huggingface_hub")
        return None
    except IndexTTSAPIError as e:
        print(f"❌ IndexTTS API error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_configuration_validation(client: IndexTTSClient):
    """Test client configuration validation."""
    print_separator("Testing Configuration Validation")
    
    try:
        print("🔍 Validating configuration...")
        config_result = client.validate_configuration()
        
        print(f"✅ Configuration validation completed")
        pretty_print_dict(config_result)
        
        if not config_result['valid']:
            print("\n⚠️  Configuration issues found:")
            for issue in config_result['issues']:
                print(f"   - {issue}")
        else:
            print("\n✅ Configuration is valid")
            
        return config_result
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_get_space_metadata(client: IndexTTSClient):
    """Test the get_space_metadata function specifically."""
    print_separator("Testing get_space_metadata Function")
    
    try:
        print("📊 Fetching space metadata...")
        metadata = client.get_space_metadata()
        
        print("✅ Metadata fetched successfully")
        print_separator()
        pretty_print_dict(metadata)
        
        # Validate metadata structure
        print_separator("Validating Metadata Structure")
        required_fields = ['space_name', 'space_url', 'metadata_available']
        
        for field in required_fields:
            if field in metadata:
                print(f"✅ Required field '{field}': present")
            else:
                print(f"❌ Required field '{field}': missing")
        
        # Check if metadata was successfully fetched
        if metadata.get('metadata_available', False):
            print("\n📋 Available metadata fields:")
            optional_fields = [
                'space_id', 'author', 'created_at', 'last_modified',
                'likes', 'downloads', 'sdk', 'runtime'
            ]
            
            for field in optional_fields:
                if field in metadata:
                    print(f"   ✅ {field}: {metadata[field]}")
                else:
                    print(f"   ❌ {field}: missing")
                    
            # Test runtime information
            if 'runtime' in metadata:
                print("\n🔧 Runtime information:")
                runtime = metadata['runtime']
                if isinstance(runtime, dict):
                    pretty_print_dict(runtime, indent=1)
                else:
                    print(f"   Unexpected runtime format: {runtime}")
        else:
            print("\n⚠️  Metadata not available")
            if 'error' in metadata:
                print(f"   Error: {metadata['error']}")
        
        return metadata
        
    except Exception as e:
        print(f"❌ get_space_metadata test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_health_check_with_metadata(client: IndexTTSClient):
    """Test health check which includes metadata."""
    print_separator("Testing Health Check (includes metadata)")
    
    try:
        print("🏥 Performing health check...")
        health_result = client.health_check()
        
        print("✅ Health check completed")
        print_separator()
        pretty_print_dict(health_result)
        
        # Check if health check includes metadata
        if 'huggingface_metadata' in health_result:
            print("\n📊 Health check includes Hugging Face metadata:")
            metadata = health_result['huggingface_metadata']
            if metadata.get('metadata_available', False):
                print("   ✅ Metadata successfully included in health check")
            else:
                print("   ⚠️  Metadata included but not available")
                if 'error' in metadata:
                    print(f"   Error: {metadata['error']}")
        else:
            print("\n❌ Health check does not include Hugging Face metadata")
        
        return health_result
        
    except Exception as e:
        print(f"❌ Health check test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_different_space_names():
    """Test metadata fetching with different space names."""
    print_separator("Testing Different Space Names")
    
    # Test with different space configurations
    test_spaces = [
        "hants/IndexTTS",  # Default space
        "microsoft/speecht5_tts",  # Different TTS space
        "invalid/nonexistent-space"  # Invalid space for error testing
    ]
    
    for space_name in test_spaces:
        print(f"\n🔍 Testing space: {space_name}")
        try:
            # Create client with specific space name
            client = IndexTTSClient(space_name=space_name)
            metadata = client.get_space_metadata()
            
            if metadata.get('metadata_available', False):
                print(f"   ✅ Successfully fetched metadata for {space_name}")
                print(f"   Author: {metadata.get('author', 'Unknown')}")
                print(f"   SDK: {metadata.get('sdk', 'Unknown')}")
                print(f"   Likes: {metadata.get('likes', 0)}")
            else:
                print(f"   ⚠️  Could not fetch metadata for {space_name}")
                if 'error' in metadata:
                    print(f"   Error: {metadata['error']}")
                    
        except Exception as e:
            print(f"   ❌ Error testing {space_name}: {str(e)}")


def test_metadata_performance():
    """Test metadata fetching performance."""
    print_separator("Testing Metadata Performance")
    
    try:
        client = IndexTTSClient()
        
        print("⏱️  Testing metadata fetching performance...")
        start_time = datetime.now()
        
        # Fetch metadata multiple times
        for i in range(3):
            print(f"   Attempt {i+1}/3...")
            metadata = client.get_space_metadata()
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Performance test completed")
        print(f"   Total time for 3 requests: {duration:.2f} seconds")
        print(f"   Average time per request: {duration/3:.2f} seconds")
        
        return duration
        
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return None


def save_test_results(results: Dict[str, Any]):
    """Save test results to a JSON file."""
    print_separator("Saving Test Results")
    
    try:
        timestamp = datetime.now().isoformat()
        results['test_timestamp'] = timestamp
        results['test_script'] = __file__
        
        output_file = '/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/indextts_metadata_test_results.json'
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Test results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Failed to save test results: {str(e)}")


def main():
    """Main test function."""
    print_separator("IndexTTS Client and Metadata Testing")
    print(f"Test started at: {datetime.now()}")
    print(f"Python version: {sys.version}")
    
    # Store all test results
    test_results = {}
    
    # Test 1: Client Initialization
    client = test_client_initialization()
    if not client:
        print("\n❌ Cannot continue testing without a valid client")
        return
    
    # Test 2: Configuration Validation
    config_result = test_configuration_validation(client)
    test_results['configuration'] = config_result
    
    # Test 3: get_space_metadata Function
    metadata_result = test_get_space_metadata(client)
    test_results['metadata'] = metadata_result
    
    # Test 4: Health Check with Metadata
    health_result = test_health_check_with_metadata(client)
    test_results['health_check'] = health_result
    
    # Test 5: Different Space Names
    test_different_space_names()
    
    # Test 6: Performance Testing
    performance_result = test_metadata_performance()
    test_results['performance'] = {'average_time': performance_result/3 if performance_result else None}
    
    # Save results
    save_test_results(test_results)
    
    print_separator("Test Summary")
    
    # Provide summary
    if metadata_result and metadata_result.get('metadata_available', False):
        print("✅ get_space_metadata function is working correctly")
    else:
        print("⚠️  get_space_metadata function has issues")
    
    if health_result and 'huggingface_metadata' in health_result:
        print("✅ Health check includes metadata")
    else:
        print("⚠️  Health check does not include metadata")
    
    if config_result and config_result.get('valid', False):
        print("✅ Client configuration is valid")
    else:
        print("⚠️  Client configuration has issues")
    
    print(f"\n🎉 Testing completed at: {datetime.now()}")


if __name__ == "__main__":
    main()
