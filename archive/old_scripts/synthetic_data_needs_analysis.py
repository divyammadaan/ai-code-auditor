#!/usr/bin/env python3
"""Analyze which CWEs need synthetic data generation"""

import json
from collections import Counter

# Load v2 training data
with open('data/processed_v2/train.jsonl') as f:
    train = [json.loads(l) for l in f]

dist = Counter(r['cwe'] for r in train)

print('='*70)
print('SYNTHETIC DATA NEEDS ANALYSIS')
print('='*70)
print('\nCurrent v2 Distribution:')
print('-'*70)

# Calculate statistics
total = len(train)
avg = total / len(dist)
threshold_low = avg * 0.7  # 70% of average
threshold_high = avg * 1.3  # 130% of average

for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
    pct = (count / total) * 100
    status = ''
    if count < threshold_low:
        status = '⚠️  NEEDS BOOST'
    elif count > threshold_high:
        status = '✅ WELL-REPRESENTED'
    else:
        status = '✓  ADEQUATE'
    
    print(f'{cwe}: {count:4d} samples ({pct:5.1f}%) {status}')

print('-'*70)
print(f'Average: {avg:.0f} samples per CWE')
print(f'Low threshold: {threshold_low:.0f} samples')
print(f'High threshold: {threshold_high:.0f} samples')
print('='*70)

# Identify CWEs needing synthetic data
needs_boost = [(cwe, count) for cwe, count in dist.items() if count < threshold_low]
needs_boost.sort(key=lambda x: x[1])

print('\n🎯 CWEs NEEDING SYNTHETIC DATA (Priority Order):')
print('='*70)

for i, (cwe, count) in enumerate(needs_boost, 1):
    gap = int(avg - count)
    print(f'{i}. {cwe}: {count} samples → Need +{gap} to reach average')

print('='*70)

# Current synthetic data status
print('\n📊 CURRENT SYNTHETIC DATA STATUS:')
print('='*70)
print('CWE-190: 50 existing + 100 pending (batches 4-8) = 150 total')
print('CWE-416: 130 existing')
print('='*70)

# Calculate final distribution with pending synthetic
print('\n📈 PROJECTED DISTRIBUTION (after batches 4-8):')
print('='*70)

projected = dict(dist)
projected['CWE-190'] = projected.get('CWE-190', 0) + 150
projected['CWE-416'] = projected.get('CWE-416', 0) + 130
total_projected = sum(projected.values())
avg_projected = total_projected / len(projected)

for cwe, count in sorted(projected.items(), key=lambda x: -x[1]):
    pct = (count / total_projected) * 100
    change = count - dist.get(cwe, 0)
    change_str = f'(+{change})' if change > 0 else ''
    
    status = ''
    if count < avg_projected * 0.7:
        status = '⚠️  STILL LOW'
    elif count > avg_projected * 1.3:
        status = '✅ GOOD'
    else:
        status = '✓  BALANCED'
    
    print(f'{cwe}: {count:4d} samples ({pct:5.1f}%) {change_str:8s} {status}')

print('-'*70)
print(f'New average: {avg_projected:.0f} samples per CWE')
print('='*70)

# Recommendations
print('\n💡 RECOMMENDATIONS:')
print('='*70)

still_low = [(cwe, count) for cwe, count in projected.items() 
             if count < avg_projected * 0.7]
still_low.sort(key=lambda x: x[1])

if still_low:
    print('\n🎯 Generate synthetic data for these CWEs:')
    for cwe, count in still_low:
        gap = int(avg_projected - count)
        print(f'  • {cwe}: Need +{gap} samples to reach average')
        print(f'    Suggested: 2-3 batches of 20 samples each')
else:
    print('\n✅ All CWEs will be adequately represented after batches 4-8!')
    print('   No additional synthetic data needed.')

print('\n📋 OPTIONAL: Generate for better balance:')
for cwe, count in projected.items():
    if avg_projected * 0.7 <= count < avg_projected * 0.9:
        gap = int(avg_projected - count)
        print(f'  • {cwe}: Could use +{gap} samples (currently adequate but below average)')

print('='*70)
