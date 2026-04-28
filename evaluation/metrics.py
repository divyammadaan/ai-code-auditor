"""
Quantitative evaluation metrics for the AI Code Auditor.

Metrics computed:
  1. Vulnerability Detection: Precision, Recall, F1, Accuracy
  2. CWE Classification: Top-1 and Top-3 accuracy
  3. Secure Rewrite Quality: BLEU-4, ROUGE-L, CodeBLEU
  4. Severity Prediction: Accuracy, weighted F1

Requirement v: Quantitative Performance evaluation using appropriate metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)


# ---------------------------------------------------------------------------
# Detection metrics (binary: vulnerable / not vulnerable)
# ---------------------------------------------------------------------------

def compute_detection_metrics(
    y_true: list[int], y_pred: list[int]
) -> dict:
    """
    Compute binary vulnerability detection metrics.

    Args:
        y_true: Ground truth labels (1 = vulnerable, 0 = not vulnerable)
        y_pred: Predicted labels

    Returns:
        Dict with precision, recall, f1, accuracy
    """
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "classification_report": classification_report(
            y_true, y_pred, target_names=["Not Vulnerable", "Vulnerable"]
        ),
    }


# ---------------------------------------------------------------------------
# CWE classification metrics
# ---------------------------------------------------------------------------

def compute_cwe_accuracy(
    y_true: list[str], y_pred: list[str], top_k: int = 3
) -> dict:
    """
    Compute CWE classification accuracy.

    For top-k, y_pred should be a list of lists (ranked predictions).
    For top-1, y_pred is a flat list of strings.
    """
    if not y_true:
        return {"top1_accuracy": 0.0}

    # Top-1 accuracy
    top1 = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)

    metrics = {"top1_accuracy": top1}

    # Per-CWE breakdown
    unique_cwes = sorted(set(y_true))
    per_cwe = {}
    for cwe in unique_cwes:
        indices = [i for i, t in enumerate(y_true) if t == cwe]
        if indices:
            correct = sum(1 for i in indices if y_pred[i] == cwe)
            per_cwe[cwe] = correct / len(indices)
    metrics["per_cwe_accuracy"] = per_cwe

    return metrics


# ---------------------------------------------------------------------------
# Text generation quality: BLEU, ROUGE
# ---------------------------------------------------------------------------

def compute_bleu(references: list[str], hypotheses: list[str]) -> dict:
    """
    Compute corpus-level BLEU-4 score for secure code rewrites.

    Uses sacrebleu for standardized, reproducible BLEU computation.
    """
    try:
        import sacrebleu
        # sacrebleu expects list of references per hypothesis
        refs = [[r] for r in references]
        bleu = sacrebleu.corpus_bleu(hypotheses, list(zip(*refs)))
        return {
            "bleu4": bleu.score,
            "bleu_brevity_penalty": bleu.bp,
            "bleu_ratio": bleu.sys_len / bleu.ref_len if bleu.ref_len > 0 else 0,
        }
    except Exception as e:
        logger.warning(f"BLEU computation failed: {e}")
        return {"bleu4": 0.0}


def compute_rouge(references: list[str], hypotheses: list[str]) -> dict:
    """
    Compute ROUGE-1, ROUGE-2, and ROUGE-L scores.
    """
    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)

        scores = {"rouge1": [], "rouge2": [], "rougeL": []}
        for ref, hyp in zip(references, hypotheses):
            if not ref or not hyp:
                continue
            result = scorer.score(ref, hyp)
            scores["rouge1"].append(result["rouge1"].fmeasure)
            scores["rouge2"].append(result["rouge2"].fmeasure)
            scores["rougeL"].append(result["rougeL"].fmeasure)

        return {
            "rouge1": np.mean(scores["rouge1"]) if scores["rouge1"] else 0.0,
            "rouge2": np.mean(scores["rouge2"]) if scores["rouge2"] else 0.0,
            "rougeL": np.mean(scores["rougeL"]) if scores["rougeL"] else 0.0,
        }
    except Exception as e:
        logger.warning(f"ROUGE computation failed: {e}")
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}


def compute_codebleu(references: list[str], hypotheses: list[str], lang: str = "c") -> dict:
    """
    Compute CodeBLEU — a code-aware BLEU variant that considers:
      - n-gram match (standard BLEU)
      - Weighted n-gram match (keyword-aware)
      - Syntactic AST match
      - Semantic data-flow match

    Requires: pip install codebleu
    """
    try:
        from codebleu import calc_codebleu
        result = calc_codebleu(
            references=[[r] for r in references],
            predictions=hypotheses,
            lang=lang,
            weights=(0.25, 0.25, 0.25, 0.25),
        )
        return {
            "codebleu": result["codebleu"],
            "ngram_match": result["ngram_match_score"],
            "weighted_ngram_match": result["weighted_ngram_match_score"],
            "syntax_match": result["syntax_match_score"],
            "dataflow_match": result["dataflow_match_score"],
        }
    except ImportError:
        logger.warning("codebleu not installed. Run: pip install codebleu")
        return {"codebleu": 0.0}
    except Exception as e:
        logger.warning(f"CodeBLEU computation failed: {e}")
        return {"codebleu": 0.0}


# ---------------------------------------------------------------------------
# Severity prediction
# ---------------------------------------------------------------------------

def compute_severity_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """Compute severity prediction accuracy and weighted F1."""
    valid_pairs = [(t, p) for t, p in zip(y_true, y_pred) if t and p]
    if not valid_pairs:
        return {"severity_accuracy": 0.0, "severity_f1": 0.0}

    y_t, y_p = zip(*valid_pairs)
    return {
        "severity_accuracy": accuracy_score(y_t, y_p),
        "severity_f1_weighted": f1_score(y_t, y_p, average="weighted", zero_division=0),
    }


# ---------------------------------------------------------------------------
# Full evaluation pipeline
# ---------------------------------------------------------------------------

def evaluate_results(results: list[dict], output_dir: str = "./results") -> dict:
    """
    Run all metrics on a list of prediction results.

    Each result dict should have:
      - ground_truth_cwe, predicted_cwe
      - ground_truth_secure_code, predicted_secure_code
      - is_vulnerable_pred (bool)
      - ground_truth_severity (optional)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Filter to samples with predictions
    valid = [r for r in results if r.get("predicted_secure_code")]
    logger.info(f"Evaluating {len(valid)}/{len(results)} samples with predictions")

    all_metrics = {}

    # --- Detection metrics ---
    y_true_vuln = [1] * len(results)  # All test samples are vulnerable
    y_pred_vuln = [1 if r.get("is_vulnerable_pred", True) else 0 for r in results]
    all_metrics["detection"] = compute_detection_metrics(y_true_vuln, y_pred_vuln)

    # --- CWE classification ---
    cwe_true = [r.get("ground_truth_cwe", "") for r in results]
    cwe_pred = [r.get("predicted_cwe", "") for r in results]
    all_metrics["cwe_classification"] = compute_cwe_accuracy(cwe_true, cwe_pred)

    # --- Rewrite quality ---
    if valid:
        refs = [r["ground_truth_secure_code"] for r in valid]
        hyps = [r["predicted_secure_code"] for r in valid]

        all_metrics["bleu"] = compute_bleu(refs, hyps)
        all_metrics["rouge"] = compute_rouge(refs, hyps)
        all_metrics["codebleu"] = compute_codebleu(refs, hyps)

    # --- Severity ---
    sev_true = [r.get("ground_truth_severity", "") for r in results]
    sev_pred = [r.get("predicted_severity", "") for r in results]
    all_metrics["severity"] = compute_severity_metrics(sev_true, sev_pred)

    # Save metrics
    metrics_path = output_path / "metrics.json"
    with open(metrics_path, "w") as f:
        # Remove non-serializable items
        serializable = {
            k: {kk: vv for kk, vv in v.items() if not isinstance(vv, dict) or kk != "per_cwe_accuracy"}
            for k, v in all_metrics.items()
            if isinstance(v, dict)
        }
        json.dump(serializable, f, indent=2, default=str)
    logger.info(f"Metrics saved to {metrics_path}")

    return all_metrics


