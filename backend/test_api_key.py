#!/usr/bin/env python3
"""Test Anthropic API key and available models."""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')

print("="* 80)
print("ANTHROPIC API KEY TEST")
print("=" * 80)
print()
print(f"API Key: {api_key[:20]}..." if api_key else "API Key: NOT SET")
print()

if not api_key or api_key == 'your_anthropic_api_key_here':
    print("❌ API key not set properly")
    exit(1)

client = Anthropic(api_key=api_key)

# Test models
models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

print("Testing models...")
print()

for model in models_to_test:
    try:
        # Try a minimal message
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"✅ {model} - WORKS!")
        print(f"   Response: {response.content[0].text}")
        print()
        break  # Found a working model
    except Exception as e:
        error_str = str(e)
        if '404' in error_str or 'not_found' in error_str:
            print(f"❌ {model} - Model not found (404)")
        elif '401' in error_str or 'unauthorized' in error_str:
            print(f"❌ {model} - Authentication error (401)")
        elif '429' in error_str or 'rate_limit' in error_str:
            print(f"⚠️  {model} - Rate limited (429)")
        else:
            print(f"❌ {model} - Error: {error_str[:100]}")

print()
print("=" * 80)
