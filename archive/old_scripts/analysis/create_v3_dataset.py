#!/usr/bin/env python3
"""
Create v3 dataset with synthetic data and class balancing

This script:
1. Loads v2 training data (Big-Vul dataset)
2. Loads all synthetic CWE-190 and CWE-416 batches
3. Formats synthetic data to match v2 structure
4. Balances classes via oversampling and capping
5. Saves balanced v3 dataset
"""

import json
import random
import glob
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

def load_v2_data():
    """Load existing v2 training data"""
    print("Loading v2 training data...")
    with open('data/processed_v2/train.jsonl') as f:
        data = [json.loads(line) for line in f]
    print(f"  ✓ Loaded {len(data)} v2 samples")
    return data

def load_synthetic_cwe190():
    """Load all CWE-190 synthetic batches"""
    print("Loading CWE-190 synthetic data...")
    synthetic = []
    
    # Find all CWE-190 batch files (excluding status file)
    pattern = 'data/synthetic/cwe190_batch*.json'
    files = [f for f in glob.glob(pattern) if 'status' not in f]
    
    for file in sorted(files):
        with open(file) as f:
            data = json.load(f)
            synthetic.extend(data)
            print(f"  ✓ {Path(file).name}: {len(data)} samples")
    
    print(f"  ✓ Total CWE-190: {len(synthetic)} samples")
    return synthetic

def load_synthetic_cwe416():
    """Load all CWE-416 synthetic batches"""
    print("Loading CWE-416 synthetic data...")
    synthetic = []
    
    # Find all CWE-416 batch files (excluding receipt files)
    pattern = 'data/synthetic/cwe416_batch*.json'
    files = [f for f in glob.glob(pattern) if 'receipt' not in f]
    
    for file in sorted(files):
        try:
            with open(file) as f:
                data = json.load(f)
                synthetic.extend(data)
                print(f"  ✓ {Path(file).name}: {len(data)} samples")
        except json.JSONDecodeError:
            print(f"  ✗ {Path(file).name}: Invalid JSON, skipping")
    
    print(f"  ✓ Total CWE-416: {len(synthetic)} samples")
    return synthetic

def format_synthetic(synthetic_data):
    """Format synthetic data to match v2 structure"""
    print("Formatting synthetic data...")
    formatted = []
    
    for idx, item in enumerate(synthetic_data):
        try:
            # Create v2-style record
            record = {
                'cwe': item['cwe'],
                'cve_id': item.get('cve_id', 'N/A'),
                'cvss_score': item.get('cvss_score', '7.0'),
                'vulnerable_code': item['vulnerable_code'],
                'secure_code': item['secure_code'],
                'source': 'synthetic'  # Track origin
            }
            
            # Format prompt (same as v2)
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
        except KeyError as e:
            print(f"  ✗ Error at index {idx}: Missing key {e}")
            print(f"    Available keys: {list(item.keys())}")
            print(f"    CVE: {item.get('cve_id', 'unknown')}")
            continue
    
    print(f"  ✓ Formatted {len(formatted)} synthetic samples")
    return formatted

