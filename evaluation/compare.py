"""
Comparison module: baseline vs fine-tuned model performance.

Generates comparison tables and visualizations for the final report.
Requirement vii: Clear improvement demonstration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger

from evaluation.metrics import evaluate_results, print_metrics_summary


def load_results(results_path: str) -> list[dict]:
    """Load prediction results from a JSONL file."""
    results = []
    with open(results_path) as f:
        for line in f:
            results.append(json.loads(line.strip()))
    return results


def compare_models(
    model_results: dict[str, list[dict]],
    output_dir: str = "./results",
) -> pd.DataFrame:
    """
    Compare multiple models on all metrics.

    Args:
        model_results: Dict mapping model name -> list of prediction results
        output_dir: Where to save comparison outputs

    Returns:
        DataFrame with one row per model and columns for each metric
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = []
    for model_name, results in model_results.items():
        logger.info(f"Evaluating {model_name}...")
        metrics = evaluate_results(results, output_dir=str(output_path / model_name))

        row = {"model": model_name}

        # Detection
        det = metrics.get("detection", {})
        row["detection_f1"] = det.get("f1", 0)
        row["detection_precision"] = det.get("precision", 0)
        row["detection_recall"] = det.get("recall", 0)

        # CWE
        cwe = metrics.get("cwe_classification", {})
        row["cwe_top1_accuracy"] = cwe.get("top1_accuracy", 0)

        # Rewrite quality
        row["bleu4"] = metrics.get("bleu", {}).get("bleu4", 0)
        row["rouge_l"] = metrics.get("rouge", {}).get("rougeL", 0)
        row["codebleu"] = metrics.get("codebleu", {}).get("codebleu", 0)

        # Severity
        sev = metrics.get("severity", {})
        row["severity_accuracy"] = sev.get("severity_accuracy", 0)

        rows.append(row)

    df = pd.DataFrame(rows).set_index("model")

    # Save comparison table
    table_path = output_path / "model_comparison.csv"
    df.to_csv(table_path)
    logger.info(f"Comparison table saved to {table_path}")

    # Print table
    print("\n" + "=" * 80)
    print("MODEL COMPARISON TABLE")
    print("=" * 80)
    print(df.to_string(float_format="{:.3f}".format))
    print("=" * 80 + "\n")

    return df


def plot_comparison(
    df: pd.DataFrame,
    output_dir: str = "./results",
    save_fig: bool = True,
) -> None:
    """Generate comparison bar charts for the report."""
    output_path = Path(output_dir)

    metrics_to_plot = {
        "Detection Performance": ["detection_f1", "detection_precision", "detection_recall"],
        "Rewrite Quality": ["bleu4", "rouge_l", "codebleu"],
        "Classification": ["cwe_top1_accuracy", "severity_accuracy"],
    }

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("AI Code Auditor — Model Comparison", fontsize=14, fontweight="bold")

    colors = sns.color_palette("husl", len(df))

    for ax, (title, metric_cols) in zip(axes, metrics_to_plot.items()):
        available_cols = [c for c in metric_cols if c in df.columns]
        if not available_cols:
            continue

        plot_df = df[available_cols].copy()
        x = np.arange(len(available_cols))
        width = 0.8 / len(df)

        for i, (model_name, row) in enumerate(plot_df.iterrows()):
            offset = (i - len(df) / 2) * width + width / 2
            bars = ax.bar(
                x + offset,
                row[available_cols].values,
                width,
                label=model_name,
                color=colors[i],
                alpha=0.85,
            )
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0.01:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 0.01,
                        f"{height:.2f}",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                    )

        ax.set_title(title, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(
            [c.replace("_", "\n") for c in available_cols], fontsize=8
        )
        ax.set_ylim(0, 1.15)
        ax.set_ylabel("Score")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if save_fig:
        fig_path = output_path / "model_comparison.png"
        plt.savefig(fig_path, dpi=150, bbox_inches="tight")
        logger.info(f"Comparison plot saved to {fig_path}")

    plt.show()


def plot_cwe_distribution(
    results: list[dict],
    output_dir: str = "./results",
    top_n: int = 15,
) -> None:
    """Plot ground truth vs predicted CWE distribution."""
    output_path = Path(output_dir)

    gt_cwes = [r.get("ground_truth_cwe", "Unknown") for r in results]
    pred_cwes = [r.get("predicted_cwe", "Unknown") for r in results]

    from collections import Counter
    gt_counts = Counter(gt_cwes).most_common(top_n)
    top_cwes = [c[0] for c in gt_counts]

    gt_vals = [Counter(gt_cwes)[c] for c in top_cwes]
    pred_vals = [Counter(pred_cwes)[c] for c in top_cwes]

    x = np.arange(len(top_cwes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width / 2, gt_vals, width, label="Ground Truth", color="steelblue", alpha=0.8)
    ax.bar(x + width / 2, pred_vals, width, label="Predicted", color="coral", alpha=0.8)

    ax.set_title(f"CWE Distribution: Ground Truth vs Predicted (Top {top_n})", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(top_cwes, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig_path = output_path / "cwe_distribution.png"
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    logger.info(f"CWE distribution plot saved to {fig_path}")
    plt.show()
