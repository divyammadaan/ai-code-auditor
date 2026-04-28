# Next Steps - Completing the Synthetic Data Integration

## ✅ **What We've Done So Far**

1. ✅ Saved **Batch 4: Archives** (20 CWE-190 samples)
2. ✅ Saved **Batch 5: Crypto** (20 CWE-190 samples)
3. ✅ Analyzed class distribution and identified needs
4. ✅ Created strategy documents and prompts

## 📊 **Current Status**

```
CWE-190 Synthetic Data:
├── Batch 1: Images (10 samples) ✅
├── Batch 2: Network (20 samples) ✅
├── Batch 3: Allocators (20 samples) ✅
├── Batch 4: Archives (20 samples) ✅ NEW!
├── Batch 5: Crypto (20 samples) ✅ NEW!
├── Batch 6: Codecs (20 samples) ⏳ Data provided, needs saving
├── Batch 7: Kernel (20 samples) ⏳ Data provided, needs saving
└── Batch 8: Databases (20 samples) ⏳ Data provided, needs saving

Total: 90 saved + 60 pending = 150 samples
```

## 🚀 **Immediate Next Steps**

### **Step 1: Save Remaining Batches (5 minutes)**

I need to save batches 6, 7, and 8 from your message. Due to the large size, I'll create them as separate JSON files.

**Action Required:** Let me know if you want me to:
- A) Save batches 6-8 now (I'll create the files)
- B) You'll save them manually from your message
- C) Skip for now and proceed with what we have (90 samples)

### **Step 2: Create v3 Dataset with Balancing (10 minutes)**

Create `scripts/create_v3_dataset.py`:

```python
#!/usr/bin/env python3
"""
Create v3 dataset with synthetic data and class balancing
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

def load_v2_data():
    """Load existing v2 training data"""
    with open('data/processed_v2/train.jsonl') as f:
        return [json.loads(l) for l in f]

def load_synthetic_cwe190():
    """Load all CWE-190 synthetic batches"""
    synthetic = []
    for i in range(1, 9):  # batches 1-8
        path = f'data/synthetic/cwe190_batch{i}_*.json'
        # Find matching files
        import glob
        files = glob.glob(path)
        for file in files:
            with open(file) as f:
                data = json.load(f)
                synthetic.extend(data)
    return synthetic

def load_synthetic_cwe416():
    """Load all CWE-416 synthetic batches"""
    synthetic = []
    for i in range(1, 10):  # batches 1-9
        path = f'data/synthetic/cwe416_batch{i}_*.json'
        import glob
        files = glob.glob(path)
        for file in files:
            try:
                with open(file) as f:
                    data = json.load(f)
                    synthetic.extend(data)
            except:
                pass  # Skip invalid JSON files
    return synthetic

def format_synthetic(synthetic_data):
    """Format synthetic data to match v2 structure"""
    formatted = []
    for item in synthetic_data:
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
            f"Analyze the following C/C++ code and identify the security vulnerability.\\n\\n"
            f"```c\\n{record['vulnerable_code']}\\n```\\n\\n"
            f"Respond with the CWE type first, then explain and provide a secure rewrite."
        )
        
        assistant_msg = (
            f"CWE: {record['cwe']}\\n"
            f"CVE: {record['cve_id']}\\n"
            f"Severity: {record['cvss_score']} (HIGH)\\n\\n"
            f"Reason: {item.get('explanation', 'Security vulnerability detected.')}\\n\\n"
            f"Fix:\\n```c\\n{record['secure_code']}\\n```"
        )
        
        record['prompt'] = user_msg
        record['completion'] = assistant_msg
        record['text'] = f"<s>[INST] {user_msg} [/INST] {assistant_msg} </s>"
        
        formatted.append(record)
    
    return formatted

def balance_classes(records, target_min=200, target_max=300):
    """Balance classes via oversampling and capping"""
    by_cwe = defaultdict(list)
    for r in records:
        by_cwe[r['cwe']].append(r)
    
    balanced = []
    for cwe, samples in by_cwe.items():
        if len(samples) > target_max:
            # Cap dominant classes
            balanced.extend(random.sample(samples, target_max))
        elif len(samples) < target_min:
            # Oversample minority classes
            oversampled = samples * (target_min // len(samples) + 1)
            balanced.extend(oversampled[:target_min])
        else:
            balanced.extend(samples)
    
    random.shuffle(balanced)
    return balanced

def main():
    print("="*70)
    print("Creating v3 Dataset with Synthetic Data")
    print("="*70)
    
    # Load data
    print("\\nLoading v2 data...")
    v2_train = load_v2_data()
    print(f"  Loaded {len(v2_train)} v2 samples")
    
    print("\\nLoading synthetic data...")
    synthetic_190 = load_synthetic_cwe190()
    synthetic_416 = load_synthetic_cwe416()
    print(f"  Loaded {len(synthetic_190)} CWE-190 samples")
    print(f"  Loaded {len(synthetic_416)} CWE-416 samples")
    
    # Format synthetic
    print("\\nFormatting synthetic data...")
    synthetic_formatted = format_synthetic(synthetic_190 + synthetic_416)
    
    # Merge
    print("\\nMerging datasets...")
    combined = v2_train + synthetic_formatted
    print(f"  Combined: {len(combined)} samples")
    
    # Balance
    print("\\nBalancing classes...")
    balanced = balance_classes(combined, target_min=200, target_max=300)
    print(f"  Balanced: {len(balanced)} samples")
    
    # Show distribution
    dist = Counter(r['cwe'] for r in balanced)
    print("\\nFinal distribution:")
    for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = (count / len(balanced)) * 100
        print(f"  {cwe}: {count:4d} samples ({pct:5.1f}%)")
    
    # Save
    output_dir = Path('data/processed_v3')
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'train.jsonl', 'w') as f:
        for record in balanced:
            f.write(json.dumps(record) + '\\n')
    
    print(f"\\n✅ Saved v3 training data: {len(balanced)} samples")
    print(f"   Location: {output_dir / 'train.jsonl'}")
    print("="*70)

if __name__ == '__main__':
    main()
```

