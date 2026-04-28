#!/usr/bin/env python3
"""
Create v4 dataset - Simple merge strategy (NO aggressive balancing)

Key difference from v3:
- v3: Capped dominant classes (CWE-119/20 from 350→300) → caused regressions
- v4: Just ADD synthetic data on top of v2, no capping, minimal oversampling
- Only oversample classes with <150 samples to bring them to 150 minimum
"""

import json
import random
import glob
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

def load_v2_data():
    print("Loading v2 training data...")
    with open('data/processed_v2/train.jsonl') as f:
        data = [json.loads(line) for line in f]
    print(f"  ✓ {len(data)} samples")
    return data

def load_synthetic_cwe190():
    print("Loading CWE-190 synthetic...")
    synthetic = []
    files = sorted([f for f in glob.glob('data/synthetic/cwe190_batch*.json') if 'status' not in f])
    for file in files:
        with open(file) as f:
            data = json.load(f)
            synthetic.extend(data)
            print(f"  ✓ {Path(file).name}: {len(data)} samples")
    print(f"  ✓ Total: {len(synthetic)}")
    return synthetic

def load_synthetic_cwe416():
    print("Loading CWE-416 synthetic...")
    synthetic = []
    files = sorted([f for f in glob.glob('data/synthetic/cwe416_batch*.json') if 'receipt' not in f])
    for file in files:
        try:
            with open(file) as f:
                data = json.load(f)
                synthetic.extend(data)
                print(f"  ✓ {Path(file).name}: {len(data)} samples")
        except json.JSONDecodeError:
            print(f"  ✗ {Path(file).name}: Invalid JSON, skipping")
    print(f"  ✓ Total: {len(synthetic)}")
    return synthetic

def format_synthetic(synthetic_data):
    print("Formatting synthetic data...")
    formatted = []
    for idx, item in enumerate(synthetic_data):
        try:
            if 'vulnerable_code' not in item or 'secure_code' not in item:
                continue
            record = {
                'cwe': item['cwe'],
                'cve_id': item.get('cve_id', 'N/A'),
                'cvss_score': item.get('cvss_score', '7.0'),
                'vulnerable_code': item['vulnerable_code'],
                'secure_code': item['secure_code'],
                'source': 'synthetic'
            }
            user_msg = (
                f"Analyze the following C/C++ code and identify the security vulnerability.\n\n"
                f"```c\n{record['vulnerable_code']}\n```\n\n"
                f"Respond with the CWE type first, then explain and provide a secure rewrite."
            )
            assistant_msg = (
                f"CWE: {record['cwe']}\n"
                f"CVE: {record['cve_id']}\n"
                f"Severity: {record['cvss_score']} (HIGH)\n\n"
                f"Reason: {item.get('explanation', 'Security vulnerability detected.')}\n\n"
                f"Fix:\n```c\n{record['secure_code']}\n```"
            )
            record['prompt'] = user_msg
            record['completion'] = assistant_msg
            record['text'] = f"<s>[INST] {user_msg} [/INST] {assistant_msg} </s>"
            formatted.append(record)
        except Exception:
            continue
    print(f"  ✓ {len(formatted)} usable synthetic samples")
    return formatted

def gentle_balance(records, min_samples=150):
    """
    v4 strategy: ONLY oversample classes below min_samples threshold.
    NO capping of dominant classes (that's what broke v3).
    """
    print(f"\nGentle balancing (min={min_samples}, NO capping)...")
    by_cwe = defaultdict(list)
    for r in records:
        by_cwe[r['cwe']].append(r)

    balanced = []
    for cwe, samples in by_cwe.items():
        if len(samples) < min_samples:
            # Only oversample if really small
            multiplier = (min_samples // len(samples)) + 1
            oversampled = (samples * multiplier)[:min_samples]
            balanced.extend(oversampled)
            print(f"  {cwe}: {len(samples)} → {min_samples} (oversampled)")
        else:
            balanced.extend(samples)
            print(f"  {cwe}: {len(samples)} (kept as-is)")

    random.shuffle(balanced)
    return balanced

def print_distribution(records, title):
    dist = Counter(r['cwe'] for r in records)
    print(f"\n{title}:")
    print("="*60)
    for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = (count / len(records)) * 100
        print(f"  {cwe}: {count:4d} ({pct:5.1f}%)")
    print(f"  Total: {len(records)}")
    if len(dist) > 1:
        print(f"  Imbalance ratio: {max(dist.values())/min(dist.values()):.1f}x")
    print("="*60)

def main():
    print("="*60)
    print("Creating v4 Dataset (Simple Merge Strategy)")
    print("="*60)
    print("\nStrategy: Add synthetic data, minimal oversampling only")
    print("No capping of dominant classes (fixes v3 regression)\n")

    v2_train = load_v2_data()
    print()
    synthetic_190 = load_synthetic_cwe190()
    print()
    synthetic_416 = load_synthetic_cwe416()
    print()
    synthetic_formatted = format_synthetic(synthetic_190 + synthetic_416)
    print()

    # Merge
    combined = v2_train + synthetic_formatted
    print(f"Merged: {len(v2_train)} v2 + {len(synthetic_formatted)} synthetic = {len(combined)} total")

    print_distribution(combined, "Before Balancing")

    # Gentle balance - only bring up tiny classes
    balanced = gentle_balance(combined, min_samples=150)

    print_distribution(balanced, "After Gentle Balancing")

    # Save
    output_dir = Path('data/processed_v4')
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / 'train.jsonl', 'w') as f:
        for record in balanced:
            f.write(json.dumps(record) + '\n')
    print(f"\n✅ Saved train.jsonl: {len(balanced)} samples")

    # Copy val/test from v2
    for split in ['val', 'test']:
        src = Path(f'data/processed_v2/{split}.jsonl')
        dst = output_dir / f'{split}.jsonl'
        with open(src) as f:
            data = [json.loads(l) for l in f]
        with open(dst, 'w') as f:
            for r in data:
                f.write(json.dumps(r) + '\n')
        print(f"✅ Copied {split}.jsonl: {len(data)} samples")

    print("\n" + "="*60)
    print("✅ v4 Dataset Ready!")
    print("="*60)
    print(f"\nLocation: data/processed_v4/")
    print(f"  train.jsonl: {len(balanced)} samples")
    print(f"\nKey differences from v3:")
    print(f"  ✓ No capping of CWE-119/20/399 (they stay at 350/350/328)")
    print(f"  ✓ Only tiny classes oversampled to 150 minimum")
    print(f"  ✓ Synthetic data still added for CWE-190/416")
    print(f"  ✓ Expected: better overall accuracy + CWE-190/416 gains")
    print("="*60)

if __name__ == '__main__':
    main()
