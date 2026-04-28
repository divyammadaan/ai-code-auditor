# %% [markdown]
# # Notebook 3b: Fine-tuning Experiment v2 — DeepSeek-Coder-6.7B
#
# Analyzes the v2 training run.
# Changes from v1:
# - Model: DeepSeek-Coder-6.7B (vs CodeLlama-7B)
# - Dataset: Top-10 CWEs only (vs 39 CWEs)
# - Format: CWE-first output (vs markdown headers)
# - Explanations: CWE-specific (vs generic boilerplate)

# %%
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

Path("results").mkdir(exist_ok=True)

# Load both training logs for comparison
with open("notebooks/training_log_v2.json", encoding="utf-8") as f:
    log_v2 = json.load(f)

with open("notebooks/training_log.json", encoding="utf-8") as f:
    log_v1 = json.load(f)

def parse_log(log):
    train = [(e["step"], e["loss"]) for e in log if "loss" in e and "eval_loss" not in e]
    evall = [(e["step"], e["eval_loss"]) for e in log if "eval_loss" in e]
    return train, evall

tl_v1, el_v1 = parse_log(log_v1)
tl_v2, el_v2 = parse_log(log_v2)

# %% [markdown]
# ## V1 vs V2 Training Loss Comparison

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
fig.suptitle("V1 vs V2 Training Comparison", fontsize=14, fontweight="bold")

# Train loss
ax = axes[0]
if tl_v1:
    s, l = zip(*tl_v1)
    ax.plot(s, l, color="steelblue", alpha=0.5, linewidth=1)
    sm = np.convolve(l, np.ones(5)/5, mode="valid")
    ax.plot(s[4:], sm, color="steelblue", linewidth=2.5, label="V1 CodeLlama-7B (39 CWEs)")
if tl_v2:
    s, l = zip(*tl_v2)
    ax.plot(s, l, color="mediumseagreen", alpha=0.5, linewidth=1)
    if len(l) >= 5:
        sm = np.convolve(l, np.ones(5)/5, mode="valid")
        ax.plot(s[4:], sm, color="mediumseagreen", linewidth=2.5, label="V2 DeepSeek-6.7B (10 CWEs)")
    else:
        ax.plot(s, l, color="mediumseagreen", linewidth=2.5, label="V2 DeepSeek-6.7B (10 CWEs)")
ax.set_title("Training Loss", fontweight="bold")
ax.set_xlabel("Step"); ax.set_ylabel("Loss")
ax.legend(); ax.grid(alpha=0.3)

# Eval loss
ax2 = axes[1]
if el_v1:
    s, l = zip(*el_v1)
    ax2.plot(s, l, color="steelblue", linewidth=2.5, marker="o", label="V1 Eval Loss")
if el_v2:
    s, l = zip(*el_v2)
    ax2.plot(s, l, color="mediumseagreen", linewidth=2.5, marker="s", label="V2 Eval Loss")
ax2.set_title("Validation Loss", fontweight="bold")
ax2.set_xlabel("Step"); ax2.set_ylabel("Loss")
ax2.legend(); ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("results/v1_vs_v2_training.png", dpi=150, bbox_inches="tight")
print("Saved: results/v1_vs_v2_training.png")

# %% [markdown]
# ## Summary Comparison Table

# %%
print("\n" + "="*60)
print(f"{'V1 vs V2 TRAINING COMPARISON':^60}")
print("="*60)
print(f"{'':30} {'V1':>12} {'V2':>12}")
print("-"*60)
print(f"{'Model':<30} {'CodeLlama-7B':>12} {'DeepSeek-6.7B':>12}")
print(f"{'CWE classes':<30} {'39':>12} {'10':>12}")
print(f"{'Train samples':<30} {'3,162':>12} {'2,137':>12}")
print(f"{'Epochs':<30} {'2':>12} {'3':>12}")
print(f"{'Initial train loss':<30} {tl_v1[0][1]:>12.4f} {tl_v2[0][1]:>12.4f}")
print(f"{'Final train loss':<30} {tl_v1[-1][1]:>12.4f} {tl_v2[-1][1]:>12.4f}")
print(f"{'Best eval loss':<30} {min(v for _,v in el_v1):>12.4f} {min(v for _,v in el_v2):>12.4f}")
print(f"{'Output format':<30} {'Markdown':>12} {'CWE-first':>12}")
print(f"{'Explanations':<30} {'Generic':>12} {'Specific':>12}")
print("="*60)
