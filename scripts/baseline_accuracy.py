"""
Baseline accuracy test: extract from lease PDFs and score against gold standard.
Run from project root: source backend/venv/bin/activate && python scripts/baseline_accuracy.py
"""
import sys
import os
import json
import re
import time
from datetime import datetime

# Add backend to path so we can import the extraction service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.claude_service import ClaudeService

# Field mapping: gold standard field -> system extraction path
FIELD_MAP = {
    'tenant_legal_name': 'parties.tenant_name',
    'premise_address': 'property.address',
    'tenant_sq_feet': 'property.rentable_area',
    'lease_commencement': 'dates.commencement_date',
    'lease_expiration': 'dates.expiration_date',
    'rent_commencement': 'dates.rent_commencement_date',
    'term_months': 'dates.lease_term_months',
    'execution_date': 'basic_info.execution_date',
    'base_rent_monthly': 'rent.base_rent_monthly',
    'base_rent_annual': 'rent.base_rent_annual',
    'rent_per_sf_annual': 'rent.rent_per_sf_annual',
    'security_deposit': 'financial.security_deposit',
    'ti_total': 'financial.tenant_improvement_allowance',
    'lease_type': 'operating_expenses.structure_type',
    'pro_rata_share': 'operating_expenses.tenant_share_percentage',
    'permitted_use': 'use.permitted_use',
    'exclusives': 'use.exclusive_use',
    'renewal_options': 'rights.renewal_options',
    'termination': 'rights.termination_rights',
    'expansion': 'rights.expansion_rights',
}


def normalize_value(val, field_type='text'):
    """Normalize a value for comparison."""
    if val is None:
        return None
    val = str(val).strip()
    if val.lower() in ('n/a', 'null', '', 'not specified', 'not applicable',
                        '#div/0!', '#n/a', '#ref!', '#value!', 'tbd'):
        return None
    return val


def normalize_number(val):
    """Normalize a numeric value."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    val = str(val).strip()
    val = re.sub(r'[,$\s]', '', val)
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None


def normalize_term_months(val):
    """Normalize a lease term to months. Handles '5 years', '60 months', '10 years and 6 months', etc."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    val = str(val).strip().lower()
    # Compound: "10 years and 6 months" / "10 years, 6 months" / "10 yrs 6 mos"
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:and|,)?\s*(\d+(?:\.\d+)?)\s*(?:months?|mos?)\s*$', val)
    if m:
        return round(float(m.group(1)) * 12 + float(m.group(2)), 2)
    # "5 years" / "5 year" / "5 yrs" / "5yr"
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*$', val)
    if m:
        return round(float(m.group(1)) * 12, 2)
    # "60 months" / "60 mos" / "60mo"
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:months?|mos?)\s*$', val)
    if m:
        return round(float(m.group(1)), 2)
    # Fall back to plain number
    return normalize_number(val)


def normalize_pro_rata(gold_val, ext_val):
    """Compare pro rata share values, handling decimal (0.30) vs percentage (30%) formats."""
    gn = normalize_number(gold_val)
    en = normalize_number(ext_val)
    if gn is None or en is None:
        return None, None
    # If gold is 0-1 and extracted is > 1, gold is likely a fraction
    if 0 < gn < 1 and en > 1:
        gn = round(gn * 100, 2)
    # If extracted is 0-1 and gold is > 1, extracted is likely a fraction
    elif 0 < en < 1 and gn > 1:
        en = round(en * 100, 2)
    return gn, en


