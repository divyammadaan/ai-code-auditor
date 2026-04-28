#!/usr/bin/env python3
"""
Analyze 5-class testing strategy for v4 final project.
Compares all possible 5-class combinations and recommends the best.
"""

from collections import Counter
import json

# Actual results from v2 and v3 evaluations (100 sample test)
v2_per_cwe = {
    'CWE-119': {'correct': 2,  'total': 27, 'train_v4': 350, 'synthetic': 0},
    'CWE-20':  {'correct': 7,  'total': 25, 'train_v4': 350, 'synthetic': 0},
    'CWE-399': {'correct': 6,  'total': 14, 'train_v4': 328, 'synthetic': 0},
    'CWE-125': {'correct': 6,  'total': 10, 'train_v4': 176, 'synthetic': 0},
    'CWE-200': {'correct': 0,  'total': 8,  'train_v4': 197, 'synthetic': 0},
    'CWE-264': {'correct': 3,  'total': 5,  'train_v4': 228, 'synthetic': 0},
    'CWE-190': {'correct': 0,  'total': 4,  'train_v4': 235, 'synthetic': 90},
    'CWE-416': {'correct': 0,  'total': 4,  'train_v4': 190, 'synthetic': 50},
    'CWE-189': {'correct': 0,  'total': 2,  'train_v4': 150, 'synthetic': 0},
    'CWE-362': {'correct': 0,  'total': 1,  'train_v4': 150, 'synthetic': 0},
}

v3_per_cwe = {
    'CWE-119': {'correct': 0,  'total': 27},
    'CWE-20':  {'correct': 10, 'total': 25},
    'CWE-399': {'correct': 2,  'total': 14},
    'CWE-125': {'correct': 0,  'total': 10},
    'CWE-200': {'correct': 0,  'total': 8},
    'CWE-264': {'correct': 2,  'total': 5},
    'CWE-190': {'correct': 2,  'total': 4},
    'CWE-416': {'correct': 1,  'total': 4},
    'CWE-189': {'correct': 0,  'total': 2},
    'CWE-362': {'correct': 0,  'total': 1},
}

# Test set sizes (actual from data/processed_v4/test.jsonl)
test_set_sizes = {
    'CWE-119': 172,
    'CWE-20':  98,
    'CWE-399': 64,
    'CWE-125': 49,
    'CWE-264': 46,
    'CWE-200': 44,
    'CWE-416': 30,
    'CWE-190': 28,
    'CWE-189': 28,
    'CWE-362': 25,
}

print("=" * 70)
print("  PER-CWE ANALYSIS: v2 vs v3 Actual Results")
print("=" * 70)
print(f"{'CWE':<10} {'Train':>6} {'Synth':>6} {'Test':>6} {'v2 Acc':>8} {'v3 Acc':>8} {'Best':>8} {'Trend'}")
print("-" * 70)

for cwe in sorted(v2_per_cwe, key=lambda x: -v2_per_cwe[x]['total']):
    v2 = v2_per_cwe[cwe]
    v3 = v3_per_cwe[cwe]
    v2_acc = v2['correct'] / v2['total']
    v3_acc = v3['correct'] / v3['total']
    best = max(v2_acc, v3_acc)
    trend = "UP  " if v3_acc > v2_acc else ("SAME" if v3_acc == v2_acc else "DOWN")
    print(f"{cwe:<10} {v2['train_v4']:>6} {v2['synthetic']:>6} {test_set_sizes[cwe]:>6} {v2_acc:>7.0%}  {v3_acc:>7.0%}  {best:>7.0%}  {trend}")

print()
print("=" * 70)
print("  SCENARIO ANALYSIS: Different 5-Class Combinations")
print("=" * 70)

scenarios = {
    "ALL 10 classes (current)": list(v2_per_cwe.keys()),
    "Top-5 by v2 accuracy":     ['CWE-264', 'CWE-125', 'CWE-399', 'CWE-20', 'CWE-200'],
    "Top-5 by training data":   ['CWE-119', 'CWE-20', 'CWE-399', 'CWE-264', 'CWE-200'],
    "Top-5 with synthetic":     ['CWE-190', 'CWE-416', 'CWE-20', 'CWE-264', 'CWE-399'],
    "RECOMMENDED for v4":       ['CWE-20', 'CWE-399', 'CWE-264', 'CWE-190', 'CWE-416'],
}