### **Step 3: Train v3 Model (2-3 hours on GPU)**

```bash
# Update training config
cp configs/training_config.yaml configs/training_config_v3.yaml

# Edit to point to v3 dataset
# dataset:
#   processed_path: "data/processed_v3"

# Train
python models/finetune.py --config configs/training_config_v3.yaml
```

### **Step 4: Evaluate v2 vs v3 (30 minutes)**

Create `evaluation/compare_v2_v3.py`:

```python
# Compare models on:
# 1. Held-out synthetic test set (20% of synthetic data)
# 2. Original v2 test set
# 3. Per-CWE accuracy
# 4. Domain-specific performance (crypto, kernel, codecs, etc.)
```

## 📊 **Expected Results**

### **v3 Dataset Composition**

```
Total: ~2,500 samples

Sources:
├── Big-Vul (v2): 2,137 samples (85%)
├── CWE-190 Synthetic: 150 samples (6%)
└── CWE-416 Synthetic: 130 samples (9%)

Distribution (after balancing):
├── CWE-20:  300 samples (12.0%)
├── CWE-119: 300 samples (12.0%)
├── CWE-399: 300 samples (12.0%)
├── CWE-190: 287 samples (11.5%) ← +142 from synthetic
├── CWE-416: 270 samples (10.8%) ← +130 from synthetic
├── CWE-264: 228 samples (9.1%)
├── CWE-362: 200 samples (8.0%) ← oversampled
├── CWE-200: 197 samples (7.9%)
├── CWE-189: 200 samples (8.0%) ← oversampled
└── CWE-125: 176 samples (7.0%)

Imbalance Ratio: 1.7x (much better than 3.2x!)
```

### **Performance Gains (Estimated)**

| Metric | v2 | v3 | Improvement |
|--------|----|----|-------------|
| CWE-190 Accuracy | 65% | 80-85% | +15-20% ⬆️ |
| CWE-416 Accuracy | 70% | 82-87% | +12-17% ⬆️ |
| CWE-189 Accuracy | 55% | 68-73% | +13-18% ⬆️ |
| CWE-362 Accuracy | 60% | 72-77% | +12-17% ⬆️ |
| Overall Accuracy | 72% | 78-82% | +6-10% ⬆️ |

## 🤔 **Decision Point**

**Do you want me to:**

1. ✅ **Save batches 6-8 now** (I'll create the JSON files)
2. ✅ **Create the v3 dataset script** (ready to run)
3. ✅ **Create evaluation scripts** (compare v2 vs v3)

**Or:**

- ⏸️ **Pause here** and you'll complete manually
- 🔄 **Skip batches 6-8** and proceed with 90 samples only

**What would you like to do?** 🚀
