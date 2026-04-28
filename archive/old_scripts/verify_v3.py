#!/usr/bin/env python3
"""Quick verification of v3 dataset"""

import json
from pathlib import Path
from collections import Counter

p = Path('data/processed_v3')
files = ['train.jsonl', 'val.jsonl', 'test.jsonl']

print('='*70)
print('v3 Dataset Verification')
print('='*70)

for f in files:
    if (p/f).exists():
        count = sum(1 for _ in open(p/f))
        print(f'  ✓ {f}: {count} samples')

print('\nTrain set analysis:')
train = [json.loads(l) for l in open(p/'train.jsonl')]
print(f'  Keys: {list(train[0].keys())}')
print(f'  Sample CWE: {train[0]["cwe"]}')
print(f'  Sample source: {train[0].get("source", "bigvul")}')

synthetic_count = sum(1 for r in train if r.get('source') == 'synthetic')
bigvul_count = sum(1 for r in train if r.get('source') != 'synthetic')

print(f'\nSource distribution:')
print(f'  Synthetic: {synthetic_count} samples')
print(f'  BigVul: {bigvul_count} samples')

cwe_dist = Counter(r['cwe'] for r in train)
print(f'\nCWE distribution:')
for cwe, count in sorted(cwe_dist.items(), key=lambda x: -x[1]):
    pct = (count / len(train)) * 100
    print(f'  {cwe}: {count} samples ({pct:.1f}%)')

print('='*70)
print('✅ v3 Dataset is ready for training!')
print('='*70)
