#!/usr/bin/env python3
"""
Test script for updated LLM service - Script generation with Llama-3.1
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_updated_llm():
    """Test the updated LLM client functionality"""
    print("🧠 Testing Updated LLM Service - Script Generation with Llama-3.1")
    print("=" * 70)
    
    try:
        # Import after setting up path
        from app.services.llm import create_llama_client, LlamaConfig
        
        # Test 1: Check environment variables
        print("\n📋 Test 1: Environment Variable Check")
        api_key = os.environ.get('HF_API_KEY')
        if api_key:
            print(f"✅ PASS - HF_API_KEY found (length: {len(api_key)})")
        else:
            print("❌ FAIL - HF_API_KEY not found in environment")
            print("Please set your HuggingFace API key:")
            print("export HF_API_KEY=hf_your_api_key_here")
            return False
        
        # Test 2: Create client
        print("\n📋 Test 2: Client Initialization")
        config = LlamaConfig()
        print(f"Model: {config.model_name}")
        print(f"Provider: {config.provider}")
        print(f"Temperature: {config.temperature}")
        
        client = create_llama_client(config)
        print("✅ PASS - Llama client created successfully")
        
        # Test 3: Health check
        print("\n📋 Test 3: Health Check")
        health_result = client.health_check()
        print(f"Status: {health_result['status']}")
        if health_result['status'] == 'healthy':
            print("✅ PASS - Health check successful")
            if 'test_response' in health_result:
                print(f"Test response: {health_result['test_response']}")
        else:
            print(f"❌ FAIL - Health check failed: {health_result.get('error', 'Unknown error')}")
            return False
        
        # Test 4: Simple script generation
        print("\n📋 Test 4: Simple Script Generation")
        result = client.generate_script(
            prompt="Create a brief introduction about artificial intelligence",
            topic="Artificial Intelligence",
            target_audience="students",
            duration_minutes=1,
            style="educational"
        )
        
        if result['success']:
            print("✅ PASS - Script generation successful")
            print(f"Script length: {len(result['script'])} characters")
            print(f"Word count: {result['metadata']['word_count']} words")
            print(f"Generation time: {result['metadata']['generation_time']} seconds")
            print(f"Estimated duration: {result['analysis']['estimated_duration']} minutes")
            print("\nGenerated script preview:")
            print("-" * 50)
            print(result['script'][:200] + "..." if len(result['script']) > 200 else result['script'])
            print("-" * 50)
        else:
            print(f"❌ FAIL - Script generation failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("\n✅ All tests passed! The updated LLM service is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ FAIL - Import error: {e}")
        print("Make sure you're running this from the backend directory")
        return False
    except Exception as e:
        print(f"❌ FAIL - Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Updated LLM Service Test...")
    
    success = test_updated_llm()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure HF_API_KEY environment variable is set")
        print("2. Install huggingface_hub: pip install huggingface_hub")
        print("3. Check your internet connection")
        print("4. Verify your HuggingFace API key is valid")
        sys.exit(1)
