#!/usr/bin/env python3
"""
Run qualitative analysis on v2 and v3 results.
Covers criterion vi: Qualitative and error analysis including hallucination.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# ── Vulnerability heuristics ──────────────────────────────────────────────
VULN_PATTERNS = {
    'buffer_overflow': [r'\bstrcpy\s*\(', r'\bstrcat\s*\(', r'\bsprintf\s*\(', r'\bgets\s*\('],
    'integer_overflow': [r'\bint\b.*\*.*\bint\b', r'malloc\s*\(\s*\w+\s*\*\s*\w+'],
    'use_after_free':  [r'free\s*\(\s*\w+\s*\)', r'delete\s+\w+'],
    'null_deref':      [r'\w+\s*->\s*\w+', r'\*\s*\w+\s*='],
    'format_string':   [r'printf\s*\(\s*\w+\s*\)', r'fprintf\s*\(\s*\w+\s*,\s*\w+\s*\)'],
}

def scan_vulns(code):
    found = set()
    for vtype, patterns in VULN_PATTERNS.items():
        for p in patterns:
            if re.search(p, code or '', re.IGNORECASE):
                found.add(vtype)
    return found

def is_hallucinated(orig, rewrite):
    if not rewrite or len(rewrite) < 20:
        return False, []
    orig_vulns   = scan_vulns(orig)
    rewrite_vulns = scan_vulns(rewrite)
    new_vulns = rewrite_vulns - orig_vulns
    return len(new_vulns) > 0, list(new_vulns)

def analyze(results, name):
    total = len(results)
    correct_cwe   = sum(1 for r in results if r['ground_truth_cwe'] == r['predicted_cwe'])
    unknown_preds = sum(1 for r in results if r['predicted_cwe'] == 'Unknown')
    wrong_cwe     = sum(1 for r in results
                        if r['ground_truth_cwe'] != r['predicted_cwe']
                        and r['predicted_cwe'] != 'Unknown')

    # Hallucination
    halluc_count = 0
    halluc_types = Counter()
    for r in results:
        h, htypes = is_hallucinated(r.get('vulnerable_code',''), r.get('predicted_secure',''))
        if h:
            halluc_count += 1
            halluc_types.update(htypes)

    # Truncated outputs (< 50 chars)
    truncated = sum(1 for r in results if len(r.get('raw_output','')) < 50)

    # CWE confusion matrix
    confusion = defaultdict(Counter)
    for r in results:
        gt, pred = r['ground_truth_cwe'], r['predicted_cwe']
        if gt != pred:
            confusion[gt][pred] += 1

    # Per-CWE accuracy
    per_cwe = {}
    for cwe in set(r['ground_truth_cwe'] for r in results):
        subset = [r for r in results if r['ground_truth_cwe'] == cwe]
        correct = sum(1 for r in subset if r['ground_truth_cwe'] == r['predicted_cwe'])
        per_cwe[cwe] = {'correct': correct, 'total': len(subset),
                        'accuracy': round(correct/len(subset), 3)}

    report = {
        'model': name,
        'total_samples': total,
        'correct_cwe': correct_cwe,
        'cwe_accuracy': round(correct_cwe / total, 3),
        'unknown_predictions': unknown_preds,
        'wrong_cwe_predictions': wrong_cwe,
        'truncated_outputs': truncated,
        'hallucination': {
            'count': halluc_count,
            'rate': round(halluc_count / total, 3),
            'types': dict(halluc_types)
        },
        'per_cwe_accuracy': per_cwe,
        'top_confusions': {
            gt: dict(preds.most_common(3))
            for gt, preds in sorted(confusion.items(), key=lambda x: -sum(x[1].values()))[:5]
        },
        'failure_cases': [
            {
                'sample_id': i,
                'ground_truth_cwe': r['ground_truth_cwe'],
                'predicted_cwe': r['predicted_cwe'],
                'error_type': (
                    'unknown_prediction' if r['predicted_cwe'] == 'Unknown'
                    else 'wrong_cwe' if r['ground_truth_cwe'] != r['predicted_cwe']
                    else 'correct'
                ),
                'output_length': len(r.get('raw_output', '')),
                'code_snippet': r.get('vulnerable_code', '')[:150] + '...'
            }
            for i, r in enumerate(results)
            if r['ground_truth_cwe'] != r['predicted_cwe']
        ][:15]  # Top 15 failure cases
    }

    return report

def print_report(report):
    name = report['model']
    total = report['total_samples']
    print(f"\n{'='*65}")
    print(f"  QUALITATIVE ANALYSIS: {name}")
    print(f"{'='*65}")
    print(f"  Total samples    : {total}")
    print(f"  CWE Accuracy     : {report['cwe_accuracy']:.1%} ({report['correct_cwe']}/{total})")
    print(f"  Unknown preds    : {report['unknown_predictions']} ({report['unknown_predictions']/total:.1%})")
    print(f"  Wrong CWE        : {report['wrong_cwe_predictions']} ({report['wrong_cwe_predictions']/total:.1%})")
    print(f"  Truncated output : {report['truncated_outputs']} ({report['truncated_outputs']/total:.1%})")
    h = report['hallucination']
    print(f"  Hallucination    : {h['count']} ({h['rate']:.1%})")
    if h['types']:
        print(f"    Types: {h['types']}")

    print(f"\n  Per-CWE Accuracy:")
    for cwe, stats in sorted(report['per_cwe_accuracy'].items(), key=lambda x: -x[1]['total']):
        bar = '█' * stats['correct'] + '░' * (stats['total'] - stats['correct'])
        print(f"    {cwe}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.0%}) {bar}")

    print(f"\n  Top Confusion Patterns (GT → Predicted):")
    for gt, preds in report['top_confusions'].items():
        for pred, count in preds.items():
            print(f"    {gt} → {pred}: {count}x")

    print(f"{'='*65}")

def main():
    output_dir = Path('results')

    # Load v2 results
    v2_results, v3_results = [], []
    v2_path = output_dir / 'finetuned_results_v2.jsonl'
    v3_path = output_dir / 'finetuned_results_v3.jsonl'

    if v2_path.exists():
        with open(v2_path) as f:
            v2_results = [json.loads(l) for l in f]
        print(f"✓ Loaded v2 results: {len(v2_results)} samples")
    else:
        print("⚠ v2 results not found")

    if v3_path.exists():
        with open(v3_path) as f:
            v3_results = [json.loads(l) for l in f]
        print(f"✓ Loaded v3 results: {len(v3_results)} samples")
    else:
        print("⚠ v3 results not found")

    reports = {}

    if v2_results:
        r = analyze(v2_results, 'v2 Fine-tuned (QLoRA, Big-Vul only)')
        print_report(r)
        reports['v2'] = r

    if v3_results:
        r = analyze(v3_results, 'v3 Fine-tuned (QLoRA, Big-Vul + Synthetic)')
        print_report(r)
        reports['v3'] = r

    # Compare if both exist
    if v2_results and v3_results:
        print(f"\n{'='*65}")
        print("  v2 vs v3 COMPARISON SUMMARY")
        print(f"{'='*65}")
        v2r, v3r = reports['v2'], reports['v3']
        print(f"  {'Metric':<30} {'v2':>8} {'v3':>8} {'Change':>10}")
        print(f"  {'-'*58}")
        metrics = [
            ('CWE Accuracy',       'cwe_accuracy',        True),
            ('Unknown Predictions','unknown_predictions',  False),
            ('Hallucination Rate', ('hallucination','rate'), False),
            ('Truncated Outputs',  'truncated_outputs',   False),
        ]
        for label, key, higher_is_better in metrics:
            if isinstance(key, tuple):
                v2v = v2r[key[0]][key[1]]
                v3v = v3r[key[0]][key[1]]
            else:
                v2v = v2r[key]
                v3v = v3r[key]
            diff = v3v - v2v
            if isinstance(v2v, float):
                improved = diff > 0 if higher_is_better else diff < 0
                status = '✅' if improved else '❌'
                print(f"  {label:<30} {v2v:>8.3f} {v3v:>8.3f} {diff:>+9.3f} {status}")
            else:
                improved = diff > 0 if higher_is_better else diff < 0
                status = '✅' if improved else '❌'
                print(f"  {label:<30} {v2v:>8} {v3v:>8} {diff:>+9} {status}")
        print(f"{'='*65}")

    # Save combined report
    with open(output_dir / 'qualitative_report_v2_v3.json', 'w') as f:
        json.dump(reports, f, indent=2)
    print(f"\n✅ Saved: results/qualitative_report_v2_v3.json")

if __name__ == '__main__':
    main()
