"""Baseline accuracy test service — runs extraction on gold-standard leases and scores results.

Used by both the API (background thread) and the CLI script.
"""
import json
import os
import re
import time
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

from app.services.claude_service import ClaudeService
from app.core.database import SessionLocal
from app.models.prompt import PromptTemplate
from app.models.few_shot_example import FewShotExample

# ── Field mapping: gold standard field -> system extraction path ──

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

# ── Normalization / comparison helpers ──


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
    """Normalize a lease term to months."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    val = str(val).strip().lower()
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:and|,)?\s*(\d+(?:\.\d+)?)\s*(?:months?|mos?)\s*$', val)
    if m:
        return round(float(m.group(1)) * 12 + float(m.group(2)), 2)
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*$', val)
    if m:
        return round(float(m.group(1)) * 12, 2)
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:months?|mos?)\s*$', val)
    if m:
        return round(float(m.group(1)), 2)
    return normalize_number(val)


def normalize_pro_rata(gold_val, ext_val):
    """Compare pro rata share values, handling decimal vs percentage formats."""
    gn = normalize_number(gold_val)
    en = normalize_number(ext_val)
    if gn is None or en is None:
        return None, None
    if 0 < gn < 1 and en > 1:
        gn = round(gn * 100, 2)
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
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
        return val
    for fmt in ['%m/%d/%Y', '%m/%d/%y', '%B %d, %Y', '%b %d, %Y', '%b. %d, %Y',
                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                '%d %B %Y', '%d %b %Y', '%B %d %Y', '%b %d %Y',
                '%m-%d-%Y', '%m-%d-%y', '%Y/%m/%d']:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
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
    date_fields = {'lease_commencement', 'lease_expiration', 'rent_commencement', 'execution_date'}
    number_fields = {'tenant_sq_feet', 'base_rent_monthly', 'base_rent_annual', 'rent_per_sf_annual',
                     'security_deposit', 'ti_total', 'term_months', 'pro_rata_share'}
    text_fields = {'tenant_legal_name', 'premise_address', 'lease_type', 'permitted_use',
                   'exclusives', 'renewal_options', 'termination', 'expansion'}

    g = normalize_value(gold_val)
    e = normalize_value(extracted_val)

    if g is None and e is None:
        return True, 'both_null'
    if g is None:
        return False, 'gold_null_extracted_present'
    if e is None:
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
        if field_name == 'term_months':
            gn = normalize_term_months(g)
            en = normalize_term_months(e)
        elif field_name == 'pro_rata_share':
            gn, en = normalize_pro_rata(g, e)
        else:
            gn = normalize_number(g)
            en = normalize_number(e)
        if gn is None or en is None:
            return False, f'number_parse_fail: gold={g} ext={e}'
        if gn == 0:
            return en == 0, f'zero_compare: gold={gn} ext={en}'
        ratio = abs(en - gn) / abs(gn)
        if ratio <= 0.05:
            return True, f'number_match (ratio={ratio:.3f})'
        return False, f'number_mismatch: gold={gn} ext={en} (off by {ratio:.1%})'

    if field_name in text_fields:
        g_lower = g.lower()
        e_lower = e.lower()
        none_exact = {'none', 'none.', 'n/a', 'no', 'not applicable', 'not applicable.'}
        g_is_none = g_lower.strip('.') in none_exact
        e_is_none = (e_lower.strip('.') in none_exact or
                     bool(re.match(r'^no\s+(option|renewal|expansion|termination|right|provision|exclusive)', e_lower)))
        if g_is_none and e_is_none:
            return True, 'both_none_semantic'
        if g_lower == e_lower:
            return True, 'exact_text_match'
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
            g_lower = re.sub(r'[,\s]+', ' ', g_lower).strip()
            e_lower = re.sub(r'[,\s]+', ' ', e_lower).strip()
            if g_lower == e_lower:
                return True, 'address_normalized_match'
        if len(g_lower) > 5 and (g_lower in e_lower or e_lower in g_lower):
            return True, 'text_contains'
        g_words = set(re.sub(r'[^a-z0-9\s]', '', g_lower).split())
        e_words = set(re.sub(r'[^a-z0-9\s]', '', e_lower).split())
        stop = {'the', 'a', 'an', 'of', 'and', 'in', 'for', 'to', 'at', 'is', 'be', 'or',
                'llc', 'inc', 'ltd', 'co', 'shall', 'will', 'with', 'its', 'such', 'any'}
        g_words -= stop
        e_words -= stop
        if g_words and e_words:
            overlap = len(g_words & e_words) / max(len(g_words), 1)
            long_text_fields = {'permitted_use', 'exclusives', 'renewal_options', 'termination', 'expansion'}
            threshold = 0.4 if field_name in long_text_fields else 0.6
            if overlap >= threshold:
                return True, f'word_overlap ({overlap:.0%})'
        return False, 'text_mismatch'

    return False, 'unknown_field_type'


# ── Prompt / few-shot loading ──


def load_prompt_and_examples():
    """Load active prompt template and few-shot examples from the DB."""
    db = SessionLocal()
    try:
        pt = db.query(PromptTemplate).filter(PromptTemplate.is_active == True).first()
        prompt_template = None
        prompt_version = None
        if pt:
            prompt_version = pt.version
            prompt_template = {
                'version': pt.version,
                'system_prompt': pt.system_prompt,
                'field_type_guidance': pt.field_type_guidance,
                'extraction_examples': pt.extraction_examples,
                'null_value_guidance': pt.null_value_guidance,
            }

        rows = (
            db.query(FewShotExample)
            .filter(FewShotExample.is_active == True)
            .order_by(FewShotExample.quality_score.desc().nullslast())
            .limit(30)
            .all()
        )
        few_shot_examples = [
            {
                'field_path': r.field_path,
                'source_text': r.source_text,
                'correct_value': r.correct_value,
                'reasoning': r.reasoning,
            }
            for r in rows
        ]
    finally:
        db.close()

    return prompt_template, prompt_version, few_shot_examples


def get_eligible_leases() -> int:
    """Return the count of eligible gold-standard leases (PDF < 4.5 MB)."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
    gold_path = os.path.join(data_dir, 'gold_standard.json')
    if not os.path.exists(gold_path):
        return 0
    with open(gold_path) as f:
        gold_standard = json.load(f)
    lease_dir = os.path.join(data_dir, 'leases', 'Leases')
    count = 0
    for entry in gold_standard:
        path = os.path.join(lease_dir, entry['lease_file'])
        if os.path.exists(path) and os.path.getsize(path) < 4.5 * 1024 * 1024:
            count += 1
    return count


