import requests
import json

def test_koboldcpp_connection():
    """Test connection to KoboldCpp"""
    endpoint = "http://localhost:5001/v1"
    
    print("Testing KoboldCpp connection...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{endpoint.replace('/v1', '')}/api/v1/model")
        if response.status_code == 200:
            print("✓ KoboldCpp server is running")
            model_info = response.json()
            print(f"  Loaded model: {model_info.get('result', 'Unknown')}")
        else:
            print("✗ KoboldCpp server responded but with error")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to KoboldCpp: {e}")
        print("  Make sure KoboldCpp is running on http://localhost:5001")
        return False
    
    # Test 2: Test chat completion
    try:
        test_message = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, I am working!' in exactly 5 words."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{endpoint}/chat/completions",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_message)
        )
        
        if response.status_code == 200:
            print("✓ Chat completion endpoint is working")
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                print(f"  Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"✗ Chat completion failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Chat completion test failed: {e}")
        return False

if __name__ == "__main__":
    if test_koboldcpp_connection():
        print("\n✓ All tests passed! You can now use the storytelling agent.")
    else:
        print("\n✗ Tests failed. Please check your KoboldCpp setup.")