def normalize_date(val):
    """Normalize a date to YYYY-MM-DD."""
    if val is None:
        return None
    val = str(val).strip()
    if not val or val.lower() in ('none', 'null', 'n/a', 'tbd', 'not specified'):
        return None
    # Already YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
        return val
    # Try common formats
    for fmt in ['%m/%d/%Y', '%m/%d/%y', '%B %d, %Y', '%b %d, %Y', '%b. %d, %Y',
                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                '%d %B %Y', '%d %b %Y', '%B %d %Y', '%b %d %Y',
                '%m-%d-%Y', '%m-%d-%y', '%Y/%m/%d']:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    # Handle ordinal dates like "June 21st, 2025" or "March 3rd, 2025"
    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', val)
    if cleaned != val:
        for fmt in ['%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y']:
            try:
                return datetime.strptime(cleaned, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return val


def compare_values(gold_val, extracted_val, field_name):
    """Compare a gold standard value with an extracted value. Returns (match, detail)."""
    # Determine field type from name
    date_fields = {'lease_commencement', 'lease_expiration', 'rent_commencement', 'execution_date'}
    number_fields = {'tenant_sq_feet', 'base_rent_monthly', 'base_rent_annual', 'rent_per_sf_annual',
                     'security_deposit', 'ti_total', 'term_months', 'pro_rata_share'}
    text_fields = {'tenant_legal_name', 'premise_address', 'lease_type', 'permitted_use',
                   'exclusives', 'renewal_options', 'termination', 'expansion'}

    g = normalize_value(gold_val)
    e = normalize_value(extracted_val)

    # Both null = match
    if g is None and e is None:
        return True, 'both_null'
    # One null = miss
    if g is None:
        return False, 'gold_null_extracted_present'
    if e is None:
        # For number fields, gold=0 and extracted=null should match (system treats "no deposit" as null)
        if field_name in number_fields:
            gn = normalize_number(g)
            if gn is not None and gn == 0:
                return True, 'zero_vs_null'
        return False, 'extracted_null'

    if field_name in date_fields:
        gd = normalize_date(g)
        ed = normalize_date(e)
        if gd and ed and gd == ed:
            return True, 'exact_date_match'
        return False, f'date_mismatch: gold={gd} ext={ed}'

    if field_name in number_fields:
        # Special handling for term_months (may be "5 years" vs 60)
        if field_name == 'term_months':
            gn = normalize_term_months(g)
            en = normalize_term_months(e)
        # Special handling for pro_rata_share (decimal vs percentage)
        elif field_name == 'pro_rata_share':
            gn, en = normalize_pro_rata(g, e)
        else:
            gn = normalize_number(g)
            en = normalize_number(e)
        if gn is None or en is None:
            return False, f'number_parse_fail: gold={g} ext={e}'
        # Allow 5% tolerance for currency/area
        if gn == 0:
            return en == 0, f'zero_compare: gold={gn} ext={en}'
        ratio = abs(en - gn) / abs(gn)
        if ratio <= 0.05:
            return True, f'number_match (ratio={ratio:.3f})'
        return False, f'number_mismatch: gold={gn} ext={en} (off by {ratio:.1%})'

    if field_name in text_fields:
        # For text fields, check if key content overlaps
        g_lower = g.lower()
        e_lower = e.lower()
        # Check if both sides express "none" / "no [field]" semantics
        none_exact = {'none', 'none.', 'n/a', 'no', 'not applicable', 'not applicable.'}
        g_is_none = g_lower.strip('.') in none_exact
        # For extracted, also match "No options to renew", "No expansion rights", etc.
        e_is_none = (e_lower.strip('.') in none_exact or
                     bool(re.match(r'^no\s+(option|renewal|expansion|termination|right|provision|exclusive)', e_lower)))
        # Both say "none/no" = match
        if g_is_none and e_is_none:
            return True, 'both_none_semantic'
        # Exact match
        if g_lower == e_lower:
            return True, 'exact_text_match'
        # For short fields (like lease_type), check containment
        if field_name == 'lease_type':
            nnn_variants = {'nnn', 'triple net', 'net net net'}
            g_is_nnn = any(v in g_lower for v in nnn_variants)
            e_is_nnn = any(v in e_lower for v in nnn_variants)
            if g_is_nnn and e_is_nnn:
                return True, 'nnn_match'
            nn_variants = {'nn', 'double net', 'net net'}
            g_is_nn = any(v in g_lower for v in nn_variants) and not g_is_nnn
            e_is_nn = any(v in e_lower for v in nn_variants) and not e_is_nnn
            if g_is_nn and e_is_nn:
                return True, 'nn_match'
            gross_variants = {'gross', 'full service'}
            g_is_gross = any(v in g_lower for v in gross_variants)
            e_is_gross = any(v in e_lower for v in gross_variants)
            if g_is_gross and e_is_gross:
                return True, 'gross_match'
            modified_variants = {'modified gross', 'modified net'}
            g_is_mod = any(v in g_lower for v in modified_variants)
            e_is_mod = any(v in e_lower for v in modified_variants)
            if g_is_mod and e_is_mod:
                return True, 'modified_match'
        # Address normalization before overlap check
        if field_name == 'premise_address':
            addr_abbrevs = {
                'pkwy': 'parkway', 'blvd': 'boulevard', 'st': 'street', 'ave': 'avenue',
                'dr': 'drive', 'rd': 'road', 'ln': 'lane', 'ct': 'court', 'pl': 'place',
                'hwy': 'highway', 'ste': 'suite', 'tx': 'texas', 'ca': 'california',
                'fl': 'florida', 'ny': 'new york',
            }
            for abbr, full in addr_abbrevs.items():
                g_lower = re.sub(r'\b' + abbr + r'\b', full, g_lower)
                e_lower = re.sub(r'\b' + abbr + r'\b', full, e_lower)
            # Remove commas and extra spaces for comparison
            g_lower = re.sub(r'[,\s]+', ' ', g_lower).strip()
            e_lower = re.sub(r'[,\s]+', ' ', e_lower).strip()
            if g_lower == e_lower:
                return True, 'address_normalized_match'
        # Containment check for longer text
        if len(g_lower) > 5 and (g_lower in e_lower or e_lower in g_lower):
            return True, 'text_contains'
        # Word overlap - use lower threshold for long descriptive fields
        g_words = set(re.sub(r'[^a-z0-9\s]', '', g_lower).split())
        e_words = set(re.sub(r'[^a-z0-9\s]', '', e_lower).split())
        stop = {'the', 'a', 'an', 'of', 'and', 'in', 'for', 'to', 'at', 'is', 'be', 'or',
                'llc', 'inc', 'ltd', 'co', 'shall', 'will', 'with', 'its', 'such', 'any'}
        g_words -= stop
        e_words -= stop
        if g_words and e_words:
            overlap = len(g_words & e_words) / max(len(g_words), 1)
            # Long descriptive fields (permitted_use, renewal, expansion) get lower threshold
            long_text_fields = {'permitted_use', 'exclusives', 'renewal_options', 'termination', 'expansion'}
            threshold = 0.4 if field_name in long_text_fields else 0.6
            if overlap >= threshold:
                return True, f'word_overlap ({overlap:.0%})'
        return False, f'text_mismatch'

    return False, 'unknown_field_type'


def run_baseline(num_leases=5):
    """Run baseline accuracy test."""
    # Load gold standard
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    with open(os.path.join(data_dir, 'gold_standard.json')) as f:
        gold_standard = json.load(f)

    lease_dir = os.path.join(data_dir, 'leases', 'Leases')

    # Filter to PDFs under 4.5MB (API token limit) and pick N
    eligible = []
    for entry in gold_standard:
        path = os.path.join(lease_dir, entry['lease_file'])
        if os.path.exists(path) and os.path.getsize(path) < 4.5 * 1024 * 1024:
            eligible.append(entry)
    test_entries = eligible[:num_leases]

    print(f"=" * 100)
    print(f"BASELINE ACCURACY TEST - {len(test_entries)} leases")
    print(f"=" * 100)

    # Initialize services
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

        # Read PDF
        with open(lease_path, 'rb') as f:
            pdf_bytes = f.read()

        pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
        print(f"  PDF size: {pdf_size_mb:.1f} MB")

        # Rate limit: wait between requests (30k tokens/min limit)
        # A 2MB PDF uses ~130k tokens, so need ~5 min between requests
        if i > 0:
            wait = 300  # 5 min between requests
            print(f"  Waiting {wait}s for rate limit...")
            time.sleep(wait)

        # Extract
        start = time.time()
        try:
            result = service.extract_lease_data(pdf_bytes)
            elapsed = time.time() - start

            cost = result['metadata']['total_cost']
            total_cost += cost
            total_time += elapsed

            print(f"  Time: {elapsed:.1f}s | Cost: ${cost:.4f} | Tokens: {result['metadata']['input_tokens']}in/{result['metadata']['output_tokens']}out")

            # Score against gold standard
            gt = entry['ground_truth']
            field_results = {}

            for gs_field, sys_field in FIELD_MAP.items():
                gold_val = gt.get(gs_field)
                ext_val = result['extractions'].get(sys_field)

                if gold_val is None and ext_val is None:
                    continue  # skip fields absent in both

                if gold_val is None:
                    continue  # skip fields not in gold standard

                match, detail = compare_values(gold_val, ext_val, gs_field)
                field_results[gs_field] = {
                    'match': match,
                    'detail': detail,
                    'gold': gold_val,
                    'extracted': ext_val,
                    'confidence': result['confidence'].get(sys_field, 0)
                }

            # Print per-field results
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

        # Per-field accuracy across all leases
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

    # Build run summary
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_label = os.environ.get('RUN_LABEL', 'baseline')

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

    # Save detailed results for this run
    runs_dir = os.path.join(data_dir, 'runs')
    os.makedirs(runs_dir, exist_ok=True)
    run_path = os.path.join(runs_dir, f'{run_id}_{run_label}.json')
    with open(run_path, 'w') as f:
        json.dump({'summary': run_summary, 'details': serializable}, f, indent=2, default=str)

    # Also save as latest
    with open(os.path.join(data_dir, 'baseline_results.json'), 'w') as f:
        json.dump(serializable, f, indent=2, default=str)

    # Append to history log
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
    # Ensure output is unbuffered
    import functools
    print = functools.partial(print, flush=True)
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    run_baseline(num)
