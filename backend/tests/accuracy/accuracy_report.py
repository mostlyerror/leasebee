"""
Accuracy report generation for extraction testing.

This module generates comprehensive reports comparing extraction accuracy
over time and identifying areas for improvement.
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class AccuracyReport:
    """Generate comprehensive accuracy reports."""

    def __init__(self, results_file: Path):
        """
        Initialize report generator.

        Args:
            results_file: Path to JSON results file
        """
        with open(results_file, 'r') as f:
            self.data = json.load(f)

        self.test_date = self.data.get('test_date', 'Unknown')
        self.test_type = self.data.get('test_type', 'Unknown')
        self.results = self.data.get('results', [])

    def generate_summary(self) -> str:
        """Generate executive summary of results."""
        if not self.results:
            return "No results to report."

        total_correct = sum(r['metrics']['correct'] for r in self.results)
        total_fields = sum(r['metrics']['total_fields'] for r in self.results)
        total_incorrect = sum(r['metrics']['incorrect'] for r in self.results)
        total_missing = sum(r['metrics']['missing'] for r in self.results)

        overall_accuracy = (total_correct / total_fields * 100) if total_fields > 0 else 0

        report = []
        report.append("=" * 80)
        report.append("EXTRACTION ACCURACY REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {self.test_date}")
        report.append(f"Test Type: {self.test_type}")
        report.append(f"Leases Tested: {len(self.results)}")
        report.append("")
        report.append("OVERALL METRICS")
        report.append("-" * 80)
        report.append(f"Overall Accuracy:  {overall_accuracy:6.2f}%")
        report.append(f"Total Fields:      {total_fields:6d}")
        report.append(f"Correct:           {total_correct:6d}")
        report.append(f"Incorrect:         {total_incorrect:6d}")
        report.append(f"Missing:           {total_missing:6d}")
        report.append("")

        return "\n".join(report)

    def generate_per_lease_summary(self) -> str:
        """Generate per-lease accuracy breakdown."""
        if not self.results:
            return ""

        report = []
        report.append("PER-LEASE ACCURACY")
        report.append("-" * 80)
        report.append(f"{'Lease ID':<25} {'Description':<35} {'Accuracy':>10}")
        report.append("-" * 80)

        for result in self.results:
            lease_id = result['lease_id']
            description = result['description'][:35]
            accuracy = result['metrics']['overall_accuracy']

            report.append(f"{lease_id:<25} {description:<35} {accuracy:>9.2f}%")

        report.append("")
        return "\n".join(report)

    def generate_field_category_analysis(self) -> str:
        """Analyze accuracy by field category."""
        # Aggregate by category across all leases
        category_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

        for result in self.results:
            field_results = result['metrics']['field_results']

            for field_path, field_result in field_results.items():
                category = field_path.split('.')[0]
                category_stats[category]['total'] += 1
                if field_result['status'] == 'correct':
                    category_stats[category]['correct'] += 1

        # Calculate accuracy per category
        category_accuracy = {
            category: (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            for category, stats in category_stats.items()
        }

        # Sort by accuracy (lowest first to highlight problem areas)
        sorted_categories = sorted(category_accuracy.items(), key=lambda x: x[1])

        report = []
        report.append("ACCURACY BY FIELD CATEGORY")
        report.append("-" * 80)
        report.append(f"{'Category':<30} {'Correct':>10} {'Total':>10} {'Accuracy':>12}")
        report.append("-" * 80)

        for category, accuracy in sorted_categories:
            stats = category_stats[category]
            report.append(
                f"{category:<30} {stats['correct']:>10d} {stats['total']:>10d} {accuracy:>11.2f}%"
            )

        report.append("")
        return "\n".join(report)

    def generate_problematic_fields(self, top_n: int = 10) -> str:
        """Identify most problematic fields across all leases."""
        field_errors = defaultdict(lambda: {'count': 0, 'examples': []})

        for result in self.results:
            problematic = result['metrics']['problematic_fields']

            for problem in problematic:
                field = problem['field']
                field_errors[field]['count'] += 1
                field_errors[field]['examples'].append({
                    'lease_id': result['lease_id'],
                    'issue': problem['issue'],
                    'expected': problem.get('expected'),
                    'actual': problem.get('actual')
                })

        # Sort by error count
        sorted_fields = sorted(
            field_errors.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:top_n]

        report = []
        report.append(f"TOP {top_n} MOST PROBLEMATIC FIELDS")
        report.append("-" * 80)

        for i, (field, data) in enumerate(sorted_fields, 1):
            report.append(f"{i}. {field}")
            report.append(f"   Errors: {data['count']}")
            report.append(f"   Examples:")

            for example in data['examples'][:3]:  # Show first 3 examples
                report.append(f"     - {example['lease_id']}: {example['issue']}")
                if example.get('expected'):
                    report.append(f"       Expected: {example['expected']}")
                if example.get('actual'):
                    report.append(f"       Got: {example['actual']}")

            report.append("")

        return "\n".join(report)

    def generate_cost_analysis(self) -> str:
        """Analyze extraction costs."""
        if not self.results:
            return ""

        total_cost = sum(r['metadata']['total_cost'] for r in self.results)
        total_tokens_in = sum(r['metadata']['input_tokens'] for r in self.results)
        total_tokens_out = sum(r['metadata']['output_tokens'] for r in self.results)
        total_fields = sum(r['metrics']['total_fields'] for r in self.results)
        total_correct = sum(r['metrics']['correct'] for r in self.results)

        avg_cost_per_lease = total_cost / len(self.results) if self.results else 0
        avg_cost_per_field = total_cost / total_fields if total_fields > 0 else 0
        cost_per_accurate_field = total_cost / total_correct if total_correct > 0 else 0

        report = []
        report.append("COST ANALYSIS")
        report.append("-" * 80)
        report.append(f"Total Cost:                ${total_cost:.4f}")
        report.append(f"Average Cost per Lease:    ${avg_cost_per_lease:.4f}")
        report.append(f"Average Cost per Field:    ${avg_cost_per_field:.6f}")
        report.append(f"Cost per Accurate Field:   ${cost_per_accurate_field:.6f}")
        report.append(f"Total Input Tokens:        {total_tokens_in:,}")
        report.append(f"Total Output Tokens:       {total_tokens_out:,}")
        report.append("")

        return "\n".join(report)

    def generate_confidence_analysis(self) -> str:
        """Analyze confidence score distribution and correlation with accuracy."""
        confidence_buckets = {
            'high': {'correct': 0, 'incorrect': 0, 'total': 0},      # >= 0.9
            'medium': {'correct': 0, 'incorrect': 0, 'total': 0},    # 0.7-0.89
            'low': {'correct': 0, 'incorrect': 0, 'total': 0},       # < 0.7
        }

        for result in self.results:
            field_results = result['metrics']['field_results']

            for field_path, field_result in field_results.items():
                confidence = field_result.get('confidence')
                if confidence is None:
                    continue

                # Determine bucket
                if confidence >= 0.9:
                    bucket = 'high'
                elif confidence >= 0.7:
                    bucket = 'medium'
                else:
                    bucket = 'low'

                confidence_buckets[bucket]['total'] += 1
                if field_result['status'] == 'correct':
                    confidence_buckets[bucket]['correct'] += 1
                else:
                    confidence_buckets[bucket]['incorrect'] += 1

        report = []
        report.append("CONFIDENCE SCORE ANALYSIS")
        report.append("-" * 80)
        report.append(f"{'Bucket':<15} {'Correct':>10} {'Incorrect':>10} {'Total':>10} {'Accuracy':>12}")
        report.append("-" * 80)

        for bucket_name in ['high', 'medium', 'low']:
            bucket = confidence_buckets[bucket_name]
            accuracy = (bucket['correct'] / bucket['total'] * 100) if bucket['total'] > 0 else 0

            report.append(
                f"{bucket_name.capitalize():<15} {bucket['correct']:>10d} "
                f"{bucket['incorrect']:>10d} {bucket['total']:>10d} {accuracy:>11.2f}%"
            )

        report.append("")
        report.append("Note: High confidence should correlate with high accuracy.")
        report.append("If low-confidence fields have high accuracy, confidence calibration may be off.")
        report.append("")

        return "\n".join(report)

    def generate_full_report(self) -> str:
        """Generate complete report with all sections."""
        sections = [
            self.generate_summary(),
            self.generate_per_lease_summary(),
            self.generate_field_category_analysis(),
            self.generate_problematic_fields(),
            self.generate_confidence_analysis(),
            self.generate_cost_analysis(),
        ]

        return "\n".join(sections)

    def save_report(self, output_path: Path):
        """Save report to file."""
        report = self.generate_full_report()

        with open(output_path, 'w') as f:
            f.write(report)

        print(f"Report saved to: {output_path}")


def compare_reports(baseline_file: Path, improved_file: Path) -> str:
    """
    Compare baseline and improved results.

    Args:
        baseline_file: Path to baseline results JSON
        improved_file: Path to improved results JSON

    Returns:
        Comparison report string
    """
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)

    with open(improved_file, 'r') as f:
        improved_data = json.load(f)

    baseline_results = baseline_data.get('results', [])
    improved_results = improved_data.get('results', [])

    # Calculate metrics
    def calc_metrics(results):
        total_correct = sum(r['metrics']['correct'] for r in results)
        total_fields = sum(r['metrics']['total_fields'] for r in results)
        total_cost = sum(r['metadata']['total_cost'] for r in results)
        return {
            'accuracy': (total_correct / total_fields * 100) if total_fields > 0 else 0,
            'correct': total_correct,
            'total': total_fields,
            'cost': total_cost
        }

    baseline_metrics = calc_metrics(baseline_results)
    improved_metrics = calc_metrics(improved_results)

    # Generate comparison
    accuracy_gain = improved_metrics['accuracy'] - baseline_metrics['accuracy']
    cost_increase = improved_metrics['cost'] - baseline_metrics['cost']
    cost_increase_pct = (cost_increase / baseline_metrics['cost'] * 100) if baseline_metrics['cost'] > 0 else 0

    report = []
    report.append("=" * 80)
    report.append("BASELINE vs IMPROVED COMPARISON")
    report.append("=" * 80)
    report.append(f"{'Metric':<30} {'Baseline':>15} {'Improved':>15} {'Change':>15}")
    report.append("-" * 80)
    report.append(
        f"{'Overall Accuracy':<30} {baseline_metrics['accuracy']:>14.2f}% "
        f"{improved_metrics['accuracy']:>14.2f}% {accuracy_gain:>+14.2f}%"
    )
    report.append(
        f"{'Correct Fields':<30} {baseline_metrics['correct']:>15d} "
        f"{improved_metrics['correct']:>15d} {improved_metrics['correct'] - baseline_metrics['correct']:>+15d}"
    )
    report.append(
        f"{'Total Cost':<30} ${baseline_metrics['cost']:>14.4f} "
        f"${improved_metrics['cost']:>14.4f} {cost_increase_pct:>+14.2f}%"
    )
    report.append("")
    report.append(f"Accuracy Improvement: {accuracy_gain:.2f} percentage points")
    report.append(f"Cost Increase: ${cost_increase:.4f} ({cost_increase_pct:+.2f}%)")
    report.append("")

    # ROI calculation
    if cost_increase > 0:
        accuracy_per_dollar = accuracy_gain / cost_increase
        report.append(f"ROI: {accuracy_per_dollar:.2f} accuracy points per dollar spent")
    else:
        report.append("ROI: Improved accuracy with no cost increase!")

    report.append("")

    return "\n".join(report)


if __name__ == '__main__':
    """Generate report from command line."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python accuracy_report.py <results_file.json> [output_report.txt]")
        print("\nOr for comparison:")
        print("Usage: python accuracy_report.py --compare <baseline.json> <improved.json>")
        sys.exit(1)

    if sys.argv[1] == '--compare':
        if len(sys.argv) < 4:
            print("Error: --compare requires two result files")
            sys.exit(1)

        baseline_file = Path(sys.argv[2])
        improved_file = Path(sys.argv[3])

        comparison = compare_reports(baseline_file, improved_file)
        print(comparison)

        if len(sys.argv) > 4:
            output_file = Path(sys.argv[4])
            with open(output_file, 'w') as f:
                f.write(comparison)
            print(f"\nComparison saved to: {output_file}")

    else:
        results_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else results_file.with_suffix('.txt')

        report_gen = AccuracyReport(results_file)
        report_gen.save_report(output_file)
        print(report_gen.generate_full_report())
