# AI Code Auditor — Automated Security Vulnerability Detection using Fine-tuned LLMs

A Gen AI project that fine-tunes **DeepSeek-Coder-6.7B** using QLoRA (Parameter-Efficient Fine-Tuning) to detect security vulnerabilities in C/C++ code and generate secure rewrites.

---

## What It Does

Paste vulnerable C/C++ code and get back:
- Vulnerability type (CWE ID)
- Natural-language explanation of the flaw
- Secure rewrite of the code

**Example input:**
```c
void process_image(unsigned char *data, int width, int height) {
    int size = width * height * 4;  // RGBA
    unsigned char *buffer = malloc(size);
    if (!buffer) return;
    memcpy(buffer, data, size);
    free(buffer);
}
```

**Example output:**
```
CWE: CWE-190
EXPLANATION: The multiplication width * height * 4 can overflow a signed 32-bit
integer if width and height are large values, resulting in a negative or
truncated size passed to malloc. The subsequent memcpy will then write beyond
the allocated buffer boundary.

SECURE_CODE:
void process_image(unsigned char *data, int width, int height) {
    if (width <= 0 || height <= 0) return;
    if ((size_t)width > SIZE_MAX / 4 / (size_t)height) return;
    size_t size = (size_t)width * (size_t)height * 4;
    unsigned char *buffer = malloc(size);
    if (!buffer) return;
    memcpy(buffer, data, size);
    free(buffer);
}
```

---

## Results Summary

The project went through four iterative model versions. Here's the final picture:

| Version | Base Model | Dataset | CWE Accuracy | BLEU-4 | Key Change |
|---------|-----------|---------|-------------|--------|-----------|
| v1 | CodeLlama-7B | 4,624 samples, 39 classes | — | — | Initial experiment — abandoned (too many classes) |
| v2 | DeepSeek-Coder-6.7B | 2,137 samples | 26% | 5.69 | Switched model, narrowed to top-10 CWEs |
| v3 | DeepSeek-Coder-6.7B | 2,363 samples | 17% | 5.82 | Added synthetic data + aggressive class capping — caused regression |
| **v4 (final)** | **DeepSeek-Coder-6.7B** | **2,384 samples** | **26%** | **12.01** | **Gentle merge, no capping — best overall** |

```
v4 Training:
  Loss reduction    : 1.19 → 0.23  (81%)
  Epochs            : 3
  Steps             : 447
  Time              : ~5 hours (2× T4 GPU)

v4 Evaluation (100 test samples):
  BLEU-4            : 5.69 → 12.01  (↑ 111%)
  ROUGE-L           : 0.270 → 0.299 (↑ 11%)
  CodeBLEU          : 37.82
  CWE Accuracy      : 26% (26/100)
  Unknown Preds     : 26/100 (lowest across all versions)
  Hallucination Rate: 3% (stable across all versions)
```

**Minority class improvement from synthetic data:**

| CWE | v2 Fine-tuned | v4 Final |
|-----|--------------|---------|
| CWE-190 (Integer Overflow) | 0% | 35% |
| CWE-416 (Use After Free) | 0% | 20% |

---

## Architecture

```
Input Code
    │
    ▼
┌─────────────────┐     ┌──────────────────────────┐
│  RAG Retrieval  │────▶│  ChromaDB Vector Store    │
│  (CVE patterns) │     │  (all-MiniLM-L6-v2 embeds)│
└─────────────────┘     └──────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  DeepSeek-Coder-6.7B + LoRA Adapter  │
│  Fine-tuned on Big-Vul dataset (v4)  │
│  QLoRA: 4-bit NF4, rank-16, ~20M     │
│  trainable params out of 6.7B        │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Structured Output                   │
│  CWE ID · Explanation · Secure Code  │
└──────────────────────────────────────┘
```

---

## Project Structure

