# AI Code Auditor — Security Vulnerability Detection with PEFT

A Gen AI course project that fine-tunes CodeLlama-7B using QLoRA (Parameter-Efficient Fine-Tuning) to detect security vulnerabilities in C/C++ code and generate secure rewrites.

---

## What We Built

A system where you paste vulnerable C/C++ code and get back:
- Vulnerability type (CWE ID)
- CVE reference and CVSS severity score
- Explanation of what's wrong
- Secure rewrite of the code

**Example input:**
```c
void get_username(char *input) {
    char username[32];
    strcpy(username, input);
    printf("Hello, %s\n", username);
}
```

**Example output:**
```
🟡 CWE-119 detected
CVE: CVE-2021-XXXX | CVSS: 7.5 (HIGH)

What's wrong: strcpy copies into a fixed 32-byte buffer with no
size check — attacker can overflow the buffer.

Secure rewrite:
void get_username(char *input) {
    char username[32];
    strncpy(username, input, sizeof(username) - 1);
    username[sizeof(username) - 1] = '\0';
    printf("Hello, %s\n", username);
}
```

---

## What We Did — Step by Step

### Step 1: Dataset
- Downloaded **Big-Vul** — 188,636 real-world C/C++ functions with CVE-linked vulnerability labels
- Filtered to vulnerable-only functions with secure rewrites: 10,900 rows
- Cleaned: removed duplicates, too-short/too-long functions → 7,306 rows
- **Fixed a critical issue**: original prompts had generic boilerplate completions ("The secure version addresses the vulnerability by applying input validation...") for every single sample — model was learning the template, not the vulnerability patterns
- Rewrote completions to be sample-specific: each includes the actual CVE, CVSS score, real secure code, and a diff of what changed
- Applied token budget filter (max 3,200 chars) to remove samples that would get truncated during training — reduced to **3,162 high-quality samples**
- Stratified 80/10/10 split by CWE category

### Step 2: Vector Store (RAG)
- Built a ChromaDB vector store with 15 CVE/CWE vulnerability patterns
- Used `all-MiniLM-L6-v2` embeddings for semantic search
- Retriever finds similar vulnerability patterns to augment prompts

### Step 3: Fine-tuning
- **Model**: CodeLlama-7B-hf (Meta)
- **Method**: QLoRA — 4-bit NF4 quantization + LoRA adapters
- **LoRA config**: r=16, alpha=32, dropout=0.05, target all attention + MLP layers
- **Trainable parameters**: ~40M out of 6.7B (0.5%)
- **Training**: 2 epochs, 394 steps, batch size 4 × grad_accum 4 = effective batch 16
- **Hardware**: Kaggle Tesla T4 (15.6GB VRAM)
- **Time**: ~3.5 hours
- **Loss**: 1.0 → 0.24 (67% reduction)

### Step 4: Evaluation
Ran inference on 100 test samples comparing zero-shot baseline vs fine-tuned:

| Metric | Baseline (Zero-shot) | Fine-tuned (QLoRA) | Change |
|---|---|---|---|
| BLEU-4 | 1.65 | 2.50 | ↑ 51% |
| ROUGE-L | 0.163 | 0.272 | ↑ 67% |
| CWE Top-1 Accuracy | 0.0% | 22.0% | ↑ from nothing |
| Hallucination Rate | 1.0% | 0.0% | ↓ eliminated |

### Step 5: Demo
- Built a Gradio web interface on Kaggle
- User pastes code → clicks Analyze → gets vulnerability report + secure rewrite
- Public URL shared with faculty for live demo

---

## What Works

- **Output format**: Model correctly learned the structured report format (CWE, CVE, CVSS, secure rewrite section)
- **Secure rewrite direction**: For buffer overflow cases, model correctly identifies that `strcpy` needs to be replaced with a bounded alternative
- **Zero hallucinations**: Fine-tuned model never introduces new dangerous patterns in rewrites (baseline did 1% of the time)
- **CWE improvement**: 0% → 22% accuracy — baseline predicted nothing, fine-tuned gets 1 in 5 correct
- **22 improvement cases**: Out of 100 test samples, 22 cases where fine-tuned got CWE right and baseline didn't

---

## What Doesn't Work (Limitations)

### 1. CWE Misclassification — Mode Collapse on CWE-190
The model predicts **CWE-190 (Integer Overflow)** for almost every input regardless of the actual vulnerability. This is mode collapse — the model learned one dominant output pattern.

