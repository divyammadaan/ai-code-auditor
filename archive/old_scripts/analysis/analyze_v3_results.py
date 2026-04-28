#!/usr/bin/env python3
"""Analyze and compare v2 vs v3 evaluation results"""

import json

v2 = {
    'cwe_accuracy': 0.26, 'bleu4': 5.69, 'rougeL': 0.270, 'unknown_count': 31,
    'per_cwe': {
        'CWE-119': {'correct': 2, 'total': 27},
        'CWE-20':  {'correct': 7, 'total': 25},
        'CWE-399': {'correct': 6, 'total': 14},
        'CWE-125': {'correct': 6, 'total': 10},
        'CWE-200': {'correct': 0, 'total': 8},
        'CWE-264': {'correct': 3, 'total': 5},
        'CWE-190': {'correct': 0, 'total': 4},
        'CWE-416': {'correct': 0, 'total': 4},
        'CWE-189': {'correct': 0, 'total': 2},
        'CWE-362': {'correct': 0, 'total': 1}
    }
}

with open('results/evaluation_metrics_v3.json') as f:
    v3 = json.load(f)['finetuned_v3']

print('='*60)
print('  v2 vs v3 RESULTS COMPARISON')
print('='*60)

v2_acc = v2['cwe_accuracy']
v3_acc = v3['cwe_accuracy']
acc_diff = (v3_acc - v2_acc) * 100

print(f'\n  Overall CWE Accuracy:')
print(f'    v2: {v2_acc:.0%} (26/100)')
print(f'    v3: {v3_acc:.0%} ({v3["correct"]}/100)')
print(f'    Change: {acc_diff:+.0f}%  {"✅ IMPROVED" if acc_diff > 0 else "❌ REGRESSED"}')

print(f'\n  BLEU-4:')
print(f'    v2: {v2["bleu4"]:.2f}  ->  v3: {v3["bleu4"]:.2f}  ({v3["bleu4"]-v2["bleu4"]:+.2f})')

print(f'\n  ROUGE-L:')
print(f'    v2: {v2["rougeL"]:.3f}  ->  v3: {v3["rougeL"]:.3f}  ({v3["rougeL"]-v2["rougeL"]:+.3f})')

print(f'\n  Unknown predictions (lower is better):')
print(f'    v2: {v2["unknown_count"]}/100  ->  v3: {v3["unknown_count"]}/100  ({v3["unknown_count"]-v2["unknown_count"]:+d})')

print(f'\n  Per-CWE Breakdown:')
print('  ' + '-'*55)

target_cwes = ['CWE-190', 'CWE-416', 'CWE-189', 'CWE-362']
all_cwes = ['CWE-190','CWE-416','CWE-189','CWE-362','CWE-125','CWE-20','CWE-119','CWE-399','CWE-200','CWE-264']

for cwe in all_cwes:
    v2c = v2['per_cwe'].get(cwe, {'correct': 0, 'total': 0})
    v3c = v3['per_cwe'].get(cwe, {'correct': 0, 'total': 0, 'accuracy': 0})
    v2a = v2c['correct'] / v2c['total'] if v2c['total'] > 0 else 0
    v3a = v3c.get('accuracy', 0)
    diff = v3a - v2a
    tag = ' <- TARGET' if cwe in target_cwes else ''

    if diff > 0:
        status = f'+{diff:.0%} ✅'
    elif diff < 0:
        status = f'{diff:.0%} ❌'
    else:
        status = '= no change'

    print(f'  {cwe}: {v2c["correct"]}/{v2c["total"]} ({v2a:.0%}) -> {v3c["correct"]}/{v3c["total"]} ({v3a:.0%})  [{status}]{tag}')

print('='*60)

# Summary
print('\n  SUMMARY:')
improved = sum(1 for cwe in all_cwes
               if v3['per_cwe'].get(cwe, {}).get('accuracy', 0) >
               (v2['per_cwe'].get(cwe, {})['correct'] / v2['per_cwe'].get(cwe, {})['total']
                if v2['per_cwe'].get(cwe, {}).get('total', 0) > 0 else 0))
regressed = sum(1 for cwe in all_cwes
                if v3['per_cwe'].get(cwe, {}).get('accuracy', 0) <
                (v2['per_cwe'].get(cwe, {})['correct'] / v2['per_cwe'].get(cwe, {})['total']
                 if v2['per_cwe'].get(cwe, {}).get('total', 0) > 0 else 0))

print(f'  CWEs improved: {improved}/10')
print(f'  CWEs regressed: {regressed}/10')
print(f'  Unknown predictions increased: {v3["unknown_count"] - v2["unknown_count"]:+d} (this is the main issue)')
print('='*60)
