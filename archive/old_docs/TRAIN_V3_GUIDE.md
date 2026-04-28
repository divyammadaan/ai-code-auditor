# 🚀 v3 Model Training Guide

## ✅ Status: Ready to Train!

The v3 dataset has been successfully created with synthetic data and class balancing applied.

---

## 📊 What We Accomplished

### Dataset Creation
- ✅ Merged Big-Vul (v2) with synthetic data
- ✅ Added 90 CWE-190 synthetic samples (5 batches)
- ✅ Added 50 CWE-416 synthetic samples (usable from 9 batches)
- ✅ Applied class balancing (oversampling + capping)
- ✅ Improved imbalance ratio: **3.2x → 1.5x**

### Final v3 Dataset
```
data/processed_v3/
├── train.jsonl    # 2,363 samples (balanced)
├── val.jsonl      # 583 samples (from v2)
└── test.jsonl     # 584 samples (from v2)
```

### Class Distribution
```
CWE-399: 300 samples (12.7%) ████████████████████
CWE-119: 300 samples (12.7%) ████████████████████
CWE-20:  300 samples (12.7%) ████████████████████
CWE-190: 235 samples ( 9.9%) ███████████████     ← +90 synthetic
CWE-264: 228 samples ( 9.6%) ███████████████
CWE-362: 200 samples ( 8.5%) █████████████       ← oversampled
CWE-189: 200 samples ( 8.5%) █████████████       ← oversampled
CWE-125: 200 samples ( 8.5%) █████████████       ← oversampled
CWE-416: 200 samples ( 8.5%) █████████████       ← +50 synthetic + oversampled
CWE-200: 200 samples ( 8.5%) █████████████       ← oversampled
```

---

## 🎯 Training v3 Model

### Step 1: Verify Dataset
```bash
# Quick verification
python verify_v3.py

# Expected output:
# ✓ train.jsonl: 2363 samples
# ✓ val.jsonl: 583 samples
# ✓ test.jsonl: 584 samples
```

### Step 2: Train the Model

**Option A: Using Kaggle Notebook (Recommended)**
```bash
# Upload the v3 dataset to Kaggle
# Use notebooks/kaggle_finetune_v2.ipynb as template
# Update dataset path to: data/processed_v3/

# Expected training time: 2-3 hours on Kaggle GPU
```

**Option B: Local Training (if you have GPU)**
```bash
# Train with v3 config
python models/finetune.py --config configs/training_config_v3.yaml

# Monitor training
# - Watch for loss convergence
# - Check validation metrics
# - Save checkpoints regularly
```

### Step 3: Evaluate Performance
```bash
# Run baseline evaluation on v3
python notebooks/02_baseline_evaluation.py --model v3

# This will create:
# - results/evaluation_metrics_v3.json
# - results/finetuned_results_v3.jsonl
# - results/per_cwe_accuracy_v3.png
```

### Step 4: Compare v2 vs v3
```bash
# Compare models
python scripts/compare_v2_v3.py

# This will show:
# - Overall metrics comparison
# - Per-CWE accuracy improvements
# - Visualization charts
```

---

## 📈 Expected Results

Based on the class balancing and synthetic data:

| Metric | v2 Baseline | v3 Target | Expected Gain |
|--------|-------------|-----------|---------------|
| **Overall Accuracy** | ~72% | 78-82% | +6-10% ⬆️ |
| **CWE-190 Accuracy** | ~65% | 78-83% | +13-18% ⬆️ |
| **CWE-416 Accuracy** | ~70% | 80-85% | +10-15% ⬆️ |
| **CWE-189 Accuracy** | ~55% | 68-73% | +13-18% ⬆️ |
| **CWE-362 Accuracy** | ~60% | 72-77% | +12-17% ⬆️ |
| **CWE-125 Accuracy** | ~68% | 75-80% | +7-12% ⬆️ |

### Why These Gains?

1. **Synthetic Data Benefits:**
   - Domain-specific patterns (crypto, network, allocators, archives)
   - Clean, well-labeled vulnerability-fix pairs
   - Explicit CWE-190/416 examples

2. **Oversampling Benefits:**
   - More exposure to minority class patterns
   - Reduced model bias toward dominant classes
   - Better generalization on underrepresented CWEs

3. **Capping Benefits:**
   - Prevents overfitting to CWE-20/119
   - Forces model to learn from diverse examples
   - Improves overall balance

---

## 🔍 Monitoring Training

