# AI Code Auditor - Complete Project Documentation

## 📋 Project Overview

**Objective:** Fine-tune LLMs for automated security vulnerability detection and secure code rewriting using PEFT techniques.

**Dataset:** Big-Vul (real CVEs) + synthetic vulnerability data  
**Model:** DeepSeek-Coder-6.7B with QLoRA fine-tuning  
**Approach:** Progressive dataset improvement across multiple versions  

---

## 🗂️ Version History & Evolution

### Version 1 (Baseline)
- **Dataset:** Raw Big-Vul dataset
- **Status:** Initial exploration
- **Results:** Not formally evaluated

### Version 2 (Production Baseline)
- **Dataset:** Big-Vul processed, top-10 CWEs, 2,137 training samples
- **Training:** 399 steps, 3 epochs, ~12 hours
- **Results:** 26% CWE accuracy, 24% zero-shot baseline
- **Issues:** Poor performance on minority classes (CWE-190: 0%, CWE-416: 0%)

### Version 3 (Synthetic Data + Aggressive Balancing)
- **Dataset:** v2 + 140 synthetic samples + aggressive class balancing
- **Strategy:** Capped dominant classes (350→300), oversampled minorities
- **Training:** 441 steps, 3 epochs, ~4 hours
- **Results:** 17% CWE accuracy (REGRESSION from v2)
- **Issues:** Too many unknown predictions (52 vs 31), lost accuracy on dominant classes

### Version 4 (Simple Merge Strategy) - **RECOMMENDED**
- **Dataset:** v2 + 140 synthetic samples + minimal oversampling only
- **Strategy:** NO capping, only boost tiny classes (<150) to 150 minimum
- **Training:** Ready to train
- **Expected:** 30-35% accuracy (best of both worlds)

---

## 📊 Detailed Version Comparison

| Metric | v2 (Baseline) | v3 (Aggressive) | v4 (Gentle) |
|--------|---------------|-----------------|-------------|
| **Training Samples** | 2,137 | 2,363 | 2,354 |
| **Synthetic Data** | 0 | 140 | 140 |
| **CWE-190 Samples** | 145 | 295 | 235 |
| **CWE-416 Samples** | 140 | 200 | 190 |
| **CWE-119 Samples** | 350 | 300 (capped) | 350 (kept) |
| **Imbalance Ratio** | 3.2x | 1.5x | 2.3x |
| **CWE Accuracy** | 26% | 17% ❌ | ~32% (est) |
| **CWE-190 Accuracy** | 0% | 50% ✅ | ~40% (est) |
| **CWE-416 Accuracy** | 0% | 25% ✅ | ~25% (est) |
| **Unknown Predictions** | 31 | 52 ❌ | ~25 (est) |

---

## 🔬 Technical Implementation Details

### Model Architecture
- **Base Model:** DeepSeek-Coder-6.7B (code-specialized)
- **Fine-tuning:** QLoRA (4-bit NF4 quantization)
- **LoRA Config:** r=16, alpha=32, dropout=0.05
- **Target Modules:** q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj

### Training Configuration
```yaml
Epochs: 3
Batch Size: 4 (effective 16 with gradient accumulation)
Learning Rate: 2e-4 (cosine schedule)
Max Sequence Length: 512
Optimizer: paged_adamw_32bit
Quantization: 4-bit NF4 with double quantization
```

### Dataset Processing
```python
# Prompt format
user_msg = f"""Analyze the following C/C++ code and identify the security vulnerability.

```c
{vulnerable_code}
```

Respond with the CWE type first, then explain and provide a secure rewrite."""

assistant_msg = f"""CWE: {cwe_id}
CVE: {cve_id}
Severity: {cvss_score} (HIGH)

Reason: {explanation}

Fix:
```c
{secure_code}
```"""
```

---

## 📈 Evaluation Results

### Quantitative Metrics (v2 vs v3)

| Metric | v2 | v3 | Change |
|--------|----|----|--------|
| **BLEU-4** | 5.69 | 5.82 | +0.13 |
| **ROUGE-L** | 0.270 | 0.267 | -0.003 |
| **CWE Accuracy** | 26% | 17% | -9% ❌ |
| **Unknown Predictions** | 31 | 52 | +21 ❌ |

### Per-CWE Performance Analysis

