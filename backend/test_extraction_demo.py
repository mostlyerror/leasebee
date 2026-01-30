#!/usr/bin/env python3
"""
Quick demo of the extraction accuracy improvements.

This script extracts data from the sample PDF and shows:
- Extracted values
- Validation warnings
- Multi-pass refinement (if any)
- Comparison with gold standard
"""
import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.claude_service import claude_service
from app.services.validation_service import validation_service
from app.schemas.field_schema import get_field_by_path


def main():
    """Run extraction demo."""
    print("=" * 80)
    print("LEASEBEE EXTRACTION ACCURACY DEMO")
    print("=" * 80)
    print()

    # Load sample PDF
    pdf_path = Path(__file__).parent / "tests/fixtures/test_leases/sample_lease.pdf"

    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at {pdf_path}")
        print("Please ensure sample_lease.pdf exists in tests/fixtures/test_leases/")
        return 1

    print(f"📄 Loading PDF: {pdf_path.name}")
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    print(f"   File size: {len(pdf_bytes):,} bytes")
    print()

    # Extract with multi-pass refinement
    print("🤖 Extracting with Claude (multi-pass enabled)...")
    print()

    try:
        result = claude_service.extract_lease_data_with_refinement(
            pdf_bytes,
            confidence_threshold=0.70
        )
    except Exception as e:
        print(f"❌ Extraction failed: {str(e)}")
        print()
        print("This likely means ANTHROPIC_API_KEY is not set.")
        print("To run this demo, set your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return 1

    # Display results
    extractions = result['extractions']
    citations = result.get('citations', {})
    confidence = result.get('confidence', {})
    metadata = result.get('metadata', {})

    print("✅ Extraction Complete!")
    print()
    print("-" * 80)
    print("EXTRACTION METADATA")
    print("-" * 80)
    print(f"Model: {metadata.get('model_version', 'N/A')}")
    print(f"Prompt Version: {metadata.get('prompt_version', 'N/A')}")
    print(f"Input Tokens: {metadata.get('input_tokens', 0):,}")
    print(f"Output Tokens: {metadata.get('output_tokens', 0):,}")
    print(f"Total Cost: ${metadata.get('total_cost', 0):.4f}")
    print(f"Processing Time: {metadata.get('processing_time_seconds', 0):.2f}s")
    print(f"Multi-Pass Used: {metadata.get('multi_pass', False)}")

    if metadata.get('multi_pass'):
        refined = metadata.get('refined_fields', [])
        print(f"Fields Refined: {len(refined)}")
        if refined:
            print("  - " + "\n  - ".join(refined[:5]))
            if len(refined) > 5:
                print(f"  ... and {len(refined) - 5} more")
    print()

    # Show sample extractions
    print("-" * 80)
    print("SAMPLE EXTRACTED VALUES")
    print("-" * 80)

    key_fields = [
        'parties.tenant_name',
        'parties.landlord_name',
        'property.address',
        'property.rentable_area',
        'dates.commencement_date',
        'dates.expiration_date',
        'rent.base_rent_monthly',
        'financial.security_deposit',
        'other.parking_spaces'
    ]

    for field_path in key_fields:
        value = extractions.get(field_path)
        conf = confidence.get(field_path, 0.0)

        # Get field definition
        field_def = get_field_by_path(field_path)
        field_label = field_def['label'] if field_def else field_path

        # Format value
        if value is None:
            value_str = "null"
            color = "⚪"
        else:
            value_str = str(value)
            if conf >= 0.9:
                color = "🟢"
            elif conf >= 0.7:
                color = "🟡"
            else:
                color = "🔴"

        print(f"{color} {field_label:.<50} {value_str} ({conf:.2f})")

    print()

    # Validation warnings
    validation_warnings = metadata.get('validation_warnings', {})
    if validation_warnings:
        print("-" * 80)
        print("VALIDATION WARNINGS")
        print("-" * 80)
        for field_path, warnings in validation_warnings.items():
            field_def = get_field_by_path(field_path)
            field_label = field_def['label'] if field_def else field_path
            print(f"\n{field_label} ({field_path}):")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        print()

    # Load gold standard for comparison
    gold_standard_path = Path(__file__).parent / "tests/fixtures/test_leases/gold_standard.json"

    if gold_standard_path.exists():
        print("-" * 80)
        print("ACCURACY COMPARISON")
        print("-" * 80)

        with open(gold_standard_path, 'r') as f:
            gold_data = json.load(f)

        # Find the gold standard for sample_lease
        gold_standard = None
        for lease in gold_data.get('leases', []):
            if lease.get('filename') == 'sample_lease.pdf':
                gold_standard = lease.get('gold_standard', {})
                break

        if gold_standard:
            correct = 0
            incorrect = 0
            missing = 0
            total = len(gold_standard)

            errors = []

            for field_path, expected in gold_standard.items():
                actual = extractions.get(field_path)

                # Normalize for comparison
                expected_str = str(expected).lower().strip() if expected is not None else "null"
                actual_str = str(actual).lower().strip() if actual is not None else "null"

                # Simple comparison (could use the normalize function from test)
                if expected_str == actual_str:
                    correct += 1
                elif actual is None:
                    missing += 1
                    errors.append(f"  ❌ {field_path}: MISSING (expected: {expected})")
                else:
                    # Check if it's close enough (for numeric values)
                    try:
                        exp_num = float(str(expected).replace(',', ''))
                        act_num = float(str(actual).replace(',', ''))
                        if abs(exp_num - act_num) < 0.01:
                            correct += 1
                            continue
                    except (ValueError, TypeError):
                        pass

                    incorrect += 1
                    errors.append(f"  ❌ {field_path}: got '{actual}', expected '{expected}'")

            accuracy = (correct / total * 100) if total > 0 else 0

            print(f"Total Fields:     {total}")
            print(f"✅ Correct:       {correct}")
            print(f"❌ Incorrect:     {incorrect}")
            print(f"⚪ Missing:       {missing}")
            print(f"📊 Accuracy:      {accuracy:.2f}%")
            print()

            if errors and len(errors) <= 10:
                print("Errors:")
                for error in errors:
                    print(error)
                print()
            elif errors:
                print(f"Showing first 10 of {len(errors)} errors:")
                for error in errors[:10]:
                    print(error)
                print(f"  ... and {len(errors) - 10} more errors")
                print()

    # Multi-pass improvements
    improvements = metadata.get('refinement_improvements', {})
    if improvements:
        print("-" * 80)
        print("MULTI-PASS IMPROVEMENTS")
        print("-" * 80)
        for field_path, improvement in improvements.items():
            initial = improvement['initial_confidence']
            focused = improvement['focused_confidence']
            gain = improvement['improvement']
            field_def = get_field_by_path(field_path)
            field_label = field_def['label'] if field_def else field_path
            print(f"📈 {field_label}")
            print(f"   {initial:.2f} → {focused:.2f} (+{gain:.2f})")
        print()

    # Summary
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("✨ Features demonstrated:")
    print("  ✅ Enhanced prompt engineering with field-type guidance")
    print("  ✅ Validation and normalization")
    print("  ✅ Multi-pass refinement for low-confidence fields")
    print("  ✅ Confidence scoring")
    print("  ✅ Accuracy measurement against gold standard")
    print()
    print("📖 For more details, see:")
    print("  - /docs/accuracy_improvements.md")
    print("  - /docs/QUICK_START_ACCURACY_TESTING.md")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
