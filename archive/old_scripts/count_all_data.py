#!/usr/bin/env python3
"""Count all synthetic and processed data"""

import json
import os

print("=" * 80)
print("AI CODE AUDITOR - COMPLETE DATA INVENTORY")
print("=" * 80)

# Count CWE-190 synthetic data
print("\n📊 CWE-190 (Integer Overflow) - Synthetic Data:")
print("-" * 80)
cwe190_files = [
    'data/synthetic/cwe190_batch1_images.json',
    'data/synthetic/cwe190_batch2_network.json',
    'data/synthetic/cwe190_batch3_allocators.json'
]
cwe190_total = 0
for f in cwe190_files:
    if os.path.exists(f):
        with open(f) as file:
            data = json.load(file)
            count = len(data)
            cwe190_total += count
            print(f"  ✓ {os.path.basename(f):40s} {count:3d} entries")
    else:
        print(f"  ✗ {os.path.basename(f):40s} NOT FOUND")

print(f"\n  {'TOTAL CWE-190 SYNTHETIC:':40s} {cwe190_total:3d} entries")

# Count CWE-416 synthetic data
print("\n📊 CWE-416 (Use After Free) - Synthetic Data:")
print("-" * 80)
cwe416_files = [
    'data/synthetic/cwe416_batch1_network.json',
    'data/synthetic/cwe416_batch2_kernel.json',
    'data/synthetic/cwe416_batch3_browser.json',
    'data/synthetic/cwe416_batch4_allocators.json',
    'data/synthetic/cwe416_batch5_codecs.json',
    'data/synthetic/cwe416_batch6_databases.json',
    'data/synthetic/cwe416_batch7_crypto.json',
    'data/synthetic/cwe416_batch8_graphics.json',
    'data/synthetic/cwe416_batch9_bonus.json'
]
cwe416_total = 0
for f in cwe416_files:
    if os.path.exists(f):
        try:
            with open(f) as file:
                data = json.load(file)
                count = len(data)
                cwe416_total += count
                print(f"  ✓ {os.path.basename(f):40s} {count:3d} entries")
        except json.JSONDecodeError:
            print(f"  ⚠ {os.path.basename(f):40s} INVALID JSON")
        except Exception as e:
            print(f"  ✗ {os.path.basename(f):40s} ERROR: {str(e)}")
    else:
        print(f"  ✗ {os.path.basename(f):40s} NOT FOUND")

print(f"\n  {'TOTAL CWE-416 SYNTHETIC:':40s} {cwe416_total:3d} entries")

# Count processed data (v1)
print("\n📊 Processed Training Data (v1):")
print("-" * 80)
processed_files = {
    'train': 'data/processed/train.jsonl',
    'val': 'data/processed/val.jsonl',
    'test': 'data/processed/test.jsonl'
}
v1_total = 0
for name, f in processed_files.items():
    if os.path.exists(f):
        with open(f) as file:
            count = sum(1 for _ in file)
            v1_total += count
            print(f"  ✓ {name:10s} ({os.path.basename(f):20s}) {count:4d} entries")
    else:
        print(f"  ✗ {name:10s} ({os.path.basename(f):20s}) NOT FOUND")

print(f"\n  {'TOTAL PROCESSED V1:':40s} {v1_total:4d} entries")

# Count processed data (v2)
print("\n📊 Processed Training Data (v2):")
print("-" * 80)
processed_v2_files = {
    'train': 'data/processed_v2/train.jsonl',
    'val': 'data/processed_v2/val.jsonl',
    'test': 'data/processed_v2/test.jsonl'
}
v2_total = 0
for name, f in processed_v2_files.items():
    if os.path.exists(f):
        with open(f) as file:
            count = sum(1 for _ in file)
            v2_total += count
            print(f"  ✓ {name:10s} ({os.path.basename(f):20s}) {count:4d} entries")
    else:
        print(f"  ✗ {name:10s} ({os.path.basename(f):20s}) NOT FOUND")

print(f"\n  {'TOTAL PROCESSED V2:':40s} {v2_total:4d} entries")

# Check for dataset stats
print("\n📊 Dataset Statistics:")
print("-" * 80)
stats_file = 'data/processed/dataset_stats.json'
if os.path.exists(stats_file):
    with open(stats_file) as f:
        stats = json.load(f)
        print(f"  ✓ Dataset stats available")
        if 'cwe_distribution' in stats:
            print(f"\n  CWE Distribution:")
            for cwe, count in sorted(stats['cwe_distribution'].items()):
                print(f"    - {cwe}: {count} entries")
else:
    print(f"  ✗ Dataset stats not found")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Synthetic Data:")
print(f"    - CWE-190 (Integer Overflow):     {cwe190_total:4d} entries")
print(f"    - CWE-416 (Use After Free):       {cwe416_total:4d} entries")
print(f"    - Total Synthetic:                {cwe190_total + cwe416_total:4d} entries")
print(f"\n  Processed Training Data:")
print(f"    - Version 1:                      {v1_total:4d} entries")
print(f"    - Version 2:                      {v2_total:4d} entries")
print(f"\n  Grand Total:                        {cwe190_total + cwe416_total + v1_total + v2_total:4d} entries")
print("=" * 80)

# Pending CWE-190 batches
print("\n⏳ PENDING CWE-190 BATCHES (Not Yet Created):")
print("-" * 80)
pending = [
    ("Batch 4", "Archives", "CVE-2023-SYNTH-261 to 280", 20),
    ("Batch 5", "Crypto", "CVE-2023-SYNTH-281 to 300", 20),
    ("Batch 6", "Video Codecs", "CVE-2023-SYNTH-301 to 320", 20),
    ("Batch 7", "Kernel", "CVE-2023-SYNTH-321 to 340", 20),
    ("Batch 8", "Databases", "CVE-2023-SYNTH-341 to 360", 20)
]
pending_total = 0
for batch, theme, cve_range, count in pending:
    print(f"  ⏳ {batch:10s} {theme:20s} {cve_range:30s} {count:3d} entries")
    pending_total += count

print(f"\n  {'TOTAL PENDING:':40s} {pending_total:3d} entries")
print(f"  {'POTENTIAL TOTAL CWE-190:':40s} {cwe190_total + pending_total:3d} entries")
print("=" * 80)
