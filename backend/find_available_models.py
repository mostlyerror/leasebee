#!/usr/bin/env python3
"""Find all available Claude models for this API key."""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

print("=" * 80)
print("COMPREHENSIVE MODEL AVAILABILITY TEST")
print("=" * 80)
print()

# Comprehensive list of possible model names
models_to_test = [
    # Claude 3.5 Sonnet variants
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-latest",
    "claude-3.5-sonnet",

    # Claude 3 Opus variants
    "claude-3-opus-20240229",
    "claude-3-opus-latest",
    "claude-3-opus",

    # Claude 3 Sonnet variants
    "claude-3-sonnet-20240229",
    "claude-3-sonnet-latest",
    "claude-3-sonnet",

    # Claude 3 Haiku variants
    "claude-3-haiku-20240307",
    "claude-3-haiku-latest",
    "claude-3-haiku",

    # Claude 2 (older)
    "claude-2.1",
    "claude-2.0",
    "claude-2",

    # Instant (if still available)
    "claude-instant-1.2",
    "claude-instant-1",
]

working_models = []
working_pdf_models = []

print("Testing basic text support...")
print("-" * 80)

for model in models_to_test:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Test"}]
        )
        print(f"✅ {model:<40} WORKS (text)")
        working_models.append(model)
    except Exception as e:
        error_str = str(e)
        if '404' in error_str or 'not_found' in error_str:
            print(f"❌ {model:<40} Not found (404)")
        elif '401' in error_str or 'unauthorized' in error_str:
            print(f"🔒 {model:<40} Unauthorized (401)")
        elif '429' in error_str:
            print(f"⏸️  {model:<40} Rate limited (429)")
        else:
            print(f"❓ {model:<40} Error: {str(e)[:50]}")

print()
print("=" * 80)
print(f"FOUND {len(working_models)} WORKING MODEL(S)")
print("=" * 80)

if working_models:
    print()
    print("Testing PDF support for working models...")
    print("-" * 80)

    # Create a minimal test PDF bytes
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test")
    pdf_bytes = doc.tobytes()
    doc.close()

    import base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    for model in working_models:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=10,
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
                        {"type": "text", "text": "What does this say?"}
                    ]
                }]
            )
            print(f"✅ {model:<40} PDF SUPPORT ✓")
            working_pdf_models.append(model)
        except Exception as e:
            error_str = str(e)
            if 'does not support PDF' in error_str or 'document' in error_str.lower():
                print(f"❌ {model:<40} No PDF support")
            else:
                print(f"❓ {model:<40} Error: {str(e)[:50]}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Models with text support: {len(working_models)}")
for m in working_models:
    print(f"  - {m}")
print()
print(f"Models with PDF support: {len(working_pdf_models)}")
for m in working_pdf_models:
    print(f"  ✅ {m} ← USE THIS ONE!")
print()

if not working_pdf_models:
    print("⚠️  NO MODELS WITH PDF SUPPORT FOUND")
    print()
    print("This could mean:")
    print("  1. Your API key is on a restricted tier")
    print("  2. PDF support requires account upgrade")
    print("  3. There's a regional or workspace restriction")
    print()
    print("Check: https://console.anthropic.com/settings/plans")
else:
    print("✅ READY TO USE!")
    print()
    print(f"Update your .env file:")
    print(f"ANTHROPIC_MODEL={working_pdf_models[0]}")

print()
print("=" * 80)