**Why it happened:**
- Training completions used the same generic explanation for all CWEs: *"The issue allows an attacker to exploit improper memory or input handling"*
- The model couldn't distinguish between CWE types from this generic text
- CWE-190 may have appeared frequently in training contexts that matched common patterns

**What would fix it:**
- Write CWE-specific explanations in training data (e.g., for CWE-119: "strcpy copies N bytes without checking buffer size", for CWE-416: "pointer is used after free() releases the memory")
- This is the single most impactful fix

### 2. Secure Rewrites Are Often Wrong or Incomplete
For Use After Free (CWE-416), the model replaced the entire function with an unrelated exit check instead of fixing the actual bug.

**Why it happened:**
- CWE-416 had only ~236 training samples — not enough to learn the pattern
- The model defaulted to patterns it saw more frequently
- 2 epochs wasn't enough for rare CWE types to be learned properly

**What would fix it:**
- Oversample rare CWE categories during training (weighted sampling)
- More epochs (3-5) for rare categories
- Larger model (13B or 34B) has more capacity to memorize rare patterns

### 3. Hallucinated Function Names
The model sometimes generates functions that don't exist in standard C (e.g., `strncpy_safe`).

**Why it happened:**
- Training data contained secure rewrites from real CVE patches — some patches used project-specific helper functions
- Model learned these as valid C functions

**What would fix it:**
- Filter training data to only include standard library functions in secure rewrites
- Add a post-processing step that validates generated code compiles

### 4. Low BLEU/ROUGE Scores
BLEU-4 of 2.50 and ROUGE-L of 0.272 are low in absolute terms.

**Why this is expected:**
- BLEU/ROUGE measure exact n-gram overlap with reference text
- A secure rewrite can be semantically correct but use different variable names, spacing, or function order than the reference
- These metrics are not ideal for code generation — CodeBLEU would be better but requires a working C parser

### 5. Only Works on C/C++
The model was trained exclusively on C/C++ functions from Big-Vul.

**What would fix it:**
- Add Python (Bandit dataset), Java (Juliet dataset), JavaScript vulnerability datasets
- Multi-language fine-tuning

---

## How to Improve This Project

In order of impact:

| Improvement | Expected Gain | Effort |
|---|---|---|
| CWE-specific training completions | CWE accuracy 22% → 50%+ | Medium |
| 5 epochs instead of 2 | CWE accuracy +10-15% | 3 more hours GPU |
| Weighted sampling for rare CWEs | Better rare CWE accuracy | Low |
| Larger model (CodeLlama-13B) | All metrics +20-30% | Need A100 GPU |
| More training data (10K+ samples) | Significant improvement | High |
| CodeBLEU evaluation | Better metric for code quality | Low |
| Post-processing: validate generated code compiles | Eliminate hallucinated functions | Medium |
| HuggingFace Spaces deployment | Permanent demo URL | 1 hour |

---

## Architecture

```
Input Code
    │
    ▼
┌─────────────────┐     ┌──────────────────────┐
│  RAG Retrieval  │────▶│  ChromaDB Vector DB   │
│  (CVE patterns) │     │  (15 CWE/CVE patterns)│
└─────────────────┘     └──────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  CodeLlama-7B + LoRA Adapter     │
│  Fine-tuned on Big-Vul dataset   │
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  Structured Output               │
│  CWE ID · CVE · CVSS · Secure ↓  │
└──────────────────────────────────┘
```

---

## Project Structure