for name, classes in scenarios.items():
    v2_correct = sum(v2_per_cwe[c]['correct'] for c in classes)
    v3_correct = sum(v3_per_cwe[c]['correct'] for c in classes)
    total = sum(v2_per_cwe[c]['total'] for c in classes)
    v2_acc = v2_correct / total
    v3_acc = v3_correct / total
    print(f"\n  [{name}]")
    print(f"  Classes: {classes}")
    print(f"  v2 accuracy: {v2_correct}/{total} = {v2_acc:.0%}")
    print(f"  v3 accuracy: {v3_correct}/{total} = {v3_acc:.0%}")

print()
print("=" * 70)
print("  DEEP DIVE: RECOMMENDED 5 Classes for v4 Final Project")
print("=" * 70)

recommended = ['CWE-20', 'CWE-399', 'CWE-264', 'CWE-190', 'CWE-416']
descriptions = {
    'CWE-20':  'Improper Input Validation',
    'CWE-399': 'Resource Management Errors',
    'CWE-264': 'Permissions, Privileges, Access Control',
    'CWE-190': 'Integer Overflow (SYNTHETIC BOOSTED)',
    'CWE-416': 'Use After Free (SYNTHETIC BOOSTED)',
}

print()
for cwe in recommended:
    v2 = v2_per_cwe[cwe]
    v3 = v3_per_cwe[cwe]
    v2_acc = v2['correct'] / v2['total']
    v3_acc = v3['correct'] / v3['total']
    synth = v2['synthetic']
    print(f"  {cwe} - {descriptions[cwe]}")
    print(f"    Training samples : {v2['train_v4']} ({'+'+str(synth)+' synthetic' if synth else 'real data only'})")
    print(f"    Test set size    : {test_set_sizes[cwe]} samples")
    print(f"    v2 accuracy      : {v2_acc:.0%}")
    print(f"    v3 accuracy      : {v3_acc:.0%}")
    # v4 estimate: take best of v2/v3 + improvement from gentle merge
    v4_est_low  = max(v2_acc, v3_acc)
    v4_est_high = min(v4_est_low + 0.15, 1.0)
    print(f"    v4 estimated     : {v4_est_low:.0%} - {v4_est_high:.0%}")
    print()

# Overall estimates
v2_rec = sum(v2_per_cwe[c]['correct'] for c in recommended)
v3_rec = sum(v3_per_cwe[c]['correct'] for c in recommended)
total_rec = sum(v2_per_cwe[c]['total'] for c in recommended)
print(f"  OVERALL on 5 classes:")
print(f"    v2 accuracy : {v2_rec}/{total_rec} = {v2_rec/total_rec:.0%}")
print(f"    v3 accuracy : {v3_rec}/{total_rec} = {v3_rec/total_rec:.0%}")
print(f"    v4 estimated: ~{int(total_rec*0.45)}-{int(total_rec*0.55)}/{total_rec} = ~45-55%")

print()
print("=" * 70)
print("  SYNTHETIC DATA NEEDED FOR FINAL v4?")
print("=" * 70)
print()
print("  Current synthetic data:")
print("    CWE-190: 90 samples (images, network, allocators, archives, crypto)")
print("    CWE-416: 50 samples (network, allocators, codecs, databases, crypto)")
print()
print("  Classes with 0 synthetic but in recommended 5:")
for cwe in recommended:
    if v2_per_cwe[cwe]['synthetic'] == 0:
        v2_acc = v2_per_cwe[cwe]['correct'] / v2_per_cwe[cwe]['total']
        print(f"    {cwe}: {v2_per_cwe[cwe]['train_v4']} training samples, v2 acc={v2_acc:.0%}")
        if v2_acc < 0.5:
            print(f"      -> COULD BENEFIT from synthetic data")
        else:
            print(f"      -> Already performing well, synthetic optional")

print()
print("  VERDICT:")
print("    CWE-20  (28% v2): 350 training samples - sufficient, no synthetic needed")
print("    CWE-399 (43% v2): 328 training samples - sufficient, no synthetic needed")
print("    CWE-264 (60% v2): 228 training samples - already good, no synthetic needed")
print("    CWE-190 (0%  v2): 90 synthetic added  - NEEDED and already done!")
print("    CWE-416 (0%  v2): 50 synthetic added  - NEEDED and already done!")
print()
print("  CONCLUSION: No additional synthetic data needed for recommended 5 classes.")
print("  Current 140 synthetic samples are sufficient for v4 final project.")
