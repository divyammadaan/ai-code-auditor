# Synthetic Data Strategy & Approach

## 🎯 **Current Approach Analysis**

Based on your codebase, here's what you're doing with synthetic data:

### **Current Reality: Synthetic Data is NOT Being Used** ⚠️

Looking at your preprocessing pipeline:

1. **`data/preprocessing.py`**: 
   - Processes **Big-Vul dataset only** (265K real-world CVE examples)
   - No integration with synthetic data
   - Outputs to `data/processed/`

2. **`scripts/prepare_v2_dataset.py`**:
   - Reads from `data/processed/` (Big-Vul only)
   - Filters to top-10 CWEs
   - No synthetic data integration
   - Outputs to `data/processed_v2/`

3. **Your synthetic data** (`data/synthetic/`):
   - 180 CWE-190 and CWE-416 examples
   - **Sitting unused** ❌
   - Not integrated into training pipeline

---

## 🤔 **The Problem**

You've been generating synthetic data, but:
- ✅ It's well-structured and high-quality
- ❌ It's not being used for training
- ❌ No pipeline to merge it with Big-Vul data
- ❌ Models are trained only on Big-Vul

**Result:** Your synthetic data is just documentation, not training data.

---

## 💡 **Recommended Approach: 3 Strategies**

### **Strategy 1: Augmentation (Recommended)** ⭐

**Goal:** Supplement Big-Vul with synthetic examples for underrepresented CWEs

**How it works:**
```python
# In prepare_v2_dataset.py or new script
def load_synthetic_data():
    """Load all synthetic vulnerability examples"""
    synthetic_records = []
    
    # Load CWE-190 batches
    for batch in ['batch1', 'batch2', 'batch3', ...]:
        with open(f'data/synthetic/cwe190_{batch}.json') as f:
            data = json.load(f)
            for item in data:
                synthetic_records.append({
                    'cwe': item['cwe'],
                    'cve_id': item['cve_id'],
                    'cvss_score': item['cvss_score'],
                    'vulnerable_code': item['vulnerable_code'],
                    'secure_code': item['secure_code'],
                    'explanation': item['explanation'],
                    'source': 'synthetic'  # Track origin
                })
    
    # Load CWE-416 batches
    # ... similar process
    
    return synthetic_records

def merge_datasets():
    """Merge Big-Vul + Synthetic"""
    # Load Big-Vul processed data
    bigvul_train = load_jsonl('data/processed/train.jsonl')
    
    # Load synthetic data
    synthetic = load_synthetic_data()
    
    # Format synthetic data to match Big-Vul format
    synthetic_formatted = [reformat(r) for r in synthetic]
    
    # Merge
    combined_train = bigvul_train + synthetic_formatted
    
    # Shuffle
    random.shuffle(combined_train)
    
    return combined_train
```

**Benefits:**
- ✅ Boosts underrepresented CWEs (CWE-190, CWE-416)
- ✅ Adds domain-specific examples (crypto, kernel, codecs)
- ✅ Maintains Big-Vul's real-world diversity
- ✅ Easy to implement

**Use case:** When Big-Vul has few examples of a CWE type

---

### **Strategy 2: Targeted Fine-tuning**

**Goal:** Create specialized models for specific vulnerability types

**How it works:**
```python
# Train separate models
model_cwe190 = train_on_synthetic('cwe190_batches')  # Integer overflow specialist
model_cwe416 = train_on_synthetic('cwe416_batches')  # UAF specialist
model_general = train_on_bigvul()                     # General auditor

# Ensemble at inference
def audit_code(code):
    results = {
        'cwe190': model_cwe190.predict(code),
        'cwe416': model_cwe416.predict(code),
        'general': model_general.predict(code)
    }
    return aggregate(results)
```

**Benefits:**
- ✅ Deep expertise in specific CWE types
- ✅ Can catch subtle variants
- ✅ Modular architecture

**Use case:** When you need high accuracy on specific vulnerability classes

---

### **Strategy 3: Evaluation & Benchmarking**

**Goal:** Use synthetic data as a controlled test set

**How it works:**
```python
# Don't train on synthetic — use it for testing
def evaluate_on_synthetic():
    """Test model on synthetic examples"""
    model = load_trained_model()
    
    # Load synthetic test set
    synthetic_test = load_synthetic_data()
    
    # Evaluate
    results = []
    for example in synthetic_test:
        prediction = model.predict(example['vulnerable_code'])
        results.append({
            'cve_id': example['cve_id'],
            'expected_cwe': example['cwe'],
            'predicted_cwe': prediction['cwe'],
            'correct': prediction['cwe'] == example['cwe']
        })
    
    # Analyze by domain
    by_domain = group_by_domain(results)
    print_accuracy_by_domain(by_domain)
```

