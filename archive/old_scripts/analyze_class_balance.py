#!/usr/bin/env python3
"""Analyze class distribution in v2 dataset"""

import json
from collections import Counter

# Load v2 training data
with open('data/processed_v2/train.jsonl') as f:
    train = [json.loads(l) for l in f]

# Count CWE distribution
dist = Counter(r['cwe'] for r in train)

print('='*60)
print('CURRENT V2 TRAINING DISTRIBUTION')
print('='*60)
for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
    pct = (count / len(train)) * 100
    print(f'{cwe}: {count:4d} samples ({pct:5.1f}%)')

print('='*60)
print(f'Total: {len(train)} samples')
print(f'Unique CWEs: {len(dist)}')
print(f'Most common: {dist.most_common(1)[0][0]} with {dist.most_common(1)[0][1]} samples')
print(f'Least common: {dist.most_common()[-1][0]} with {dist.most_common()[-1][1]} samples')
print(f'Imbalance ratio: {dist.most_common(1)[0][1] / dist.most_common()[-1][1]:.1f}x')
print('='*60)

# Calculate what synthetic data would add
print('\nSYNTHETIC DATA AVAILABLE:')
print('-'*60)
print('CWE-190: 50 samples (batches 1-3) + 100 pending (batches 4-8)')
print('CWE-416: 130 samples (batches 1-9)')
print('-'*60)

# Simulate balanced distribution
print('\nPROJECTED V3 DISTRIBUTION (with synthetic):')
print('='*60)

# Add synthetic to existing
projected = dict(dist)
projected['CWE-190'] = projected.get('CWE-190', 0) + 150  # 50 + 100 pending
projected['CWE-416'] = projected.get('CWE-416', 0) + 130

total_v3 = sum(projected.values())
for cwe, count in sorted(projected.items(), key=lambda x: -x[1]):
    pct = (count / total_v3) * 100
    change = count - dist.get(cwe, 0)
    change_str = f'(+{change})' if change > 0 else ''
    print(f'{cwe}: {count:4d} samples ({pct:5.1f}%) {change_str}')

print('='*60)
print(f'Total: {total_v3} samples (+{total_v3 - len(train)})')
print(f'New imbalance ratio: {max(projected.values()) / min(projected.values()):.1f}x')
print(f'Improvement: {(dist.most_common(1)[0][1] / dist.most_common()[-1][1]) / (max(projected.values()) / min(projected.values())):.1f}x better balance')
print('='*60)
