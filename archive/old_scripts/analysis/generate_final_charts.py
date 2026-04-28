"""
Generates final comparison charts for the report using all results.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

Path("results").mkdir(exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────
# V1 results (CodeLlama-7B, 39 CWEs)
v1 = {
    "baseline_cwe":  0.00,
    "finetuned_cwe": 0.22,
    "baseline_bleu":  1.65,
    "finetuned_bleu": 2.50,
    "baseline_rouge":  0.163,
    "finetuned_rouge": 0.272,
    "baseline_halluc":  0.01,
    "finetuned_halluc": 0.00,
}

# V2 results (DeepSeek-6.7B, top-10 CWEs)
v2 = {
    "baseline_cwe":  0.24,
    "finetuned_cwe": 0.26,
    "finetuned_cwe_valid": 0.377,
    "baseline_bleu":  5.69,
    "finetuned_bleu": 5.69,
    "baseline_rouge":  0.270,
    "finetuned_rouge": 0.270,
    "baseline_halluc":  0.00,
    "finetuned_halluc": 0.00,
}

# ── Chart 1: CWE Accuracy progression ────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("AI Code Auditor — V1 vs V2 Results", fontsize=14, fontweight="bold")

ax = axes[0]
models = ["V1 Baseline\n(CodeLlama-7B\nZero-shot)", "V1 Fine-tuned\n(CodeLlama-7B\nQLoRA)", "V2 Baseline\n(DeepSeek-6.7B\nZero-shot)", "V2 Fine-tuned\n(DeepSeek-6.7B\nQLoRA)"]
accs   = [v1["baseline_cwe"]*100, v1["finetuned_cwe"]*100, v2["baseline_cwe"]*100, v2["finetuned_cwe"]*100]
colors = ["#5b9bd5", "#2e75b6", "#70ad47", "#375623"]
bars   = ax.bar(models, accs, color=colors, alpha=0.85, width=0.5)
ax.set_title("CWE Classification Accuracy", fontweight="bold")
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 45)
ax.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, accs):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
            f"{val:.0f}%", ha="center", fontsize=11, fontweight="bold")

# Add annotation for valid-only accuracy
ax.annotate("37.7%\n(valid only)", xy=(3, v2["finetuned_cwe"]*100),
            xytext=(3, 35), ha="center", fontsize=9, color="darkgreen",
            arrowprops=dict(arrowstyle="->", color="darkgreen"),
            bbox=dict(boxstyle="round,pad=0.2", facecolor="lightgreen", alpha=0.5))

# ── Chart 2: Full metrics comparison ─────────────────────────────────────
ax2 = axes[1]
metrics = ["BLEU-4", "ROUGE-L\n(×100)", "CWE Acc\n(×100)"]
v1_bl = [v1["baseline_bleu"], v1["baseline_rouge"]*100, v1["baseline_cwe"]*100]
v1_ft = [v1["finetuned_bleu"], v1["finetuned_rouge"]*100, v1["finetuned_cwe"]*100]
v2_bl = [v2["baseline_bleu"], v2["baseline_rouge"]*100, v2["baseline_cwe"]*100]
v2_ft = [v2["finetuned_bleu"], v2["finetuned_rouge"]*100, v2["finetuned_cwe"]*100]

x = np.arange(len(metrics))
w = 0.2
ax2.bar(x - 1.5*w, v1_bl, w, label="V1 Baseline",   color="#aec7e8", alpha=0.85)
ax2.bar(x - 0.5*w, v1_ft, w, label="V1 Fine-tuned", color="#1f77b4", alpha=0.85)
ax2.bar(x + 0.5*w, v2_bl, w, label="V2 Baseline",   color="#98df8a", alpha=0.85)
ax2.bar(x + 1.5*w, v2_ft, w, label="V2 Fine-tuned", color="#2ca02c", alpha=0.85)
ax2.set_xticks(x)
ax2.set_xticklabels(metrics)
ax2.set_title("All Metrics Comparison", fontweight="bold")
ax2.set_ylabel("Score")
ax2.legend(fontsize=8)
ax2.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("results/v1_v2_final_comparison.png", dpi=150, bbox_inches="tight")
print("Saved: results/v1_v2_final_comparison.png")

# ── Chart 3: Per-CWE accuracy (V2) ───────────────────────────────────────
with open("results/evaluation_metrics_v2.json") as f:
    m = json.load(f)

per_cwe = m["baseline"]["per_cwe"]
cwes    = list(per_cwe.keys())
bl_accs = [per_cwe[c]["correct"]/per_cwe[c]["total"]*100 for c in cwes]
counts  = [per_cwe[c]["total"] for c in cwes]

fig, ax = plt.subplots(figsize=(12, 5))
x = np.arange(len(cwes))
bars = ax.bar(x, bl_accs, color=plt.cm.RdYlGn([v/100 for v in bl_accs]), alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels([f"{c}\n(n={n})" for c, n in zip(cwes, counts)], rotation=30, ha="right")
ax.set_title("Per-CWE Classification Accuracy — V2 DeepSeek-6.7B", fontweight="bold")
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 80)
ax.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, bl_accs):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
            f"{val:.0f}%", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig("results/per_cwe_accuracy_v2.png", dpi=150, bbox_inches="tight")
print("Saved: results/per_cwe_accuracy_v2.png")

# ── Summary table ─────────────────────────────────────────────────────────
print("\n" + "="*65)
print(f"{'COMPLETE RESULTS SUMMARY':^65}")
print("="*65)
print(f"{'':30} {'V1 Base':>8} {'V1 FT':>8} {'V2 Base':>8} {'V2 FT':>8}")
print("-"*65)
print(f"{'Model':<30} {'CodeLlama':>8} {'CodeLlama':>8} {'DeepSeek':>8} {'DeepSeek':>8}")
print(f"{'CWE classes':<30} {'39':>8} {'39':>8} {'10':>8} {'10':>8}")
print(f"{'BLEU-4':<30} {v1['baseline_bleu']:>8.2f} {v1['finetuned_bleu']:>8.2f} {v2['baseline_bleu']:>8.2f} {v2['finetuned_bleu']:>8.2f}")
print(f"{'ROUGE-L':<30} {v1['baseline_rouge']:>8.3f} {v1['finetuned_rouge']:>8.3f} {v2['baseline_rouge']:>8.3f} {v2['finetuned_rouge']:>8.3f}")
print(f"{'CWE Accuracy':<30} {v1['baseline_cwe']:>8.1%} {v1['finetuned_cwe']:>8.1%} {v2['baseline_cwe']:>8.1%} {v2['finetuned_cwe']:>8.1%}")
print(f"{'Hallucination Rate':<30} {v1['baseline_halluc']:>8.1%} {v1['finetuned_halluc']:>8.1%} {v2['baseline_halluc']:>8.1%} {v2['finetuned_halluc']:>8.1%}")
print("="*65)
print("\nKey findings:")
print(f"  Model upgrade (CodeLlama→DeepSeek): baseline 0% → 24% (+24pp)")
print(f"  Fine-tuning V1 (39 CWEs):           0% → 22% (+22pp)")
print(f"  Fine-tuning V2 (10 CWEs):           24% → 26% (+2pp overall)")
print(f"  Fine-tuning V2 (valid responses):   32.9% → 37.7% (+4.8pp)")
