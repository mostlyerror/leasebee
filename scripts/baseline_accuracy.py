"""
Baseline accuracy test: extract from lease PDFs and score against gold standard.
Run from project root: source backend/venv/bin/activate && python scripts/baseline_accuracy.py
Usage:
  python scripts/baseline_accuracy.py [num_leases] [--multi-pass]
"""
import sys
import os
import json
import time
import argparse
import functools

# Add backend to path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import scoring/normalization and core logic from the shared service
from app.services.baseline_service import (
    FIELD_MAP,
    normalize_value,
    normalize_number,
    normalize_term_months,
    normalize_pro_rata,
    normalize_date,
    compare_values,
    load_prompt_and_examples,
    run_baseline,
)


def run_baseline_cli(num_leases=5, multi_pass=False):
    """Run baseline accuracy test with CLI output."""
    prompt_template, prompt_version, few_shot_examples = load_prompt_and_examples()

    mode_label = "MULTI-PASS" if multi_pass else "SINGLE-PASS"
    print(f"=" * 100)
    print(f"BASELINE ACCURACY TEST - {num_leases} leases ({mode_label})")
    print(f"=" * 100)
    print(f"  Prompt:             {f'v{prompt_version}' if prompt_version else 'default (no DB template)'}")
    print(f"  Few-shot examples:  {len(few_shot_examples)}")
    print(f"  Extraction mode:    {mode_label}")

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    with open(os.path.join(data_dir, 'gold_standard.json')) as f:
        gold_standard = json.load(f)

    lease_dir = os.path.join(data_dir, 'leases', 'Leases')

    eligible = []
    for entry in gold_standard:
        path = os.path.join(lease_dir, entry['lease_file'])
        if os.path.exists(path) and os.path.getsize(path) < 4.5 * 1024 * 1024:
            eligible.append(entry)
    test_entries = eligible[:num_leases]

    from app.services.claude_service import ClaudeService
    service = ClaudeService()

    all_results = []
    total_cost = 0
    total_time = 0

    for i, entry in enumerate(test_entries):
        lease_path = os.path.join(lease_dir, entry['lease_file'])
        if not os.path.exists(lease_path):
            print(f"\n[{i+1}/{len(test_entries)}] SKIP - File not found: {entry['lease_file']}")
            continue

        tenant = entry['tenant']
        print(f"\n{'─' * 100}")
        print(f"[{i+1}/{len(test_entries)}] {tenant}")
        print(f"  Lease: {entry['lease_file']}")

        with open(lease_path, 'rb') as f:
            pdf_bytes = f.read()

        pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
        print(f"  PDF size: {pdf_size_mb:.1f} MB")

        if i > 0:
            wait = 300
            print(f"  Waiting {wait}s for rate limit...")
            time.sleep(wait)

        start = time.time()
        try:
            if multi_pass:
                result = service.extract_lease_data_with_refinement(
                    pdf_bytes,
                    few_shot_examples=few_shot_examples,
                    prompt_template=prompt_template,
                )
            else:
                result = service.extract_lease_data(
                    pdf_bytes,
                    few_shot_examples=few_shot_examples,
                    prompt_template=prompt_template,
                )
            elapsed = time.time() - start

            cost = result['metadata']['total_cost']
            total_cost += cost
            total_time += elapsed

            print(f"  Time: {elapsed:.1f}s | Cost: ${cost:.4f} | Tokens: {result['metadata']['input_tokens']}in/{result['metadata']['output_tokens']}out")

            gt = entry['ground_truth']
            field_results = {}

            for gs_field, sys_field in FIELD_MAP.items():
                gold_val = gt.get(gs_field)
                ext_val = result['extractions'].get(sys_field)

                if gold_val is None and ext_val is None:
                    continue
                if gold_val is None:
                    continue

                match, detail = compare_values(gold_val, ext_val, gs_field)
                field_results[gs_field] = {
                    'match': match,
                    'detail': detail,
                    'gold': gold_val,
                    'extracted': ext_val,
                    'confidence': result['confidence'].get(sys_field, 0)
                }

            correct = sum(1 for r in field_results.values() if r['match'])
            total = len(field_results)
            accuracy = correct / total * 100 if total > 0 else 0

            print(f"  Accuracy: {correct}/{total} ({accuracy:.0f}%)")
            print()

            for gs_field, r in sorted(field_results.items()):
                status = 'OK' if r['match'] else 'XX'
                conf = r['confidence']
                gold_display = str(r['gold'])[:40]
                ext_display = str(r['extracted'])[:40] if r['extracted'] else 'null'
                print(f"    [{status}] {gs_field:<25} conf={conf:.2f}  gold={gold_display:<42} ext={ext_display}")

            all_results.append({
                'tenant': tenant,
                'lease_file': entry['lease_file'],
                'field_results': field_results,
                'accuracy': accuracy,
                'cost': cost,
                'time': elapsed,
                'extraction': result['extractions'],
                'confidence': result['confidence'],
            })

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ERROR after {elapsed:.1f}s: {e}")
            all_results.append({
                'tenant': tenant,
                'lease_file': entry['lease_file'],
                'error': str(e),
                'accuracy': 0,
                'cost': 0,
                'time': elapsed,
            })

    # Overall summary
    print(f"\n{'=' * 100}")
    print(f"OVERALL RESULTS")
    print(f"{'=' * 100}")

    successful = [r for r in all_results if 'error' not in r]
    if successful:
        avg_accuracy = sum(r['accuracy'] for r in successful) / len(successful)

        field_scores = {}
        for r in successful:
            for field, fr in r['field_results'].items():
                if field not in field_scores:
                    field_scores[field] = {'correct': 0, 'total': 0}
                field_scores[field]['total'] += 1
                if fr['match']:
                    field_scores[field]['correct'] += 1

        print(f"\n  Leases tested:    {len(successful)}")
        print(f"  Average accuracy: {avg_accuracy:.1f}%")
        print(f"  Total cost:       ${total_cost:.4f}")
        print(f"  Total time:       {total_time:.1f}s")
        print(f"  Avg time/lease:   {total_time/len(successful):.1f}s")

        print(f"\n  Per-field accuracy:")
        print(f"  {'Field':<30} {'Correct':>8} {'Total':>6} {'Accuracy':>9}")
        print(f"  {'─' * 55}")
        for field in sorted(field_scores, key=lambda f: field_scores[f]['correct']/max(field_scores[f]['total'],1)):
            fs = field_scores[field]
            acc = fs['correct'] / fs['total'] * 100 if fs['total'] > 0 else 0
            print(f"  {field:<30} {fs['correct']:>8} {fs['total']:>6} {acc:>8.0f}%")

    # Save results using the service's run_baseline for file persistence
    # (The CLI version already prints verbose output above, but we still
    #  want to save run files + history like the service does.)
    from datetime import datetime

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    version_suffix = f'_v{prompt_version}' if prompt_version else ''
    mode_suffix = '_multipass' if multi_pass else ''
    run_label = os.environ.get('RUN_LABEL', f'baseline{version_suffix}{mode_suffix}')

    serializable = []
    for r in all_results:
        sr = {k: v for k, v in r.items() if k != 'field_results'}
        if 'field_results' in r:
            sr['field_results'] = {}
            for f, fr in r['field_results'].items():
                sr['field_results'][f] = {
                    'match': fr['match'],
                    'detail': fr['detail'],
                    'gold': str(fr['gold']) if fr['gold'] is not None else None,
                    'extracted': str(fr['extracted']) if fr['extracted'] is not None else None,
                    'confidence': fr['confidence'],
                }
        serializable.append(sr)

    field_scores = {}
    for r in successful:
        for field, fr in r['field_results'].items():
            if field not in field_scores:
                field_scores[field] = {'correct': 0, 'total': 0}
            field_scores[field]['total'] += 1
            if fr['match']:
                field_scores[field]['correct'] += 1

    run_summary = {
        'run_id': run_id,
        'label': run_label,
        'timestamp': datetime.now().isoformat(),
        'prompt_version': prompt_version,
        'few_shot_count': len(few_shot_examples),
        'multi_pass': multi_pass,
        'leases_tested': len(successful),
        'leases_errored': len(all_results) - len(successful),
        'average_accuracy': avg_accuracy if successful else 0,
        'total_cost': round(total_cost, 4),
        'total_time': round(total_time, 1),
        'field_accuracy': {
            f: round(s['correct'] / s['total'] * 100, 1) if s['total'] > 0 else 0
            for f, s in field_scores.items()
        },
        'per_lease': [
            {'tenant': r['tenant'], 'accuracy': r.get('accuracy', 0), 'error': r.get('error')}
            for r in all_results
        ],
    }

    runs_dir = os.path.join(data_dir, 'runs')
    os.makedirs(runs_dir, exist_ok=True)
    run_path = os.path.join(runs_dir, f'{run_id}_{run_label}.json')
    with open(run_path, 'w') as f:
        json.dump({'summary': run_summary, 'details': serializable}, f, indent=2, default=str)

    with open(os.path.join(data_dir, 'baseline_results.json'), 'w') as f:
        json.dump(serializable, f, indent=2, default=str)

    history_path = os.path.join(data_dir, 'accuracy_history.json')
    history = []
    if os.path.exists(history_path):
        with open(history_path) as f:
            history = json.load(f)
    history.append(run_summary)
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2, default=str)

    print(f"\n  Run saved: data/runs/{run_id}_{run_label}.json")
    print(f"  History:   data/accuracy_history.json ({len(history)} runs)")


if __name__ == '__main__':
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser(description='Baseline accuracy test for lease extraction')
    parser.add_argument('num_leases', nargs='?', type=int, default=5, help='Number of leases to test')
    parser.add_argument('--multi-pass', action='store_true', help='Use multi-pass refinement extraction')
    args = parser.parse_args()

    run_baseline_cli(args.num_leases, multi_pass=args.multi_pass)
