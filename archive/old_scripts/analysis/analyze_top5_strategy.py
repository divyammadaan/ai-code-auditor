#!/usr/bin/env python3
"""Analyze which 5 CWEs to focus on for v4"""

import json

v2_per_cwe = {
    'CWE-119': {'correct': 2,  'total': 27},
    'CWE-20':  {'correct': 7,  'total': 25},
    'CWE-399': {'correct': 6,  'total': 14},
    'CWE-125': {'correct': 6,  'total': 10},
    'CWE-200': {'correct': 0,  'total': 8},
    'CWE-264': {'correct': 3,  'total': 5},
    'CWE-190': {'correct': 0,  'total': 4},
    'CWE-416': {'correct': 0,  'total': 4},
    'CWE-189': {'correct': 0,  'total': 2},
    'CWE-362': {'correct': 0,  'total': 1}
}

v3_per_cwe = {
    'CWE-119': {'correct': 0,  'total': 27, 'accuracy': 0.0},
    'CWE-20':  {'correct': 10, 'total': 25, 'accuracy': 0.4},
    'CWE-399': {'correct': 2,  'total': 14, 'accuracy': 0.143},
    'CWE-125': {'correct': 0,  'total': 10, 'accuracy': 0.0},
    'CWE-200': {'correct': 0,  'total': 8,  'accuracy': 0.0},
    'CWE-264': {'correct': 2,  'total': 5,  'accuracy': 0.4},
    'CWE-190': {'correct': 2,  'total': 4,  'accuracy': 0.5},
    'CWE-416': {'correct': 1,  'total': 4,  'accuracy': 0.25},
    'CWE-189': {'correct': 0,  'total': 2,  'accuracy': 0.0},
    'CWE-362': {'correct': 0,  'total': 1,  'accuracy': 0.0}
}

v2_train = {
    'CWE-20': 350, 'CWE-119': 350, 'CWE-399': 328,
    'CWE-264': 228, 'CWE-200': 197, 'CWE-125': 176,
    'CWE-190': 145, 'CWE-416': 140, 'CWE-362': 114, 'CWE-189': 109
}

synthetic_available = {
    'CWE-190': 90,
    'CWE-416': 50,
}

print('='*70)
print('CWE ANALYSIS - Which 5 to Focus On?')
print('='*70)
print(f'{"CWE":<10} {"Train":>8} {"v2 Acc":>8} {"v3 Acc":>8} {"Synth":>8} {"Score":>8}')
print('-'*70)

scores = {}
for cwe in v2_per_cwe:
    v2a = v2_per_cwe[cwe]['correct'] / v2_per_cwe[cwe]['total'] if v2_per_cwe[cwe]['total'] > 0 else 0
    v3a = v3_per_cwe[cwe]['accuracy']
    train = v2_train[cwe]
    synth = synthetic_available.get(cwe, 0)

    # Score = training samples (more = better candidate) + v3 improvement bonus
    improvement = v3a - v2a
    score = train + (synth * 2) + (improvement * 100)
    scores[cwe] = score

    print(f'{cwe:<10} {train:>8} {v2a:>8.0%} {v3a:>8.0%} {synth:>8} {score:>8.0f}')

print('='*70)

# Top 5 recommendation
top5 = sorted(scores.items(), key=lambda x: -x[1])[:5]
print('\n🎯 RECOMMENDED TOP 5 CWEs:')
print('-'*40)
for i, (cwe, score) in enumerate(top5, 1):
    v2a = v2_per_cwe[cwe]['correct'] / v2_per_cwe[cwe]['total'] if v2_per_cwe[cwe]['total'] > 0 else 0
    v3a = v3_per_cwe[cwe]['accuracy']
    train = v2_train[cwe]
    synth = synthetic_available.get(cwe, 0)
    print(f'  {i}. {cwe}')
    print(f'     Training samples: {train}')
    print(f'     v2 accuracy: {v2a:.0%} | v3 accuracy: {v3a:.0%}')
    print(f'     Synthetic available: {synth} samples')
    print(f'     Synthetic needed: {max(0, 200 - train - synth)} more samples')
    print()

print('='*70)
print('\n📊 STRATEGY FOR TOP 5:')
print('-'*40)
print('Focus training ONLY on these 5 CWEs:')
for cwe, _ in top5:
    train = v2_train[cwe]
    synth = synthetic_available.get(cwe, 0)
    total = train + synth
    needed = max(0, 300 - total)
    print(f'  {cwe}: {train} real + {synth} synthetic = {total} total (need {needed} more)')

print('\nBenefits:')
print('  ✅ Focused model - better at fewer classes')
print('  ✅ Less class confusion')
print('  ✅ Easier to generate targeted synthetic data')
print('  ✅ Cleaner evaluation (5 classes vs 10)')
print('  ✅ Higher accuracy on chosen classes')
print('='*70)
