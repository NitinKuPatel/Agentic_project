import os
from openai import OpenAI
import sys

# Force UTF-8 for windows console
sys.stdout.reconfigure(encoding='utf-8')

key = "api_key"

def test_key():
    print(f"Testing key: {key[:10]}...")
    
    # 1. Try Standard OpenAI
    print("\n[Attempt 1] Standard OpenAI Endpoint...")
    try:
        client = OpenAI(api_key=key)
        client.models.list()
        print("SUCCESS: Key works with Standard OpenAI API.")
        return
    except Exception as e:
        print(f"FAIL Standard OpenAI: {e}")

    # 2. Try OpenRouter
    print("\n[Attempt 2] OpenRouter Endpoint (https://openrouter.ai/api/v1)...")
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
        models = client.models.list()
        print("SUCCESS: Key works with OpenRouter API.")
        print(f"Retrieved {len(models.data)} models from OpenRouter.")
    except Exception as e:
        print(f"FAIL OpenRouter: {e}")

if __name__ == "__main__":
    test_key()