**v2 Results:**
- CWE-125: 60% (6/10) - Best performing
- CWE-264: 60% (3/5) - Good on small sample
- CWE-399: 43% (6/14) - Decent
- CWE-20: 28% (7/25) - Moderate
- CWE-119: 7% (2/27) - Poor
- CWE-190: 0% (0/4) - Failed completely
- CWE-416: 0% (0/4) - Failed completely

**v3 Results:**
- CWE-190: 50% (2/4) - ✅ Major improvement
- CWE-20: 40% (10/25) - ✅ Improved
- CWE-264: 40% (2/5) - Maintained
- CWE-416: 25% (1/4) - ✅ Improved from 0%
- CWE-399: 14% (2/14) - ❌ Regressed
- CWE-119: 0% (0/27) - ❌ Regressed badly
- CWE-125: 0% (0/10) - ❌ Regressed badly

### Qualitative Analysis

**Hallucination Rate:** 3% (consistent across v2 and v3)
- Types: buffer_overflow, null_deref, use_after_free
- Low rate indicates model generates mostly safe rewrites

**Error Patterns:**
- **v2:** 49% wrong CWE, 27% unknown predictions
- **v3:** 31% wrong CWE, 52% unknown predictions
- **Issue:** v3 became more conservative (more unknowns, fewer guesses)

**Top Confusion Patterns:**
- CWE-119 → Unknown (most common failure)
- CWE-119 → CWE-190 (integer overflow confusion)
- CWE-20 → Unknown (input validation issues)

---

## 🧬 Synthetic Data Strategy

### Data Generation Approach
Generated domain-specific synthetic vulnerabilities to address class imbalance:

**CWE-190 (Integer Overflow) - 90 samples:**
- Batch 1: Image processing (PNG, JPEG, BMP) - 10 samples
- Batch 2: Network protocols (TCP, UDP, HTTP) - 20 samples  
- Batch 3: Memory allocators (malloc, calloc) - 20 samples
- Batch 4: Archive formats (ZIP, TAR, RAR) - 20 samples
- Batch 5: Cryptographic operations (RSA, AES) - 20 samples

**CWE-416 (Use After Free) - 50 samples:**
- Batch 1: Network connections - 20 samples
- Batch 4: Memory allocators - 20 samples
- Batch 9: Bonus mixed scenarios - 10 samples

### Quality Assessment
- **Structure:** All samples follow vulnerable_code → secure_code → explanation format
- **Domains:** Cover real-world scenarios (crypto, networking, file processing)
- **Effectiveness:** CWE-190 improved 0%→50%, CWE-416 improved 0%→25%

---

## 🏗️ Infrastructure & Architecture

### Data Storage
- **Vector Database:** ChromaDB for CVE pattern storage and RAG retrieval
- **Dataset Storage:** JSONL format for training data
- **Model Storage:** HuggingFace format with LoRA adapters

### API Backend (FastAPI)
```python
# Endpoints
POST /audit          # Audit code snippet
POST /search         # Search vulnerability patterns  
GET  /patterns       # List stored patterns
GET  /health         # Health check
```

### RAG Integration
- **Vector Store:** 1,000+ CVE patterns embedded
- **Retrieval:** Top-3 similar patterns for context augmentation
- **Usage:** Available but not actively used in current evaluation

---

## 📋 Evaluation Criteria Compliance

### ✅ Completed Requirements

**i. Dataset Quality**
- ✅ Application-specific: Big-Vul (real CVEs) + synthetic vulnerabilities
- ✅ Preprocessing: Structured prompt formatting, proper tokenization
- ✅ Data split: 80/10/10 train/val/test stratified by CWE

**ii. PEFT Fine-tuning**
- ✅ QLoRA implementation with 4-bit quantization
- ✅ LoRA rank=16, justified for parameter efficiency vs performance
- ✅ Multiple versions trained and compared

**iii. Baseline Comparison**
- ✅ Zero-shot baseline: 24% accuracy
- ✅ Fine-tuned v2: 26% accuracy  
- ✅ Fine-tuned v3: 17% accuracy

**iv. Data Storage**
- ✅ ChromaDB vector database for CVE patterns
- ✅ JSONL files for structured training data
- ✅ RAG retrieval system implemented

**v. Quantitative Metrics**
- ✅ BLEU-4, ROUGE-L for code rewrite quality
- ✅ CWE classification accuracy with per-class breakdown
- ✅ Comprehensive evaluation framework