# ── Run state (module-level singleton) ──

_run_lock = threading.Lock()

_current_run: Optional[Dict[str, Any]] = None


def get_run_state() -> Dict[str, Any]:
    """Return the current run progress state."""
    if _current_run is None:
        return {'status': 'idle'}
    return dict(_current_run)


# ── Core run logic ──


def run_baseline(
    num_leases: int = 5,
    multi_pass: bool = False,
    on_progress: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Run baseline accuracy test. Called from API (background thread) or CLI.

    Args:
        num_leases: Number of gold-standard leases to test.
        multi_pass: Use multi-pass refinement extraction.
        on_progress: Callback ``(state_dict)`` called after each lease completes.

    Returns:
        The run summary dict (same shape as accuracy_history entries).
    """
    global _current_run

    acquired = _run_lock.acquire(blocking=False)
    if not acquired:
        raise RuntimeError('A baseline run is already in progress')

    try:
        # Load prompt + examples
        prompt_template, prompt_version, few_shot_examples = load_prompt_and_examples()

        # Load gold standard
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
        with open(os.path.join(data_dir, 'gold_standard.json')) as f:
            gold_standard = json.load(f)

        lease_dir = os.path.join(data_dir, 'leases', 'Leases')

        eligible = []
        for entry in gold_standard:
            path = os.path.join(lease_dir, entry['lease_file'])
            if os.path.exists(path) and os.path.getsize(path) < 4.5 * 1024 * 1024:
                eligible.append(entry)
        test_entries = eligible[:num_leases]

        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = time.time()

        # Initialize run state
        _current_run = {
            'status': 'running',
            'run_id': run_id,
            'current_lease': 0,
            'total_leases': len(test_entries),
            'current_tenant': '',
            'completed_results': [],
            'elapsed_seconds': 0,
            'estimated_remaining': 0,
            'overall_accuracy': 0,
            'error': None,
        }

        service = ClaudeService()
        all_results: List[Dict[str, Any]] = []
        total_cost = 0.0
        total_time = 0.0

        for i, entry in enumerate(test_entries):
            lease_path = os.path.join(lease_dir, entry['lease_file'])
            if not os.path.exists(lease_path):
                continue

            tenant = entry['tenant']
            _current_run['current_lease'] = i + 1
            _current_run['current_tenant'] = tenant
            _current_run['elapsed_seconds'] = int(time.time() - start_time)

            # Estimate remaining time based on average so far
            if all_results:
                avg_per_lease = (time.time() - start_time) / len(all_results)
                _current_run['estimated_remaining'] = int(avg_per_lease * (len(test_entries) - i))

            if on_progress:
                on_progress(dict(_current_run))

            with open(lease_path, 'rb') as f:
                pdf_bytes = f.read()

            # Rate limit between requests
            if i > 0:
                time.sleep(300)

            lease_start = time.time()
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
                elapsed = time.time() - lease_start

                cost = result['metadata']['total_cost']
                total_cost += cost
                total_time += elapsed

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
                        'confidence': result['confidence'].get(sys_field, 0),
                    }

                correct = sum(1 for r in field_results.values() if r['match'])
                total = len(field_results)
                accuracy = correct / total * 100 if total > 0 else 0

                lease_result = {
                    'tenant': tenant,
                    'lease_file': entry['lease_file'],
                    'field_results': field_results,
                    'accuracy': accuracy,
                    'cost': cost,
                    'time': elapsed,
                    'extraction': result['extractions'],
                    'confidence': result['confidence'],
                }
                all_results.append(lease_result)

                # Update run state with completed result
                _current_run['completed_results'].append({
                    'tenant': tenant,
                    'accuracy': accuracy,
                    'fields_correct': correct,
                    'fields_total': total,
                })

            except Exception as e:
                elapsed = time.time() - lease_start
                all_results.append({
                    'tenant': tenant,
                    'lease_file': entry['lease_file'],
                    'error': str(e),
                    'accuracy': 0,
                    'cost': 0,
                    'time': elapsed,
                })
                _current_run['completed_results'].append({
                    'tenant': tenant,
                    'accuracy': 0,
                    'error': str(e),
                })

            # Update rolling overall accuracy
            successful_so_far = [r for r in all_results if 'error' not in r]
            if successful_so_far:
                _current_run['overall_accuracy'] = round(
                    sum(r['accuracy'] for r in successful_so_far) / len(successful_so_far), 1
                )
            _current_run['elapsed_seconds'] = int(time.time() - start_time)

            if on_progress:
                on_progress(dict(_current_run))

        # Build run summary (same as CLI)
        successful = [r for r in all_results if 'error' not in r]
        avg_accuracy = sum(r['accuracy'] for r in successful) / len(successful) if successful else 0

        field_scores: Dict[str, Dict[str, int]] = {}
        for r in successful:
            for field, fr in r['field_results'].items():
                if field not in field_scores:
                    field_scores[field] = {'correct': 0, 'total': 0}
                field_scores[field]['total'] += 1
                if fr['match']:
                    field_scores[field]['correct'] += 1

        version_suffix = f'_v{prompt_version}' if prompt_version else ''
        mode_suffix = '_multipass' if multi_pass else ''
        run_label = os.environ.get('RUN_LABEL', f'baseline{version_suffix}{mode_suffix}')

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

        # Serialize detailed results
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

        # Save to disk
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

        # Mark run complete
        _current_run = {
            'status': 'complete',
            'run_id': run_id,
            'current_lease': len(test_entries),
            'total_leases': len(test_entries),
            'current_tenant': '',
            'completed_results': _current_run['completed_results'],
            'elapsed_seconds': int(time.time() - start_time),
            'estimated_remaining': 0,
            'overall_accuracy': run_summary['average_accuracy'],
            'run_summary': run_summary,
            'error': None,
        }

        if on_progress:
            on_progress(dict(_current_run))

        return run_summary

    except Exception as exc:
        _current_run = {
            'status': 'error',
            'error': str(exc),
            'elapsed_seconds': int(time.time() - start_time) if 'start_time' in dir() else 0,
        }
        raise
    finally:
        _run_lock.release()


def clear_run_state():
    """Reset run state to idle (call after frontend has consumed the complete/error state)."""
    global _current_run
    _current_run = None
