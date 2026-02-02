#!/usr/bin/env python3
"""Test with CURRENT 2026 model names from official docs."""
import os
from dotenv import load_dotenv
from anthropic import Anthropic
import base64

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

print("=" * 80)
print("TESTING CURRENT 2026 CLAUDE MODELS (Official Names)")
print("=" * 80)
print()

# Current models from official docs
current_models = [
    # Latest 4.5 series
    ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5 (recommended)"),
    ("claude-haiku-4-5-20251001", "Claude Haiku 4.5 (fastest)"),
    ("claude-opus-4-5-20251101", "Claude Opus 4.5 (most capable)"),

    # Legacy but still available
    ("claude-opus-4-1-20250805", "Claude Opus 4.1"),
    ("claude-sonnet-4-20250514", "Claude Sonnet 4"),
    ("claude-3-7-sonnet-20250219", "Claude Sonnet 3.7"),
    ("claude-3-haiku-20240307", "Claude Haiku 3 (legacy)"),
]

# Create minimal test PDF
import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Test PDF")
pdf_bytes = doc.tobytes()
doc.close()
pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

print("Testing models with PDF support...")
print("-" * 80)

working_models = []

for model_id, description in current_models:
    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {"type": "text", "text": "What does this PDF say?"}
                ]
            }]
        )
        print(f"✅ {model_id:<35} {description}")
        print(f"   Response: {response.content[0].text[:50]}...")
        working_models.append((model_id, description))
        print()
    except Exception as e:
        error_str = str(e)
        if '404' in error_str or 'not_found' in error_str:
            print(f"❌ {model_id:<35} Not found (may need account upgrade)")
        elif 'does not support PDF' in error_str or 'document' in error_str:
            print(f"⚠️  {model_id:<35} No PDF support")
        elif '401' in error_str or 'unauthorized' in error_str:
            print(f"🔒 {model_id:<35} Unauthorized (check API key)")
        else:
            print(f"❓ {model_id:<35} Error: {str(e)[:60]}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

if working_models:
    print(f"✅ Found {len(working_models)} model(s) with PDF support!")
    print()
    for model_id, description in working_models:
        print(f"  • {model_id} - {description}")
    print()
    print("UPDATE YOUR .ENV FILE:")
    print(f"ANTHROPIC_MODEL={working_models[0][0]}")
else:
    print("❌ No models with PDF support found")
    print()
    print("Your API key may be:")
    print("  1. On a free tier (upgrade at console.anthropic.com)")
    print("  2. Restricted by organization admin")
    print("  3. Missing payment method")

print()
print("=" * 80)
