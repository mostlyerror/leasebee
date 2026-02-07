#!/usr/bin/env python3
"""Test Claude API connection."""
import os
from anthropic import Anthropic

# Load from .env
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')

print(f"Testing Claude API...")
print(f"API Key: {api_key[:20]}..." if api_key else "API Key: NOT SET")
print(f"Model: {model}")
print()

try:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": "Say hello in 5 words"
        }]
    )
    print("✅ SUCCESS!")
    print(f"Response: {response.content[0].text}")
except Exception as e:
    print(f"❌ ERROR: {e}")