### Key Metrics to Watch

1. **Training Loss**
   - Should decrease steadily
   - Target: < 0.5 by end of training

2. **Validation Loss**
   - Should track training loss
   - Watch for overfitting (val loss increases while train loss decreases)

3. **Per-CWE Accuracy**
   - Monitor minority classes (CWE-190, CWE-416, CWE-189, CWE-362)
   - Should see improvements over v2

4. **Overall Accuracy**
   - Target: 78-82% on test set
   - Compare with v2 baseline (~72%)

---

## 📁 Files Created

### Dataset Files
- ✅ `data/processed_v3/train.jsonl` - Training data (2,363 samples)
- ✅ `data/processed_v3/val.jsonl` - Validation data (583 samples)
- ✅ `data/processed_v3/test.jsonl` - Test data (584 samples)

### Configuration Files
- ✅ `configs/training_config_v3.yaml` - Training configuration for v3
- ✅ `scripts/create_v3_dataset.py` - Dataset creation script
- ✅ `scripts/compare_v2_v3.py` - Model comparison script
- ✅ `verify_v3.py` - Dataset verification script

### Documentation Files
- ✅ `V3_DATASET_SUMMARY.md` - Detailed dataset statistics
- ✅ `TRAIN_V3_GUIDE.md` - This guide

---

## 🚨 Troubleshooting

### Issue: Training loss not decreasing
**Solution:** 
- Check learning rate (try 2e-4 or 5e-5)
- Verify data format is correct
- Ensure GPU is being used

### Issue: Validation loss increasing (overfitting)
**Solution:**
- Reduce number of epochs
- Increase dropout rate
- Add more regularization

### Issue: Poor performance on minority classes
**Solution:**
- Check if synthetic data is being loaded correctly
- Verify class balancing worked (run verify_v3.py)
- Consider adding more synthetic data

### Issue: Out of memory during training
**Solution:**
- Reduce batch size
- Use gradient accumulation
- Enable gradient checkpointing

---

## 🎯 Success Criteria

Your v3 model is successful if:

1. ✅ **Overall accuracy improves by 5-10%** over v2
2. ✅ **CWE-190 accuracy improves by 10-15%** (target: 78-83%)
3. ✅ **CWE-416 accuracy improves by 10-15%** (target: 80-85%)
4. ✅ **Minority class accuracy improves** (CWE-189, CWE-362, CWE-125)
5. ✅ **No major regressions** on dominant classes (CWE-20, CWE-119)

---

## 🔄 Next Steps After Training

### If v3 Shows Good Results:
1. **Generate More Synthetic Data**
   - Use prompts in `SYNTHETIC_DATA_GENERATION_PROMPTS.md`
   - Add batches 6-8 for CWE-190 (60 more samples)
   - Add batches for CWE-189, CWE-362 (120 more samples)

2. **Create v4 Dataset**
   - Merge v3 + new synthetic data
   - Further improve class balance
   - Target: 2,500-2,600 samples

3. **Advanced Techniques**
   - Add focal loss for hard examples
   - Implement class weights
   - Try ensemble methods

### If v3 Shows Poor Results:
1. **Analyze Failure Modes**
   - Which CWEs are still struggling?
   - Is synthetic data too different from real data?
   - Are there data quality issues?

2. **Adjust Strategy**
   - Reduce synthetic data ratio
   - Improve synthetic data quality
   - Try different balancing ratios

3. **Iterate**
   - Create v3.1 with adjustments
   - Test on smaller subset first
   - Validate before full training

---

## 📞 Quick Reference

### Verify Dataset
```bash
python verify_v3.py
```

### Train Model
```bash
python models/finetune.py --config configs/training_config_v3.yaml
```

### Evaluate Model
```bash
python notebooks/02_baseline_evaluation.py --model v3
```

### Compare Models
```bash
python scripts/compare_v2_v3.py
```

### Check Dataset Stats
```bash
python -c "import json; train = [json.loads(l) for l in open('data/processed_v3/train.jsonl')]; print(f'Total: {len(train)} samples'); from collections import Counter; dist = Counter(r['cwe'] for r in train); [print(f'{cwe}: {count}') for cwe, count in sorted(dist.items(), key=lambda x: -x[1])]"
```

---

## ✅ Ready to Go!

Your v3 dataset is ready for training. The class balance has been significantly improved, and synthetic data has been added to boost minority classes.

**Start training now and let's see those accuracy improvements!** 🚀

Good luck! 🎯

