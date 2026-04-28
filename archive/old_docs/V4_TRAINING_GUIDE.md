# 🚀 AI Code Auditor v4 Training Guide

## Priority 3: Train v4 Model (Current Task)

### 📋 Quick Start Checklist

**Step 1: Upload v4 Dataset to Kaggle**
1. Go to [Kaggle Datasets](https://www.kaggle.com/datasets)
2. Click "New Dataset" 
3. Upload the entire `data/processed_v4/` folder
4. Title: "AI Code Auditor v4 Dataset"
5. Make it public and save

**Step 2: Create Kaggle Notebook**
1. Go to [Kaggle Notebooks](https://www.kaggle.com/code)
2. Click "New Notebook"
3. Copy-paste content from `notebooks/kaggle_finetune_v4.ipynb`
4. In Settings → Accelerator: **GPU T4 x2** (required)
5. In Data → Add Dataset → Select your v4 dataset

**Step 3: Run Training**
1. Click "Run All" in the notebook
2. Training will take ~2-3 hours
3. Monitor progress in the output logs
4. **Don't close browser** - training will stop if session ends

**Step 4: Download Results**
After training completes, download these 3 files:
- `lora_adapter_v4_download.zip` (LoRA weights)
- `training_log_v4.json` (training metrics)  
- `training_loss_v4.png` (loss curves)

---

## 📊 v4 Dataset Details

**Strategy:** Gentle merge (fixes v3 regression)
- **Base:** Big-Vul v2 (2,137 samples)
- **Synthetic:** +140 samples (90 CWE-190 + 50 CWE-416)
- **Balancing:** NO capping, only oversample tiny classes (<150) to 150 minimum
- **Total:** 2,354 training samples

**Key Differences from v3:**
- ✅ **NO capping** of dominant classes (CWE-119/20/399 stay at 350/350/328)
- ✅ Only boost tiny classes (CWE-190: 145→235, CWE-416: 140→190)
- ✅ Expected: Better overall accuracy + minority class gains

---

## 🎯 Expected Results

Based on v2/v3 analysis, v4 should achieve:
- **Overall CWE Accuracy:** 30-35% (vs v2: 26%, v3: 17%)
- **CWE-190 (Integer Overflow):** 40-60% (vs v2: 0%, v3: 50%)
- **CWE-416 (Use After Free):** 25-50% (vs v2: 0%, v3: 25%)
- **Unknown Predictions:** <40 (vs v2: 31, v3: 52)

---

## 🔧 Training Configuration

```python
# Model & Method
BASE_MODEL = 'deepseek-ai/deepseek-coder-6.7b-base'
METHOD = 'QLoRA (4-bit NF4 quantization)'

# LoRA Settings
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

# Training Settings  
NUM_EPOCHS = 3
BATCH_SIZE = 4
GRAD_ACCUM = 4
LEARNING_RATE = 2e-4
MAX_SEQ_LEN = 512
```

---

## 🚨 Common Issues & Solutions

**Issue: "Dataset not found"**
- Solution: Make sure you added the v4 dataset in Kaggle notebook settings

**Issue: "CUDA out of memory"**
- Solution: Use GPU T4 x2, reduce batch size to 2 if needed

**Issue: Training stuck/slow**
- Solution: Check GPU utilization, restart session if needed

**Issue: Session timeout**
- Solution: Keep browser tab active, don't let computer sleep

---

## 📁 File Locations After Training

Place downloaded files in these locations:
```
models/lora_adapter_v4/           # Extract lora_adapter_v4_download.zip here
├── adapter_config.json
├── adapter_model.safetensors
├── README.md
├── special_tokens_map.json
├── tokenizer.json
└── tokenizer_config.json

notebooks/
├── training_log_v4.json         # Training metrics
└── training_loss_v4.png         # Loss curves
```

---

## 🔄 Next Steps After v4 Training

1. **Evaluate v4 Model** (create evaluation notebook)
2. **Build Frontend UI** (reuse v1 components with FastAPI)
3. **Add Few-shot Baseline** (prompt engineering comparison)
4. **Complete Documentation** (final project report)

---

## 💡 Tips for Success

- **Monitor VRAM:** Should use ~10-12GB during training
- **Check Progress:** Loss should decrease steadily
- **Save Frequently:** Click "Save Version" every hour
- **Backup Downloads:** Keep multiple copies of trained weights

---

Ready to start? Upload the v4 dataset and run the training notebook! 🚀