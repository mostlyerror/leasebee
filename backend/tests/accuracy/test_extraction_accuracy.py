"""
Accuracy testing framework for extraction validation.

This module tests extraction accuracy against a gold standard dataset,
providing detailed field-by-field comparison and overall metrics.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime

from app.services.claude_service import claude_service


class AccuracyMetrics:
    """Container for accuracy measurement results."""

    def __init__(self):
        self.total_fields = 0
        self.correct = 0
        self.incorrect = 0
        self.missing = 0
        self.field_results = {}
        self.per_field_accuracy = {}
        self.problematic_fields = []

    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy percentage."""
        if self.total_fields == 0:
            return 0.0
        return self.correct / self.total_fields

    @property
    def precision(self) -> float:
        """Precision: correct / (correct + incorrect)."""
        denominator = self.correct + self.incorrect
        if denominator == 0:
            return 0.0
        return self.correct / denominator

    @property
    def recall(self) -> float:
        """Recall: correct / total_fields."""
        return self.overall_accuracy

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting."""
        return {
            'overall_accuracy': round(self.overall_accuracy * 100, 2),
            'precision': round(self.precision * 100, 2),
            'recall': round(self.recall * 100, 2),
            'total_fields': self.total_fields,
            'correct': self.correct,
            'incorrect': self.incorrect,
            'missing': self.missing,
            'field_results': self.field_results,
            'per_field_accuracy': self.per_field_accuracy,
            'problematic_fields': self.problematic_fields
        }


def normalize_value_for_comparison(value: Any) -> Any:
    """
    Normalize a value for comparison.

    Handles type conversions, rounding, and standardization to ensure
    fair comparison between extracted and gold standard values.

    Args:
        value: Value to normalize

    Returns:
        Normalized value
    """
    if value is None:
        return None

    # Convert to string for processing
    value_str = str(value).strip()

    # Handle empty strings as None
    if value_str == '' or value_str.lower() == 'null':
        return None

    # Try to parse as number (for currency, area, percentages)
    try:
        # Handle percentages (might be stored as "0.05" or "5%" or "5")
        if '%' in value_str:
            value_str = value_str.replace('%', '')
            num = float(value_str) / 100
        else:
            # Remove currency symbols and commas
            cleaned = value_str.replace('$', '').replace(',', '')
            num = float(cleaned)

        # Round to 2 decimal places for comparison
        return round(num, 2)
    except (ValueError, TypeError):
        pass

    # Try to parse as date
    try:
        # ISO format
        if len(value_str) == 10 and '-' in value_str:
            datetime.strptime(value_str, '%Y-%m-%d')
            return value_str  # Already normalized
    except ValueError:
        pass

    # For text, lowercase and strip for comparison
    return value_str.lower().strip()


def compare_values(extracted: Any, expected: Any) -> Tuple[bool, str]:
    """
    Compare extracted value with expected gold standard value.

    Args:
        extracted: Extracted value from Claude
        expected: Expected value from gold standard

    Returns:
        Tuple of (is_match, reason)
    """
    # Normalize both values
    norm_extracted = normalize_value_for_comparison(extracted)
    norm_expected = normalize_value_for_comparison(expected)

    # Direct match
    if norm_extracted == norm_expected:
        return True, "Exact match"

    # Both are None/missing
    if norm_extracted is None and norm_expected is None:
        return True, "Both null"

    # One is None
    if norm_extracted is None:
        return False, f"Missing (expected: {expected})"
    if norm_expected is None:
        return False, f"Unexpected value (got: {extracted})"

    # Numeric comparison with tolerance
    try:
        if isinstance(norm_extracted, (int, float)) and isinstance(norm_expected, (int, float)):
            # Allow 0.5% difference for rounding
            tolerance = abs(norm_expected * 0.005)
            if abs(norm_extracted - norm_expected) <= tolerance:
                return True, f"Within tolerance ({tolerance})"
            else:
                diff = abs(norm_extracted - norm_expected)
                return False, f"Numeric mismatch (diff: {diff}, expected: {expected}, got: {extracted})"
    except (TypeError, ValueError):
        pass

    # String comparison
    if isinstance(norm_extracted, str) and isinstance(norm_expected, str):
        # Check if one contains the other (for text fields that might have variations)
        if norm_expected in norm_extracted or norm_extracted in norm_expected:
            return True, "Partial text match"

    return False, f"Mismatch (expected: {expected}, got: {extracted})"


def calculate_accuracy(
    extracted: Dict[str, Any],
    gold_standard: Dict[str, Any],
    confidence: Dict[str, float] = None
) -> AccuracyMetrics:
    """
    Calculate extraction accuracy metrics.

    Args:
        extracted: Extracted field values from Claude
        gold_standard: Gold standard field values
        confidence: Optional confidence scores for each field

    Returns:
        AccuracyMetrics object with detailed results
    """
    metrics = AccuracyMetrics()
    confidence = confidence or {}

    for field_path, expected_value in gold_standard.items():
        metrics.total_fields += 1
        actual_value = extracted.get(field_path)

        is_match, reason = compare_values(actual_value, expected_value)

        if is_match:
            metrics.correct += 1
            metrics.field_results[field_path] = {
                'status': 'correct',
                'expected': expected_value,
                'actual': actual_value,
                'confidence': confidence.get(field_path),
                'reason': reason
            }
        elif actual_value is None:
            metrics.missing += 1
            metrics.field_results[field_path] = {
                'status': 'missing',
                'expected': expected_value,
                'actual': None,
                'confidence': confidence.get(field_path, 0.0),
                'reason': reason
            }
            metrics.problematic_fields.append({
                'field': field_path,
                'issue': 'missing',
                'expected': expected_value
            })
        else:
            metrics.incorrect += 1
            metrics.field_results[field_path] = {
                'status': 'incorrect',
                'expected': expected_value,
                'actual': actual_value,
                'confidence': confidence.get(field_path),
                'reason': reason
            }
            metrics.problematic_fields.append({
                'field': field_path,
                'issue': 'incorrect',
                'expected': expected_value,
                'actual': actual_value,
                'confidence': confidence.get(field_path)
            })

    # Calculate per-field accuracy (for aggregating across multiple leases)
    field_categories = {}
    for field_path, result in metrics.field_results.items():
        category = field_path.split('.')[0]  # e.g., "dates" from "dates.commencement_date"
        if category not in field_categories:
            field_categories[category] = {'correct': 0, 'total': 0}
        field_categories[category]['total'] += 1
        if result['status'] == 'correct':
            field_categories[category]['correct'] += 1

    metrics.per_field_accuracy = {
        category: round((stats['correct'] / stats['total']) * 100, 2)
        for category, stats in field_categories.items()
    }

    return metrics


class TestExtractionAccuracy:
    """Test suite for extraction accuracy measurement."""

    @pytest.fixture(scope='class')
    def gold_standard_data(self):
        """Load gold standard test data."""
        test_dir = Path(__file__).parent.parent / 'fixtures' / 'test_leases'
        gold_standard_path = test_dir / 'gold_standard.json'

        with open(gold_standard_path, 'r') as f:
            data = json.load(f)

        return data

    @pytest.fixture(scope='class')
    def test_lease_pdfs(self):
        """
        Get test lease PDFs.

        NOTE: This fixture needs actual PDF files in test_leases directory.
        For now, it will skip if PDFs are not available.
        """
        test_dir = Path(__file__).parent.parent / 'fixtures' / 'test_leases'
        pdf_files = list(test_dir.glob('*.pdf'))

        if not pdf_files:
            pytest.skip("No test PDF files found. Place sample PDFs in tests/fixtures/test_leases/")

        return {pdf.stem: pdf for pdf in pdf_files}

    def test_baseline_accuracy(self, gold_standard_data, test_lease_pdfs):
        """
        Test baseline extraction accuracy.

        This test measures the current accuracy of the extraction system
        against the gold standard dataset.
        """
        all_metrics = []

        for lease_data in gold_standard_data['leases']:
            lease_id = lease_data['lease_id']
            filename = lease_data['filename']
            gold_standard = lease_data['gold_standard']

            # Skip if PDF not available
            pdf_name = filename.replace('.pdf', '')
            if pdf_name not in test_lease_pdfs:
                print(f"Skipping {lease_id}: PDF not found ({filename})")
                continue

            # Read PDF
            pdf_path = test_lease_pdfs[pdf_name]
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            # Extract using Claude
            print(f"\nExtracting {lease_id}...")
            result = claude_service.extract_lease_data(pdf_bytes)

            # Calculate accuracy
            metrics = calculate_accuracy(
                result['extractions'],
                gold_standard,
                result.get('confidence')
            )

            # Store results
            all_metrics.append({
                'lease_id': lease_id,
                'filename': filename,
                'description': lease_data['description'],
                'metrics': metrics.to_dict(),
                'metadata': result['metadata']
            })

            # Print summary for this lease
            print(f"  Accuracy: {metrics.overall_accuracy * 100:.2f}%")
            print(f"  Correct: {metrics.correct}/{metrics.total_fields}")
            print(f"  Incorrect: {metrics.incorrect}")
            print(f"  Missing: {metrics.missing}")

        # Save detailed results
        results_dir = Path(__file__).parent
        results_file = results_dir / 'baseline_results.json'

        with open(results_file, 'w') as f:
            json.dump({
                'test_date': datetime.utcnow().isoformat(),
                'test_type': 'baseline',
                'results': all_metrics
            }, f, indent=2)

        print(f"\nDetailed results saved to: {results_file}")

        # Calculate aggregate metrics
        if all_metrics:
            total_correct = sum(m['metrics']['correct'] for m in all_metrics)
            total_fields = sum(m['metrics']['total_fields'] for m in all_metrics)
            overall_accuracy = (total_correct / total_fields * 100) if total_fields > 0 else 0

            print(f"\n{'='*60}")
            print(f"AGGREGATE BASELINE METRICS")
            print(f"{'='*60}")
            print(f"Overall Accuracy: {overall_accuracy:.2f}%")
            print(f"Total Correct: {total_correct}/{total_fields}")
            print(f"Leases Tested: {len(all_metrics)}")

            # Assert minimum accuracy threshold
            # This will fail initially but shows baseline
            assert overall_accuracy >= 60.0, \
                f"Baseline accuracy {overall_accuracy:.2f}% is below minimum threshold of 60%"

    def test_field_type_accuracy(self, gold_standard_data, test_lease_pdfs):
        """
        Test accuracy by field type (dates, currency, areas, etc.).

        This helps identify which field types need the most improvement.
        """
        # This will be implemented after we gather baseline data
        pytest.skip("Run after baseline test to analyze field type accuracy")

    def test_confidence_correlation(self, gold_standard_data, test_lease_pdfs):
        """
        Test correlation between confidence scores and accuracy.

        High confidence should correlate with high accuracy.
        """
        # This will be implemented after we gather baseline data
        pytest.skip("Run after baseline test to analyze confidence correlation")


if __name__ == '__main__':
    """Run tests directly for manual testing."""
    pytest.main([__file__, '-v', '--tb=short'])