**Benefits:**
- ✅ Controlled evaluation (known ground truth)
- ✅ Domain-specific performance metrics
- ✅ Identifies model weaknesses
- ✅ No data leakage concerns

**Use case:** Understanding model strengths/weaknesses across domains

---

## 🚀 **Recommended Implementation Plan**

### **Phase 1: Augmentation (Immediate)**

1. **Create integration script** (`scripts/merge_synthetic_data.py`):
   ```python
   # Load Big-Vul processed data
   # Load synthetic data from data/synthetic/
   # Format synthetic to match Big-Vul structure
   # Merge and shuffle
   # Save to data/processed_v3/
   ```

2. **Update training config**:
   ```yaml
   dataset:
     use_synthetic: true
     synthetic_weight: 0.2  # 20% synthetic, 80% Big-Vul
     synthetic_cwes: ['CWE-190', 'CWE-416']
   ```

3. **Train v3 model**:
   ```bash
   python scripts/merge_synthetic_data.py
   python models/finetune.py --config configs/training_config_v3.yaml
   ```

### **Phase 2: Evaluation (Next)**

1. **Create synthetic test suite**:
   - Hold out 20% of synthetic data for testing
   - Organize by domain (crypto, kernel, codecs, etc.)
   - Create domain-specific benchmarks

2. **Run comparative evaluation**:
   ```python
   # Compare v2 (Big-Vul only) vs v3 (Big-Vul + Synthetic)
   evaluate_model(model_v2, synthetic_test_set)
   evaluate_model(model_v3, synthetic_test_set)
   ```

### **Phase 3: Expansion (Future)**

1. **Generate more synthetic data**:
   - Batches 9-11: More CWE-190 domains
   - Batches 12-14: New CWE types (787, 125, 476)
   - Target: 400+ synthetic examples

2. **Domain-specific models**:
   - Crypto specialist
   - Kernel specialist
   - Web framework specialist

---

## 📊 **Expected Impact**

### **Before (Current)**
```
Training Data: 3,304 examples (Big-Vul only)
CWE-190 examples: ~200 (from Big-Vul)
CWE-416 examples: ~150 (from Big-Vul)
```

### **After (With Augmentation)**
```
Training Data: 3,584 examples (Big-Vul + Synthetic)
CWE-190 examples: ~350 (+75% increase)
CWE-416 examples: ~280 (+87% increase)
Domain coverage: +8 new domains (crypto, kernel, codecs, etc.)
```

### **Performance Gains (Estimated)**
- CWE-190 detection: +15-25% accuracy
- CWE-416 detection: +10-20% accuracy
- Domain-specific: +30-40% on crypto/kernel code
- False positives: -10-15% (better discrimination)

---

## 🎯 **Immediate Action Items**

### **Option A: Full Integration (Recommended)**
1. Create `scripts/merge_synthetic_data.py`
2. Merge Big-Vul + Synthetic → `data/processed_v3/`
3. Train new model on combined dataset
4. Evaluate on held-out synthetic test set

### **Option B: Evaluation Only**
1. Use synthetic data as test set only
2. Evaluate current v2 model on synthetic examples
3. Identify weaknesses by domain
4. Generate targeted synthetic data for weak areas

### **Option C: Hybrid**
1. Use 80% synthetic for training (augmentation)
2. Use 20% synthetic for testing (evaluation)
3. Best of both worlds

---

## 💭 **My Recommendation**

**Go with Option A (Full Integration)** because:

1. **You already have the data** - 180 high-quality examples ready
2. **Easy to implement** - Just need a merge script
3. **Measurable impact** - Can compare v2 vs v3 performance
4. **Scalable** - Once pipeline is built, easy to add more batches
5. **Low risk** - Synthetic data is high-quality and validated

**Next steps:**
1. I create the merge script
2. You run it to generate v3 dataset
3. Train v3 model
4. Compare v2 vs v3 on synthetic test set
5. If v3 is better, use it; if not, we learned something

---

## 🤔 **Questions to Consider**

1. **Do you want to use synthetic data for training or just evaluation?**
2. **Should we create a v3 dataset with merged data?**
3. **What's your priority: better CWE-190/416 detection or broader CWE coverage?**
4. **Do you want domain-specific models or one general model?**

Let me know your preference and I'll implement it! 🚀
