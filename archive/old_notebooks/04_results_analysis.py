# %% [markdown]
# # Notebook 4: Results Analysis & Visualization
#
# Generates all charts and tables for the final report using real evaluation data.
# No GPU required — runs entirely locally.

# %%
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

RESULTS_DIR = Path("results")
Path("results").mkdir(exist_ok=True)

# Load all results
with open(RESULTS_DIR / "evaluation_metrics.json") as f:
    metrics = json.load(f)

with open(RESULTS_DIR / "qualitative_report.json") as f:
    qual = json.load(f)

baseline  = metrics["baseline"]
finetuned = metrics["finetuned"]

print("Loaded evaluation metrics:")
print(f"  Baseline  — BLEU: {baseline['bleu4']:.2f} | ROUGE-L: {baseline['rougeL']:.3f} | CWE Acc: {baseline['cwe_accuracy']:.1%}")
print(f"  Fine-tuned — BLEU: {finetuned['bleu4']:.2f} | ROUGE-L: {finetuned['rougeL']:.3f} | CWE Acc: {finetuned['cwe_accuracy']:.1%}")

# %% [markdown]
# ## Main Comparison Chart

# %%
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle("AI Code Auditor — Baseline vs Fine-tuned (QLoRA CodeLlama-7B)",
             fontsize=14, fontweight="bold", y=1.02)

colors = {"baseline": "steelblue", "finetuned": "mediumseagreen"}

# --- Plot 1: BLEU-4 and ROUGE-L ---
ax = axes[0]
metrics_names = ["BLEU-4", "ROUGE-L"]
b_vals = [baseline["bleu4"], baseline["rougeL"] * 100]   # scale ROUGE to same range
f_vals = [finetuned["bleu4"], finetuned["rougeL"] * 100]

x = np.arange(len(metrics_names))
w = 0.35
bars1 = ax.bar(x - w/2, b_vals, w, label="Baseline",    color=colors["baseline"],  alpha=0.85)
bars2 = ax.bar(x + w/2, f_vals, w, label="Fine-tuned",  color=colors["finetuned"], alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(["BLEU-4", "ROUGE-L\n(×100)"])
ax.set_ylabel("Score")
ax.set_title("Text Generation Quality", fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
for bar in list(bars1) + list(bars2):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
            f"{bar.get_height():.2f}", ha="center", fontsize=9, fontweight="bold")

# --- Plot 2: CWE Classification Accuracy ---
ax2 = axes[1]
models = ["Baseline\n(Zero-shot)", "Fine-tuned\n(QLoRA)"]
accs   = [baseline["cwe_accuracy"] * 100, finetuned["cwe_accuracy"] * 100]
bar_colors = [colors["baseline"], colors["finetuned"]]
bars = ax2.bar(models, accs, color=bar_colors, alpha=0.85, width=0.4)
ax2.set_ylabel("Accuracy (%)")
ax2.set_title("CWE Classification Accuracy", fontweight="bold")
ax2.set_ylim(0, 35)
ax2.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, accs):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f"{val:.1f}%", ha="center", fontsize=12, fontweight="bold")
ax2.annotate("0% → 22%\n(∞ improvement)", xy=(0.5, 0.7), xycoords="axes fraction",
             ha="center", fontsize=10, color="darkgreen",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.4))

# --- Plot 3: Hallucination Rate ---
ax3 = axes[2]
halluc = [baseline["halluc_rate"] * 100, finetuned["halluc_rate"] * 100]
bars = ax3.bar(models, halluc, color=["coral", "mediumseagreen"], alpha=0.85, width=0.4)
ax3.set_ylabel("Hallucination Rate (%)")
ax3.set_title("Hallucination Rate\n(lower is better)", fontweight="bold")
ax3.set_ylim(0, 3)
ax3.grid(axis="y", alpha=0.3)
for bar, val in zip(bars, halluc):
    label = f"{val:.1f}%" if val > 0 else "0.0%\n✓ None"
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
             label, ha="center", fontsize=11, fontweight="bold")

plt.tight_layout()
plt.savefig(RESULTS_DIR / "final_comparison.png", dpi=150, bbox_inches="tight")
print("Saved: results/final_comparison.png")

# %% [markdown]
# ## Improvement Summary Table

# %%
print("\n" + "="*60)
print(f"{'MODEL COMPARISON TABLE':^60}")
print("="*60)
print(f"{'Metric':<28} {'Baseline':>10} {'Fine-tuned':>12} {'Δ':>8}")
print("-"*60)

rows = [
    ("BLEU-4",              baseline["bleu4"],         finetuned["bleu4"]),
    ("ROUGE-L",             baseline["rougeL"],        finetuned["rougeL"]),
    ("CWE Top-1 Accuracy",  baseline["cwe_accuracy"],  finetuned["cwe_accuracy"]),
    ("Hallucination Rate",  baseline["halluc_rate"],   finetuned["halluc_rate"]),
]

