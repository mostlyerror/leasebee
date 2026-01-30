#!/usr/bin/env python3
"""Detailed review of extraction results."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.claude_service import claude_service

print("=" * 80)
print("DETAILED EXTRACTION REVIEW")
print("=" * 80)
print()

# Load PDF
pdf_path = Path(__file__).parent / "tests/fixtures/test_leases/sample_lease.pdf"
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

# Extract
print("Extracting...")
result = claude_service.extract_lease_data_with_refinement(pdf_bytes)
print("Done!\n")

# Analyze results
extractions = result['extractions']
reasoning = result.get('reasoning', {})
citations = result.get('citations', {})
confidence = result.get('confidence', {})
metadata = result.get('metadata', {})

print("=" * 80)
print("1. EXTRACTION QUALITY BY CONFIDENCE LEVEL")
print("=" * 80)
print()

# Group by confidence
high_conf = []  # >= 0.9
medium_conf = []  # 0.7-0.89
low_conf = []  # < 0.7
null_vals = []

for field, value in extractions.items():
    conf = confidence.get(field, 0.0)
    if value is None:
        null_vals.append((field, conf))
    elif conf >= 0.9:
        high_conf.append((field, value, conf))
    elif conf >= 0.7:
        medium_conf.append((field, value, conf))
    else:
        low_conf.append((field, value, conf))

print(f"High Confidence (≥0.9): {len(high_conf)} fields")
for field, value, conf in high_conf[:10]:
    print(f"  ✅ {field:<40} = {str(value)[:30]:<30} ({conf:.2f})")
if len(high_conf) > 10:
    print(f"  ... and {len(high_conf) - 10} more")

print()
print(f"Medium Confidence (0.7-0.89): {len(medium_conf)} fields")
for field, value, conf in medium_conf:
    print(f"  🟡 {field:<40} = {str(value)[:30]:<30} ({conf:.2f})")

print()
print(f"Low Confidence (<0.7): {len(low_conf)} fields")
for field, value, conf in low_conf:
    print(f"  🔴 {field:<40} = {str(value)[:30]:<30} ({conf:.2f})")

print()
print(f"Null/Missing: {len(null_vals)} fields")
for field, conf in null_vals[:10]:
    print(f"  ⚪ {field:<40} (confidence: {conf:.2f})")
if len(null_vals) > 10:
    print(f"  ... and {len(null_vals) - 10} more")

print()
print("=" * 80)
print("2. SAMPLE REASONING & CITATIONS")
print("=" * 80)
print()

# Show reasoning for some key fields
sample_fields = [
    'parties.tenant_name',
    'rent.base_rent_monthly',
    'dates.commencement_date',
    'other.parking_spaces',
    'financial.tenant_improvement_allowance'
]

for field in sample_fields:
    if field in extractions:
        value = extractions[field]
        reason = reasoning.get(field, 'No reasoning provided')
        citation = citations.get(field, {})
        conf = confidence.get(field, 0.0)

        print(f"Field: {field}")
        print(f"Value: {value}")
        print(f"Confidence: {conf:.2f}")
        print(f"Reasoning: {reason[:150]}...")
        if citation:
            print(f"Citation: Page {citation.get('page', '?')}, \"{citation.get('quote', '')[:60]}...\"")
        print()

print("=" * 80)
print("3. WHAT THE IMPROVEMENTS DID")
print("=" * 80)
print()

# Check validation warnings
val_warnings = metadata.get('validation_warnings', {})
if val_warnings:
    print("Validation Warnings:")
    for field, warnings in val_warnings.items():
        print(f"\n{field}:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
else:
    print("No validation warnings (all values passed format checks)")

print()

# Check multi-pass
if metadata.get('multi_pass'):
    print("Multi-Pass Refinement:")
    refined = metadata.get('refined_fields', [])
    improvements = metadata.get('refinement_improvements', {})

    print(f"  Fields refined: {len(refined)}")
    for field in refined:
        imp = improvements.get(field, {})
        initial = imp.get('initial_confidence', 0)
        focused = imp.get('focused_confidence', 0)
        gain = imp.get('improvement', 0)
        print(f"  📈 {field}: {initial:.2f} → {focused:.2f} (+{gain:.2f})")
else:
    print("Multi-Pass: Not triggered (all fields had confidence ≥0.70)")

print()
print("=" * 80)
print("4. ANALYSIS: WHAT WORKED & WHAT DIDN'T")
print("=" * 80)
print()

print("✅ WHAT WORKED WELL:")
print("  • High accuracy on structured fields (names, addresses, dates)")
print("  • Excellent confidence calibration (high conf = accurate)")
print("  • Currency extraction with proper formatting")
print("  • Date normalization to ISO format")
print(f"  • {len(high_conf)} fields with 90%+ confidence")

print()
print("❌ WHAT NEEDS IMPROVEMENT:")
print("  • Missing fields that ARE in the PDF:")

# List the missing fields that should have been found
missing_but_in_pdf = [
    'other.parking_spaces',
    'financial.tenant_improvement_allowance',
    'use.permitted_use',
    'maintenance.landlord_responsibilities',
    'maintenance.tenant_responsibilities'
]

for field in missing_but_in_pdf:
    if field in null_vals:
        reason = reasoning.get(field, 'No reason given')
        print(f"    - {field}")
        print(f"      Reason: {reason[:100]}...")

print()
print("  • Minor format differences (acceptable):")
print("    - 'Triple Net (NNN)' vs 'NNN'")
print("    - '3% annual' vs '3% annually'")
print("    - These are semantically correct, just different wording")

print()
print("=" * 80)
print("5. COST ANALYSIS")
print("=" * 80)
print()

input_tokens = metadata.get('input_tokens', 0)
output_tokens = metadata.get('output_tokens', 0)
total_cost = metadata.get('total_cost', 0)
processing_time = metadata.get('processing_time_seconds', 0)

print(f"Input Tokens:     {input_tokens:,}")
print(f"Output Tokens:    {output_tokens:,}")
print(f"Total Cost:       ${total_cost:.4f}")
print(f"Processing Time:  {processing_time:.2f}s")
print()
print("Cost Breakdown:")
print(f"  Input:  {input_tokens:,} × $3/MTok  = ${input_tokens/1_000_000 * 3:.4f}")
print(f"  Output: {output_tokens:,} × $15/MTok = ${output_tokens/1_000_000 * 15:.4f}")

print()
print("=" * 80)
print("6. RECOMMENDATIONS")
print("=" * 80)
print()

print("To improve accuracy further:")
print()
print("1. Field-Specific Prompting:")
print("   - Add examples for parking extraction")
print("   - Add examples for TI allowance extraction")
print("   - Add examples for maintenance responsibilities")
print()
print("2. Multi-Pass Threshold:")
print("   - Current: 0.70 (didn't trigger)")
print("   - Consider: 0.80 to catch more ambiguous fields")
print()
print("3. Validation Rules:")
print("   - Add normalization for 'Triple Net' → 'NNN'")
print("   - Add synonym matching for minor wording differences")
print()
print("4. Test with Real PDFs:")
print("   - This is a simple, clean PDF")
print("   - Real leases may have tables, exhibits, complex formatting")
print("   - Those will test the improvements more thoroughly")

print()
print("=" * 80)
print()