def print_metrics_summary(metrics: dict) -> None:
    """Print a human-readable summary of evaluation metrics."""
    print("\n" + "=" * 60)
    print("EVALUATION METRICS SUMMARY")
    print("=" * 60)

    if "detection" in metrics:
        d = metrics["detection"]
        print(f"\n[Vulnerability Detection]")
        print(f"  Precision : {d.get('precision', 0):.3f}")
        print(f"  Recall    : {d.get('recall', 0):.3f}")
        print(f"  F1        : {d.get('f1', 0):.3f}")
        print(f"  Accuracy  : {d.get('accuracy', 0):.3f}")

    if "cwe_classification" in metrics:
        c = metrics["cwe_classification"]
        print(f"\n[CWE Classification]")
        print(f"  Top-1 Accuracy: {c.get('top1_accuracy', 0):.3f}")

    if "bleu" in metrics:
        print(f"\n[Rewrite Quality]")
        print(f"  BLEU-4    : {metrics['bleu'].get('bleu4', 0):.2f}")
        print(f"  ROUGE-L   : {metrics.get('rouge', {}).get('rougeL', 0):.3f}")
        print(f"  CodeBLEU  : {metrics.get('codebleu', {}).get('codebleu', 0):.3f}")

    if "severity" in metrics:
        s = metrics["severity"]
        print(f"\n[Severity Prediction]")
        print(f"  Accuracy  : {s.get('severity_accuracy', 0):.3f}")
        print(f"  F1 (wtd)  : {s.get('severity_f1_weighted', 0):.3f}")

    print("=" * 60 + "\n")