def balance_classes(records, target_min=200, target_max=300):
    """Balance classes via oversampling and capping"""
    print(f"\nBalancing classes (min={target_min}, max={target_max})...")
    
    # Group by CWE
    by_cwe = defaultdict(list)
    for r in records:
        by_cwe[r['cwe']].append(r)
    
    print("\nBefore balancing:")
    for cwe in sorted(by_cwe.keys()):
        print(f"  {cwe}: {len(by_cwe[cwe])} samples")
    
    # Balance each class
    balanced = []
    for cwe, samples in by_cwe.items():
        if len(samples) > target_max:
            # Cap dominant classes
            selected = random.sample(samples, target_max)
            balanced.extend(selected)
            print(f"  {cwe}: Capped {len(samples)} → {target_max}")
        elif len(samples) < target_min:
            # Oversample minority classes
            multiplier = (target_min // len(samples)) + 1
            oversampled = samples * multiplier
            selected = oversampled[:target_min]
            balanced.extend(selected)
            print(f"  {cwe}: Oversampled {len(samples)} → {target_min}")
        else:
            balanced.extend(samples)
            print(f"  {cwe}: Kept {len(samples)} samples")
    
    # Shuffle to mix sources
    random.shuffle(balanced)
    
    print(f"\n  ✓ Balanced dataset: {len(balanced)} samples")
    return balanced

def save_dataset(records, output_path):
    """Save dataset to JSONL format"""
    print(f"\nSaving dataset to {output_path}...")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    print(f"  ✓ Saved {len(records)} samples")

def print_distribution(records, title="Distribution"):
    """Print class distribution"""
    dist = Counter(r['cwe'] for r in records)
    
    print(f"\n{title}:")
    print("=" * 70)
    for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = (count / len(records)) * 100
        bar = '█' * int(pct / 2)
        print(f"  {cwe}: {count:4d} samples ({pct:5.1f}%) {bar}")
    
    print("=" * 70)
    print(f"  Total: {len(records)} samples")
    print(f"  Unique CWEs: {len(dist)}")
    print(f"  Most common: {dist.most_common(1)[0][0]} ({dist.most_common(1)[0][1]} samples)")
    print(f"  Least common: {dist.most_common()[-1][0]} ({dist.most_common()[-1][1]} samples)")
    
    if len(dist) > 1:
        imbalance = dist.most_common(1)[0][1] / dist.most_common()[-1][1]
        print(f"  Imbalance ratio: {imbalance:.1f}x")
    print("=" * 70)

def main():
    print("=" * 70)
    print("Creating v3 Dataset with Synthetic Data and Class Balancing")
    print("=" * 70)
    print()
    
    # Load data
    v2_train = load_v2_data()
    print()
    
    synthetic_190 = load_synthetic_cwe190()
    print()
    
    synthetic_416 = load_synthetic_cwe416()
    print()
    
    # Format synthetic
    synthetic_formatted = format_synthetic(synthetic_190 + synthetic_416)
    print()
    
    # Merge
    print("Merging datasets...")
    combined = v2_train + synthetic_formatted
    print(f"  ✓ Combined: {len(combined)} samples")
    print(f"    - v2: {len(v2_train)} samples")
    print(f"    - synthetic: {len(synthetic_formatted)} samples")
    
    # Show distribution before balancing
    print_distribution(combined, "Distribution Before Balancing")
    
    # Balance
    balanced = balance_classes(combined, target_min=200, target_max=300)
    
    # Show distribution after balancing
    print_distribution(balanced, "Distribution After Balancing")
    
    # Save
    save_dataset(balanced, 'data/processed_v3/train.jsonl')
    
    # Copy val and test sets from v2
    print("\nCopying validation and test sets from v2...")
    for split in ['val', 'test']:
        src = Path(f'data/processed_v2/{split}.jsonl')
        dst = Path(f'data/processed_v3/{split}.jsonl')
        
        if src.exists():
            with open(src) as f:
                data = [json.loads(line) for line in f]
            
            with open(dst, 'w') as f:
                for record in data:
                    f.write(json.dumps(record) + '\n')
            
            print(f"  ✓ Copied {split}.jsonl ({len(data)} samples)")
    
    print("\n" + "=" * 70)
    print("✅ v3 Dataset Created Successfully!")
    print("=" * 70)
    print(f"\nLocation: data/processed_v3/")
    print(f"  - train.jsonl: {len(balanced)} samples (balanced)")
    print(f"  - val.jsonl: copied from v2")
    print(f"  - test.jsonl: copied from v2")
    print("\nNext steps:")
    print("  1. Update training config to use v3 dataset")
    print("  2. Train v3 model: python models/finetune.py")
    print("  3. Evaluate and compare with v2")
    print("=" * 70)

if __name__ == '__main__':
    main()