```
ai-code-auditor/
├── data/
│   ├── preprocessing.py            # Dataset pipeline (load, clean, format, split)
│   └── processed/                  # train.jsonl, val.jsonl, test.jsonl
├── models/
│   ├── inference.py                # Model inference wrapper + output parser
│   ├── finetune.py                 # Fine-tuning pipeline
│   ├── baseline.py                 # Zero-shot baseline evaluator
│   └── lora_adapter/               # Trained LoRA weights (not in Git — too large)
├── rag/
│   ├── vectorstore.py              # ChromaDB setup and search
│   ├── retriever.py                # Similarity search + prompt augmentation
│   └── cve_loader.py               # CVE/CWE pattern definitions
├── evaluation/
│   ├── metrics.py                  # BLEU, ROUGE, CWE accuracy, hallucination rate
│   ├── qualitative.py              # Error categorization, failure case analysis
│   └── compare.py                  # Baseline vs fine-tuned comparison charts
├── api/
│   ├── main.py                     # FastAPI app (requires GPU to run /audit)
│   └── schemas.py                  # Pydantic request/response models
├── notebooks/
│   ├── 01_data_exploration.py      # Dataset stats and CWE distribution charts
│   ├── 02_baseline_evaluation.py   # Baseline evaluation setup
│   ├── 03_finetuning_experiment.py # Training loss analysis (runs locally)
│   ├── 04_results_analysis.py      # Final comparison charts (runs locally)
│   ├── kaggle_finetune.ipynb       # Training notebook (run on Kaggle T4)
│   ├── kaggle_evaluate.ipynb       # Evaluation notebook (run on Kaggle T4)
│   └── kaggle_demo.ipynb           # Gradio demo notebook (run on Kaggle T4)
├── configs/
│   ├── lora_config.yaml            # LoRA hyperparameters
│   └── training_config.yaml        # Dataset and training settings
├── scripts/
│   ├── download_dataset.py         # Download Big-Vul from Google Drive
│   ├── build_vectorstore.py        # Build ChromaDB vector store
│   └── run_evaluation.py           # Full evaluation pipeline
├── results/                        # All generated charts and metrics
│   ├── final_comparison.png
│   ├── training_loss_curve.png
│   ├── per_cwe_accuracy.png
│   ├── evaluation_metrics.json
│   └── qualitative_report.json
└── tests/                          # Unit tests
```

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Download and preprocess dataset
```bash
python scripts/download_dataset.py
python data/preprocessing.py
```

### 3. Build vector store
```bash
python scripts/build_vectorstore.py
```

### 4. Run analysis notebooks locally (no GPU needed)
```bash
python notebooks/01_data_exploration.py   # dataset charts
python notebooks/03_finetuning_experiment.py  # training loss curves
python notebooks/04_results_analysis.py  # comparison charts
```

### 5. Fine-tune on Kaggle (GPU required)
- Upload `notebooks/kaggle_finetune.ipynb` to Kaggle
- Add `bigvul-processed` dataset (train/val/test JSONL files)
- Set GPU to T4 x1, enable Internet
- Run all cells (~3.5 hours)
- Download `lora_adapter_download.zip` from Output tab

### 6. Evaluate on Kaggle
- Upload `notebooks/kaggle_evaluate.ipynb`
- Add `bigvul-processed` + `lora-adapter` datasets
- Run all cells (~1 hour)
- Download `evaluation_metrics.json`, `comparison_chart.png`, `qualitative_report.json`

### 7. Run live demo on Kaggle
- Upload `notebooks/kaggle_demo.ipynb`
- Add `lora-adapter` dataset
- Set GPU to T4 x1
- Run all cells → get public Gradio URL (valid 1 week)

---

## Results Summary

```
Training:
  Loss reduction    : 1.0 → 0.24  (67%)
  Epochs            : 2
  Steps             : 394
  Time              : 3.5 hours (T4 GPU)

Evaluation (100 test samples):
  BLEU-4            : 1.65 → 2.50  (↑ 51%)
  ROUGE-L           : 0.163 → 0.272 (↑ 67%)
  CWE Accuracy      : 0% → 22%     (↑ from nothing)
  Hallucination Rate: 1% → 0%      (eliminated)
  Improvement cases : 22 / 100
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Base model | CodeLlama-7B (Meta) |
| Fine-tuning | PEFT / QLoRA (HuggingFace + TRL) |
| Vector DB | ChromaDB + sentence-transformers |
| Evaluation | sacrebleu, rouge-score |
| API | FastAPI |
| Demo UI | Gradio |
| Training platform | Kaggle (T4 GPU) |
| Dataset | Big-Vul (MSR 2020) |

---

## Important Notes

- `models/lora_adapter/adapter_model.safetensors` (~1GB) is not in Git — download from Kaggle output
- `data/raw/` (10GB CSV) is not in Git — re-download with `scripts/download_dataset.py`
- The `/audit` API endpoint requires a GPU — won't work locally on CPU
- Gradio demo link expires after 1 week — re-run `kaggle_demo.ipynb` to get a new one
- For a permanent demo URL, deploy to HuggingFace Spaces using `gradio deploy`
