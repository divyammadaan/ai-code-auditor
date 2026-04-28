#!/usr/bin/env python3
"""
Gap analysis against project evaluation criteria
"""

criteria = {
    "i. Dataset Quality": {
        "requirement": "Application-specific dataset, preprocessing, proper data split",
        "status": "✅ DONE",
        "details": [
            "Big-Vul dataset (real CVEs) + synthetic data",
            "80/10/10 train/val/test split",
            "Preprocessing pipeline in data/preprocessing.py",
            "v3 dataset with class balancing",
        ],
        "gaps": ["Test set only has ~4 samples per minority CWE (too few for reliable eval)"]
    },
    "ii. PEFT Fine-tuning": {
        "requirement": "Effective LLM Fine-tuning using PEFT with justification",
        "status": "✅ DONE",
        "details": [
            "QLoRA (4-bit NF4 quantization)",
            "LoRA rank=16, alpha=32",
            "DeepSeek-Coder-6.7B base model",
            "v2 and v3 adapters trained",
        ],
        "gaps": ["Justification doc could be more explicit in README"]
    },
    "iii. Baseline Comparison": {
        "requirement": "Comparison with pre-trained and prompt-engineered models",
        "status": "✅ DONE",
        "details": [
            "Zero-shot baseline evaluated (24% accuracy)",
            "Fine-tuned v2 evaluated (26% accuracy)",
            "Fine-tuned v3 evaluated (17% accuracy)",
        ],
        "gaps": ["No few-shot prompt engineering baseline yet"]
    },
    "iv. Data Storage": {
        "requirement": "Vector DB, regular SQL/NoSQL as applicable",
        "status": "✅ DONE",
        "details": [
            "ChromaDB vector store in data/vectorstore/",
            "RAG retriever in rag/retriever.py",
            "CVE patterns stored and searchable",
        ],
        "gaps": ["Vector store not actively used in evaluation pipeline"]
    },
    "v. Quantitative Metrics": {
        "requirement": "BLEU, ROUGE, and other appropriate metrics",
        "status": "✅ DONE",
        "details": [
            "BLEU-4 computed",
            "ROUGE-L computed",
            "CWE classification accuracy",
            "Per-CWE breakdown",
        ],
        "gaps": ["CodeBLEU not computed", "F1/Precision/Recall not in eval notebook"]
    },
    "vi. Qualitative Analysis": {
        "requirement": "Qualitative and error analysis including hallucination",
        "status": "⚠️  PARTIAL",
        "details": [
            "evaluation/qualitative.py exists with hallucination detection",
            "Error categorization framework built",
        ],
        "gaps": [
            "NOT RUN on actual results yet",
            "No hallucination report generated",
            "No failure case analysis done",
            "NEEDS TO BE EXECUTED on v3 results"
        ]
    },
    "vii. Improvement Demo": {
        "requirement": "Clear improvement demonstration and real-world applicability",
        "status": "⚠️  PARTIAL",
        "details": [
            "v2 vs v3 comparison done",
            "CWE-190 improved 0% -> 50%",
            "CWE-416 improved 0% -> 25%",
        ],
        "gaps": [
            "Overall accuracy DROPPED (26% -> 17%)",
            "Need v4 with better strategy to show clear improvement",
            "Real-world demo needs stronger results"
        ]
    },
    "BONUS: Frontend UI": {
        "requirement": "Frontend UI integration (desired for demo)",
        "status": "❌ NOT DONE",
        "details": [
            "FastAPI backend exists (api/main.py)",
            "API endpoints ready (/audit, /search, /health)",
        ],
        "gaps": [
            "NO frontend UI built",
            "This is a DEMO requirement - important for presentation!",
            "Need a simple web UI to demonstrate the model"
        ]
    }
}

print("="*70)
print("PROJECT GAP ANALYSIS vs EVALUATION CRITERIA")
print("="*70)

for criterion, info in criteria.items():
    print(f"\n{criterion}")
    print(f"  Status: {info['status']}")
    print(f"  Requirement: {info['requirement']}")
    if info['details']:
        print(f"  What we have:")
        for d in info['details']:
            print(f"    ✓ {d}")
    if info['gaps']:
        print(f"  Gaps/Issues:")
        for g in info['gaps']:
            print(f"    ⚠ {g}")

print("\n" + "="*70)
print("PRIORITY ACTION ITEMS")
print("="*70)
print("""
🔴 CRITICAL (Must fix before demo):
   1. Frontend UI - Build simple web interface
   2. Qualitative analysis - Run hallucination/error analysis
   3. Improve overall accuracy (v3 regressed to 17%)

🟡 IMPORTANT (Should fix):
   4. Few-shot baseline comparison
   5. CodeBLEU metric
   6. Better test set (more samples per CWE)

🟢 NICE TO HAVE:
   7. More synthetic data for CWE-119, CWE-399
   8. RAG integration in evaluation
   9. Training justification in README
""")
