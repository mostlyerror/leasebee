"""
Accuracy dashboard: view progress over time.
Run: python scripts/accuracy_dashboard.py
"""
import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HISTORY_PATH = os.path.join(DATA_DIR, 'accuracy_history.json')


def show_dashboard():
    if not os.path.exists(HISTORY_PATH):
        print("No runs yet. Run scripts/baseline_accuracy.py first.")
        return

    with open(HISTORY_PATH) as f:
        history = json.load(f)

    if not history:
        print("No runs recorded.")
        return

    # Header
    print()
    print("=" * 90)
    print("  LEASEBEE EXTRACTION ACCURACY DASHBOARD")
    print("=" * 90)

    # Run history table
    print()
    print(f"  {'#':<4} {'Date':<20} {'Label':<20} {'Leases':>7} {'Accuracy':>10} {'Cost':>8} {'Time':>8}")
    print(f"  {'─' * 80}")

    for i, run in enumerate(history):
        ts = run['timestamp'][:16].replace('T', ' ')
        label = run['label'][:18]
        n = run['leases_tested']
        acc = run['average_accuracy']
        cost = run['total_cost']
        time_s = run['total_time']

        # Trend arrow
        if i > 0:
            prev = history[i-1]['average_accuracy']
            if acc > prev + 1:
                trend = ' ^'
            elif acc < prev - 1:
                trend = ' v'
            else:
                trend = ' ='
        else:
            trend = '  '

        print(f"  {i+1:<4} {ts:<20} {label:<20} {n:>7} {acc:>8.1f}%{trend} ${cost:>7.2f} {time_s:>6.0f}s")

    # Latest run detail
    latest = history[-1]
    print()
    print(f"  LATEST RUN: {latest['label']} ({latest['timestamp'][:16].replace('T', ' ')})")
    print(f"  {'─' * 60}")

    # Per-field accuracy
    if latest.get('field_accuracy'):
        print()
        print(f"  {'Field':<30} {'Accuracy':>10}  Bar")
        print(f"  {'─' * 55}")
        for field in sorted(latest['field_accuracy'], key=lambda f: latest['field_accuracy'][f]):
            acc = latest['field_accuracy'][field]
            bar_len = int(acc / 5)
            bar = '#' * bar_len + '.' * (20 - bar_len)
            print(f"  {field:<30} {acc:>8.0f}%  [{bar}]")

    # Per-lease results
    if latest.get('per_lease'):
        print()
        print(f"  Per-lease:")
        for lease in latest['per_lease']:
            if lease.get('error'):
                print(f"    XX  {lease['tenant']:<40} ERROR")
            else:
                acc = lease['accuracy']
                print(f"    {acc:>3.0f}% {lease['tenant']}")

    # Progress summary
    if len(history) >= 2:
        first = history[0]
        print()
        print(f"  PROGRESS: {first['average_accuracy']:.1f}% -> {latest['average_accuracy']:.1f}% "
              f"({latest['average_accuracy'] - first['average_accuracy']:+.1f}%) "
              f"over {len(history)} runs")

    print()
    print(f"  History file: data/accuracy_history.json")
    print(f"  Run details:  data/runs/")
    print()


def show_run_detail(run_id):
    """Show detailed results for a specific run."""
    runs_dir = os.path.join(DATA_DIR, 'runs')
    # Find the run file
    matches = [f for f in os.listdir(runs_dir) if f.startswith(run_id)]
    if not matches:
        print(f"No run found matching '{run_id}'. Available runs:")
        for f in sorted(os.listdir(runs_dir)):
            print(f"  {f}")
        return

    with open(os.path.join(runs_dir, matches[0])) as f:
        data = json.load(f)

    summary = data['summary']
    details = data['details']

    print(f"\nRun: {summary['label']} ({summary['timestamp'][:16]})")
    print(f"Accuracy: {summary['average_accuracy']:.1f}% across {summary['leases_tested']} leases")
    print()

    for lease in details:
        if lease.get('error'):
            print(f"  {lease['tenant']}: ERROR - {lease['error'][:80]}")
            continue

        print(f"  {lease['tenant']}: {lease['accuracy']:.0f}%")
        if lease.get('field_results'):
            for field, fr in sorted(lease['field_results'].items()):
                status = 'OK' if fr['match'] else 'XX'
                gold = str(fr['gold'])[:35] if fr['gold'] else 'null'
                ext = str(fr['extracted'])[:35] if fr['extracted'] else 'null'
                print(f"    [{status}] {field:<25} gold={gold:<37} ext={ext}")
        print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        show_run_detail(sys.argv[1])
    else:
        show_dashboard()