**vi. Qualitative Analysis**
- ✅ Hallucination detection (3% rate)
- ✅ Error categorization and failure case analysis
- ✅ Confusion matrix analysis for CWE misclassification

### ⚠️ Partial Requirements

**vii. Improvement Demonstration**
- ⚠️ v3 shows mixed results: CWE-190/416 improved but overall accuracy dropped
- ✅ v4 strategy designed to address issues
- ⚠️ Need v4 training results to demonstrate clear improvement

### ❌ Missing Requirements

**Frontend UI (Desired)**
- ❌ No web interface built yet
- ✅ FastAPI backend ready for frontend integration
- 🎯 Priority for demo presentation

---

## 🚀 Next Steps & Recommendations

### Immediate Actions (This Week)

1. **Train v4 Model** (Priority 1)
   - Use gentle merge strategy (no capping)
   - Expected: 30-35% accuracy
   - Timeline: 3-4 hours training

2. **Build Frontend UI** (Priority 2)  
   - Simple web interface for code auditing
   - Connect to existing FastAPI backend
   - Timeline: 2-3 hours (reuse v1 components)

3. **Few-shot Baseline** (Priority 3)
   - Add prompt engineering comparison
   - Timeline: 1 hour

### Future Improvements

4. **Generate More Synthetic Data**
   - CWE-119: Buffer overflow variants (100 samples)
   - CWE-399: Resource management issues (50 samples)
   - Target: 40-45% overall accuracy

5. **Advanced Techniques**
   - Focal loss for hard examples
   - Class-weighted training
   - Ensemble methods

---

## 📁 File Structure & Locations

```
ai-code-auditor/
├── data/
│   ├── processed_v2/           # v2 dataset (2,137 samples)
│   ├── processed_v3/           # v3 dataset (2,363 samples, balanced)
│   ├── processed_v4/           # v4 dataset (2,354 samples, gentle)
│   └── synthetic/              # Synthetic vulnerability data
├── models/
│   ├── lora_adapter_v2/        # v2 trained model
│   ├── lora_adapter_v3/        # v3 trained model
│   └── lora_adapter_v4/        # v4 model (to be trained)
├── results/
│   ├── evaluation_metrics_v2.json
│   ├── evaluation_metrics_v3.json
│   ├── finetuned_results_v2.jsonl
│   ├── finetuned_results_v3.jsonl
│   └── qualitative_report_v2_v3.json
├── notebooks/
│   ├── kaggle_finetune_v2.ipynb    # v2 training notebook
│   ├── kaggle_finetune_v3.ipynb    # v3 training notebook
│   ├── kaggle_evaluate_v2.ipynb    # v2 evaluation
│   └── kaggle_evaluate_v3.ipynb    # v3 evaluation
├── api/                        # FastAPI backend
├── rag/                        # Vector database & retrieval
├── evaluation/                 # Metrics & analysis tools
└── scripts/                    # Dataset creation & analysis
```

---

## 🎯 Success Metrics & Goals

### Current Status
- ✅ 5/7 evaluation criteria completed
- ✅ Working model with 26% baseline accuracy
- ✅ Synthetic data strategy validated (CWE-190/416 improvements)
- ⚠️ Need to fix overall accuracy regression

### Target Goals
- 🎯 **v4 Accuracy:** 30-35% overall CWE classification
- 🎯 **Minority Classes:** CWE-190 >40%, CWE-416 >25%
- 🎯 **Demo Ready:** Frontend UI + comprehensive evaluation
- 🎯 **Documentation:** Complete project documentation ✅

### Demo Readiness Checklist
- ✅ Trained models (v2, v3)
- ⏳ v4 model training
- ❌ Frontend UI
- ✅ API backend
- ✅ Evaluation results
- ✅ Qualitative analysis
- ✅ Complete documentation

---

## 📞 Quick Reference Commands

```bash
# Create v4 dataset
python scripts/create_v4_dataset.py

# Train v4 model (Kaggle)
# Upload data/processed_v4/ to Kaggle
# Run kaggle_finetune_v3.ipynb with v4 dataset

# Run qualitative analysis
python scripts/run_qualitative_analysis.py

# Compare all versions
python scripts/compare_v2_v3.py

# Start API server
cd api && uvicorn main:app --reload

# Run evaluation
python notebooks/02_baseline_evaluation.py
```

---

**Status:** Ready for v4 training and frontend development  
**Timeline:** Complete by Wednesday EOD  
**Next Action:** Train v4 model on Kaggle  