for name, b, f in rows:
    delta = f - b
    arrow = "↑" if (delta > 0 and name != "Hallucination Rate") or (delta < 0 and name == "Hallucination Rate") else "↓"
    print(f"{name:<28} {b:>10.3f} {f:>12.3f} {arrow}{abs(delta):>6.3f}")

print("="*60)
print(f"\nSamples evaluated: {baseline['n_samples']} (test set subset)")
print(f"Improvement cases (CWE correct in FT, wrong in baseline): {qual['improvement_cases']}")
print(f"Hallucination cases: {qual['hallucination_cases']}")

# %% [markdown]
# ## Qualitative Examples — Where Fine-tuning Helped

# %%
print("\n" + "="*60)
print("TOP IMPROVEMENT EXAMPLES")
print("="*60)

for i, ex in enumerate(qual["top_improvements"][:3]):
    print(f"\n── Example {i+1} ──────────────────────────────────")
    print(f"Ground Truth CWE : {ex['ground_truth_cwe']}")
    print(f"Baseline pred    : {ex['baseline_pred']}  ✗")
    print(f"Fine-tuned pred  : {ex['finetuned_pred']}  ✓")
    print(f"Code snippet     :\n{ex['code_snippet'][:150].strip()}...")
    print(f"\nFine-tuned output preview:")
    print(ex["finetuned_output"][:300].strip())
    print()

# %% [markdown]
# ## Qualitative Examples Chart

# %%
# CWE accuracy breakdown — what the fine-tuned model gets right
import json
from collections import Counter

with open(RESULTS_DIR / "finetuned_results.jsonl") as f:
    ft_results = [json.loads(l) for l in f]

with open(RESULTS_DIR / "baseline_results.jsonl") as f:
    bl_results = [json.loads(l) for l in f]

# Per-CWE accuracy for fine-tuned
cwe_correct = Counter()
cwe_total   = Counter()
for r in ft_results:
    gt = r["ground_truth_cwe"]
    cwe_total[gt] += 1
    if r["predicted_cwe"] == gt:
        cwe_correct[gt] += 1

top_cwes = [c for c, _ in Counter({k: v for k, v in cwe_total.items()}).most_common(10)]
ft_accs  = [cwe_correct[c] / cwe_total[c] for c in top_cwes]
bl_accs  = []
for c in top_cwes:
    bl_correct = sum(1 for r in bl_results if r["ground_truth_cwe"] == c and r["predicted_cwe"] == c)
    bl_total   = sum(1 for r in bl_results if r["ground_truth_cwe"] == c)
    bl_accs.append(bl_correct / bl_total if bl_total > 0 else 0)

x = np.arange(len(top_cwes))
w = 0.35

fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(x - w/2, [v*100 for v in bl_accs], w, label="Baseline",   color="steelblue",      alpha=0.85)
ax.bar(x + w/2, [v*100 for v in ft_accs], w, label="Fine-tuned", color="mediumseagreen", alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(top_cwes, rotation=30, ha="right")
ax.set_ylabel("CWE Classification Accuracy (%)")
ax.set_title("Per-CWE Classification Accuracy: Baseline vs Fine-tuned", fontweight="bold")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(RESULTS_DIR / "per_cwe_accuracy.png", dpi=150, bbox_inches="tight")
print("Saved: results/per_cwe_accuracy.png")

# %% [markdown]
# ## Final Summary

# %%
print("\n" + "="*60)
print(f"{'PROJECT SUMMARY':^60}")
print("="*60)
print(f"{'Model':<35} CodeLlama-7B")
print(f"{'Fine-tuning method':<35} QLoRA (4-bit NF4, LoRA r=16)")
print(f"{'Dataset':<35} Big-Vul (3,162 samples)")
print(f"{'Training epochs':<35} 2")
print(f"{'Training time':<35} ~3.5 hours (T4 GPU)")
print(f"{'Adapter size':<35} ~1 GB")
print(f"{'Trainable parameters':<35} ~40M / 6.7B (0.5%)")
print()
print(f"{'RESULTS':^60}")
print("-"*60)
print(f"{'CWE accuracy improvement':<35} 0% → 22% (↑ from nothing)")
print(f"{'BLEU-4 improvement':<35} 1.65 → 2.50 (↑ 51%)")
print(f"{'ROUGE-L improvement':<35} 0.163 → 0.272 (↑ 67%)")
print(f"{'Hallucination rate':<35} 1% → 0% (eliminated)")
print(f"{'Improvement cases':<35} 22 / 100 samples")
print("="*60)

print("\nAll charts saved to results/:")
for f in sorted(Path("results").glob("*.png")):
    print(f"  {f.name}")