```
ai-code-auditor/
├── data/
│   ├── preprocessing.py            # Dataset pipeline (load, clean, format, split)
│   ├── processed/                  # v1 train/val/test JSONL
│   ├── processed_v2/               # v2 train/val/test JSONL
│   ├── processed_v3/               # v3 train/val/test JSONL
│   ├── processed_v4/               # v4 train/val/test JSONL (final)
│   └── synthetic/                  # Synthetic CWE-190 and CWE-416 samples
├── models/
│   ├── inference.py                # Model inference wrapper + output parser
│   ├── finetune.py                 # Fine-tuning pipeline
│   ├── baseline.py                 # Zero-shot baseline evaluator
│   ├── lora_adapter/               # v1 LoRA config + tokenizer (weights not in Git)
│   ├── lora_adapter_v2/            # v2 LoRA config + tokenizer (weights not in Git)
│   ├── lora_adapter_v3/            # v3 LoRA config + tokenizer (weights not in Git)
│   └── lora_adapter_v4/            # v4 LoRA config + tokenizer (weights not in Git)
├── rag/
│   ├── vectorstore.py              # ChromaDB setup and search
│   ├── retriever.py                # Similarity search + prompt augmentation
│   └── cve_loader.py               # CVE/CWE pattern definitions
├── evaluation/
│   ├── metrics.py                  # BLEU-4, ROUGE-L, CodeBLEU, CWE accuracy
│   ├── qualitative.py              # Error categorisation, failure case analysis
│   └── compare.py                  # Cross-version comparison charts
├── api/
│   ├── main.py                     # FastAPI app (POST /audit, /search, GET /patterns, /health)
│   └── schemas.py                  # Pydantic request/response models
├── notebooks/
│   ├── kaggle_finetune_v2.ipynb    # v2 training notebook (Kaggle T4)
│   ├── kaggle_finetune_v4.ipynb    # v4 training notebook (Kaggle T4) ← final
│   ├── kaggle_evaluate_v2.ipynb    # v2 evaluation notebook
│   ├── kaggle_evaluate_v4.ipynb    # v4 evaluation notebook ← final
│   ├── kaggle_demo_v2.ipynb        # v2 Gradio demo
│   ├── kaggle_demo_v4.ipynb        # v4 Gradio demo ← final
│   └── training_log_v4.json        # v4 training loss log
├── configs/
│   ├── lora_config.yaml            # LoRA hyperparameters
│   ├── training_config.yaml        # v4 training settings
│   └── training_config_v3.yaml     # v3 training settings
├── scripts/
│   ├── build_vectorstore.py        # Build ChromaDB vector store
│   ├── create_v4_dataset.py        # Build v4 dataset with synthetic data
│   ├── prepare_v2_dataset.py       # Build v2 dataset
│   ├── analyze_v4_results.py       # v4 results analysis
│   ├── compute_codebleu.py         # CodeBLEU computation
│   └── run_qualitative_analysis.py # Qualitative error analysis
├── results/                        # All generated charts and metrics (all versions)
│   ├── evaluation_metrics_v4.json  # v4 final metrics
│   ├── finetuned_results_v4.jsonl  # v4 inference outputs
│   ├── v2_v3_v4_comparison.png     # Cross-version comparison chart
│   └── ...
├── tests/                          # Unit tests
├── frontend/index.html             # Single-page demo UI
├── requirements.txt
├── setup.py
└── start_api.py                    # Launch FastAPI server
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Base model | DeepSeek-Coder-6.7B (`deepseek-ai/deepseek-coder-6.7b-base`) |
| Fine-tuning | PEFT / QLoRA (Hugging Face PEFT + TRL) |
| Quantisation | bitsandbytes — 4-bit NF4, double quantisation |
| Vector DB | ChromaDB + sentence-transformers (`all-MiniLM-L6-v2`) |
| Evaluation | sacrebleu, rouge-score, codebleu, scikit-learn |
| API | FastAPI + uvicorn |
| Demo UI | Gradio (Kaggle) / vanilla HTML frontend |
| Training platform | Kaggle (2× NVIDIA T4, 16 GB VRAM each) |
| Dataset | Big-Vul (Fan et al., MSR 2020) + synthetic data |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Build the vector store
```bash
python scripts/build_vectorstore.py
```

### 3. Run the API (requires GPU)
```bash
python start_api.py
```
The API will be available at `http://localhost:8000`. See `/docs` for the OpenAPI spec.

### 4. Fine-tune on Kaggle (GPU required)
- Upload `notebooks/kaggle_finetune_v4.ipynb` to Kaggle
- Add the processed v4 dataset (JSONL files from `data/processed_v4/`)
- Set accelerator to GPU T4 x2, enable Internet
- Run all cells (~5 hours)
- Download the `lora_adapter` output folder

### 5. Evaluate on Kaggle
- Upload `notebooks/kaggle_evaluate_v4.ipynb`
- Add the processed dataset + downloaded LoRA adapter
- Run all cells (~1 hour)

### 6. Run the Gradio demo on Kaggle
- Upload `notebooks/kaggle_demo_v4.ipynb`
- Add the LoRA adapter dataset
- Run all cells → get a public Gradio URL (valid 72 hours)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/audit` | Primary vulnerability analysis — runs LLM + RAG |
| POST | `/search` | Semantic similarity search against the vector store |
| GET | `/patterns` | List all indexed vulnerability patterns |
| GET | `/health` | System health check |

**Example request:**
```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"code": "void foo(char *src) { char buf[32]; strcpy(buf, src); }"}'
```

---

## Model Weights

The LoRA adapter weights (`adapter_model.safetensors`, ~153 MB per version) are not stored in this repository — they exceed GitHub's file size limit. Download them from the Kaggle output of the corresponding training notebook, or retrain using the notebooks provided.

The adapter configs and tokenizer files for all versions are included in `models/lora_adapter_v*/`.

---

## Known Limitations

- **26% CWE accuracy** — the dominant failure mode is Unknown predictions (model abstains rather than guessing wrong), which is a reasonable safety property but limits utility
- **512-token context window** — longer functions get truncated; extending to 1024+ tokens is the most impactful next step
- **C/C++ only** — trained exclusively on Big-Vul; no Python, Java, or JavaScript support
- **GPU required for inference** — the `/audit` endpoint will not run on CPU in reasonable time
- **Gradio demo link expires** — re-run `kaggle_demo_v4.ipynb` to get a fresh URL; for a permanent deployment use `gradio deploy` to HuggingFace Spaces

---

## Dataset

The project uses [Big-Vul](https://github.com/ZeoVan/MSR_20_Code_vulnerability_dataset_package) (Fan et al., MSR 2020) — 188,636 real-world C/C++ functions with CVE-linked vulnerability labels. The top-10 most frequent CWE classes were used, supplemented with synthetic samples for two minority classes (CWE-190 and CWE-416).

`data/raw/` is not included in this repository (10 GB CSV). The preprocessed JSONL splits for all four dataset versions are included in `data/processed_v*/`.

---

## Project Report

See [`PROJECT_REPORT.md`](PROJECT_REPORT.md) for the full academic report covering methodology, literature review, all four model versions, detailed results tables, and conclusions.
