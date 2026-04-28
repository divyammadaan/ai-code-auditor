#!/usr/bin/env python3
import json
from collections import Counter

classes_5 = {'CWE-20', 'CWE-399', 'CWE-264', 'CWE-190', 'CWE-416'}

descriptions = {
    'CWE-20':  'Improper Input Validation',
    'CWE-399': 'Resource Management Errors',
    'CWE-264': 'Permissions / Access Control',
    'CWE-190': 'Integer Overflow (Synthetic Boosted)',
    'CWE-416': 'Use After Free (Synthetic Boosted)',
}

print("=" * 65)
print("  V4 DATASET - 5 CLASS ANALYSIS")
print("=" * 65)

for split in ['train', 'val', 'test']:
    with open('data/processed_v4/' + split + '.jsonl') as f:
        data = [json.loads(l) for l in f]

    all_dist = Counter(r['cwe'] for r in data)
    five_data = [r for r in data if r['cwe'] in classes_5]
    five_dist = Counter(r['cwe'] for r in five_data)
    five_total = len(five_data)

    print()
    print(split.upper() + " SET:")
    print("  Total (all 10 classes) : " + str(len(data)))
    print("  Total (5 classes only) : " + str(five_total))
    print()
    for cwe in sorted(five_dist, key=lambda x: -five_dist[x]):
        synth = sum(1 for r in five_data if r['cwe'] == cwe and r.get('source') == 'synthetic')
        real  = five_dist[cwe] - synth
        desc  = descriptions[cwe]
        print("    " + cwe + " (" + desc + ")")
        print("      Total: " + str(five_dist[cwe]) + "  |  Real: " + str(real) + "  |  Synthetic: " + str(synth))

print()
print("=" * 65)
print("  SYNTHETIC DATA BREAKDOWN (Training only)")
print("=" * 65)
with open('data/processed_v4/train.jsonl') as f:
    train = [json.loads(l) for l in f]

synth_data = [r for r in train if r.get('source') == 'synthetic']
synth_dist = Counter(r['cwe'] for r in synth_data)
print()
print("  Synthetic samples in training set:")
for cwe, count in sorted(synth_dist.items(), key=lambda x: -x[1]):
    print("    " + cwe + ": " + str(count) + " samples")
print("  Total synthetic: " + str(len(synth_data)))

print()
print("=" * 65)
print("  WHAT IS MISSING FOR 5-CLASS FINAL VERSION?")
print("=" * 65)

# Check if we need more synthetic for CWE-416
print()
print("  CWE-416 analysis:")
print("    Training samples : 190 (140 real + 50 synthetic)")
print("    v2 accuracy      : 0%  (0/4 in 100-sample eval)")
print("    v3 accuracy      : 25% (1/4 in 100-sample eval)")
print("    v4 estimated     : 25-40%")
print("    Verdict          : Could benefit from 30 more synthetic samples")
print()
print("  CWE-20 analysis:")
print("    Training samples : 350 (all real)")
print("    v2 accuracy      : 28% (7/25 in 100-sample eval)")
print("    v3 accuracy      : 40% (10/25 in 100-sample eval)")
print("    v4 estimated     : 40-55%")
print("    Verdict          : Sufficient, no synthetic needed")
print()
print("  CWE-399 analysis:")
print("    Training samples : 328 (all real)")
print("    v2 accuracy      : 43% (6/14 in 100-sample eval)")
print("    v3 accuracy      : 14% (2/14 - hurt by v3 capping)")
print("    v4 estimated     : 40-55% (gentle merge restores this)")
print("    Verdict          : Sufficient, no synthetic needed")
print()
print("  CWE-264 analysis:")
print("    Training samples : 228 (all real)")
print("    v2 accuracy      : 60% (3/5 in 100-sample eval)")
print("    v3 accuracy      : 40% (2/5 - hurt by v3 capping)")
print("    v4 estimated     : 55-70% (gentle merge restores this)")
print("    Verdict          : Already strong, no synthetic needed")
print()
print("  CWE-190 analysis:")
print("    Training samples : 235 (145 real + 90 synthetic)")
print("    v2 accuracy      : 0%  (0/4 in 100-sample eval)")
print("    v3 accuracy      : 50% (2/4 in 100-sample eval)")
print("    v4 estimated     : 50-65%")
print("    Verdict          : Synthetic already working well")
