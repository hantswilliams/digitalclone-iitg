#!/usr/bin/env python3
"""
Quick test of the LLM client functionality
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def quick_test():
    """Quick test of LLM functionality"""
    print("🧠 Quick LLM Test")
    print("=" * 50)
    
    # Check if HF_API_TOKEN is set
    api_key = os.environ.get('HF_API_TOKEN') or os.environ.get('HF_API_KEY')
    if not api_key:
        print("❌ HF_API_TOKEN not set. Please set it first:")
        print("export HF_API_TOKEN=hf_your_api_key_here")
        return False
    
    print(f"✅ HF_API_TOKEN found (length: {len(api_key)})")
    
    try:
        # Test basic HuggingFace Inference Client
        from huggingface_hub import InferenceClient
        
        print("🔗 Testing HuggingFace Inference Client...")
        
        client = InferenceClient(
            provider="novita",
            api_key=api_key,
        )
        
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello World' if you can hear me."
                }
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        print(f"✅ Success! Response: {response}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 LLM client is working!")
    else:
        print("\n💥 LLM client test failed!")
    
    sys.exit(0 if success else 1)
