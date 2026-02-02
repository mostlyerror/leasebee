#!/usr/bin/env python3
"""
Verify environment setup for extraction accuracy testing.

This script checks that all dependencies and configurations are correct.
"""
import sys
from pathlib import Path

print("=" * 80)
print("LEASEBEE ENVIRONMENT SETUP VERIFICATION")
print("=" * 80)
print()

# Track issues
issues = []
warnings = []

# 1. Check Python version
print("✓ Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"  ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    issues.append("Python version too old")

# 2. Check required packages
print("\n✓ Checking required packages...")
required_packages = [
    ('anthropic', 'Anthropic API client'),
    ('fastapi', 'FastAPI framework'),
    ('sqlalchemy', 'SQLAlchemy ORM'),
    ('pydantic', 'Pydantic validation'),
    ('pytest', 'Pytest testing'),
]

for package, description in required_packages:
    try:
        __import__(package)
        print(f"  ✅ {package:<15} - {description}")
    except ImportError:
        print(f"  ❌ {package:<15} - {description} (NOT INSTALLED)")
        issues.append(f"Missing package: {package}")

# 3. Check environment variables
print("\n✓ Checking environment variables...")
import os
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"  ✅ .env file found at {env_path}")
else:
    print(f"  ⚠️  .env file not found at {env_path}")
    warnings.append(".env file missing")

# Check API key
api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key and api_key != 'your_anthropic_api_key_here' and api_key.startswith('sk-ant-'):
    print(f"  ✅ ANTHROPIC_API_KEY is set (starts with {api_key[:15]}...)")
elif api_key and api_key != 'your_anthropic_api_key_here':
    print(f"  ⚠️  ANTHROPIC_API_KEY is set but doesn't look valid")
    print(f"     (should start with 'sk-ant-', got: {api_key[:20]}...)")
    warnings.append("API key format looks incorrect")
else:
    print(f"  ❌ ANTHROPIC_API_KEY not set or using placeholder")
    print(f"     Set it in .env or: export ANTHROPIC_API_KEY='sk-ant-xxxxx'")
    issues.append("ANTHROPIC_API_KEY not configured")

# 4. Check test files
print("\n✓ Checking test files...")
test_files = [
    ('tests/fixtures/test_leases/sample_lease.pdf', 'Sample PDF'),
    ('tests/fixtures/test_leases/gold_standard.json', 'Gold standard data'),
    ('tests/accuracy/test_extraction_accuracy.py', 'Test framework'),
    ('tests/accuracy/accuracy_report.py', 'Report generator'),
]

for file_path, description in test_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"  ✅ {description:<25} ({size:,} bytes)")
    else:
        print(f"  ❌ {description:<25} (NOT FOUND)")
        issues.append(f"Missing file: {file_path}")

# 5. Check core services
print("\n✓ Checking core services...")
service_files = [
    ('app/services/claude_service.py', 'Claude service'),
    ('app/services/validation_service.py', 'Validation service'),
    ('app/api/extractions.py', 'Extraction API'),
]

for file_path, description in service_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        print(f"  ✅ {description}")
    else:
        print(f"  ❌ {description} (NOT FOUND)")
        issues.append(f"Missing service: {file_path}")

# 6. Test API connectivity (if key is set)
print("\n✓ Testing Anthropic API connectivity...")
if api_key and api_key != 'your_anthropic_api_key_here' and api_key.startswith('sk-ant-'):
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # Simple test - just check we can create client
        print(f"  ✅ API client created successfully")
        print(f"     (Skipping actual API call to save costs)")

    except Exception as e:
        print(f"  ⚠️  Could not create API client: {str(e)}")
        warnings.append(f"API client error: {str(e)}")
else:
    print(f"  ⏭️  Skipped (API key not configured)")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if not issues and not warnings:
    print("\n✅ ALL CHECKS PASSED! Your environment is ready.")
    print("\nNext steps:")
    print("  1. Make sure your ANTHROPIC_API_KEY is set")
    print("  2. Run: python3 test_extraction_demo.py")
    print("  3. Or run full tests: pytest tests/accuracy/ -v -s")

elif not issues:
    print(f"\n⚠️  Setup complete with {len(warnings)} warning(s):")
    for warning in warnings:
        print(f"  • {warning}")
    print("\nYou can proceed, but address warnings for best results.")

else:
    print(f"\n❌ Found {len(issues)} issue(s) that need to be fixed:")
    for issue in issues:
        print(f"  • {issue}")

    if warnings:
        print(f"\nAlso found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  • {warning}")

    print("\nFix these issues before running tests.")
    sys.exit(1)

print("\n" + "=" * 80)
print()
