# %% [markdown]
# # Notebook 3: Fine-tuning Experiment — Results Analysis
#
# Analyzes the completed LoRA fine-tuning run on DeepSeek-Coder-1.3B.
# Uses the saved training_log.json — no GPU required.
#
# **Training summary:**
# - Model: deepseek-ai/deepseek-coder-1.3b-base
# - Method: LoRA (r=16, alpha=32) — fp16, no quantization
# - Dataset: Big-Vul (5,844 train / 731 val samples)
# - Hardware: Google Colab Tesla T4 (15.6GB VRAM)
# - Duration: ~3 hours (1,095 steps, 3 epochs)

# %%
import json
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — saves files without display
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

# Load training log
LOG_PATH = Path("notebooks/training_log.json")
if not LOG_PATH.exists():
    LOG_PATH = Path("training_log.json")

with open(LOG_PATH) as f:
    log_history = json.load(f)

print(f"Loaded {len(log_history)} log entries")

# %% [markdown]
# ## Parse Training & Eval Loss

# %%
train_steps, train_losses = [], []
eval_steps, eval_losses   = [], []
lr_steps, lr_values       = [], []

for entry in log_history:
    if "loss" in entry and "eval_loss" not in entry:
        train_steps.append(entry["step"])
        train_losses.append(entry["loss"])
    if "eval_loss" in entry:
        eval_steps.append(entry["step"])
        eval_losses.append(entry["eval_loss"])
    if "learning_rate" in entry:
        lr_steps.append(entry["step"])
        lr_values.append(entry["learning_rate"])

# Final stats
final_entry = [e for e in log_history if "train_loss" in e]
if final_entry:
    e = final_entry[0]
    print(f"\n{'='*50}")
    print(f"TRAINING COMPLETE")
    print(f"{'='*50}")
    print(f"  Total steps      : {e['step']}")
    print(f"  Epochs completed : {e['epoch']:.2f}")
    print(f"  Final train loss : {e['train_loss']:.4f}")
    print(f"  Runtime          : {e['train_runtime']/3600:.2f} hours")
    print(f"  Samples/sec      : {e['train_samples_per_second']:.3f}")
    print(f"  Best eval loss   : {min(eval_losses):.4f} (step {eval_steps[eval_losses.index(min(eval_losses))]})")
    print(f"{'='*50}")

# %% [markdown]
# ## Training Loss Curve

# %%
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
fig.suptitle("LoRA Fine-tuning — DeepSeek-Coder-1.3B on Big-Vul", fontsize=14, fontweight="bold")

# --- Plot 1: Loss curves ---
ax = axes[0]
ax.plot(train_steps, train_losses, color="steelblue", alpha=0.6, linewidth=1, label="Train Loss (per 25 steps)")

# Smoothed train loss
window = 5
smoothed = np.convolve(train_losses, np.ones(window)/window, mode='valid')
smooth_steps = train_steps[window-1:]
ax.plot(smooth_steps, smoothed, color="steelblue", linewidth=2.5, label="Train Loss (smoothed)")

ax.plot(eval_steps, eval_losses, color="coral", linewidth=2.5, linestyle="--",
        marker="o", markersize=5, label="Eval Loss")

# Epoch boundaries (365 steps/epoch)
for epoch_end in [365, 730, 1095]:
    ax.axvline(epoch_end, color="gray", linestyle=":", alpha=0.5)
    ax.text(epoch_end + 5, max(train_losses)*0.95, f"Epoch {epoch_end//365}", fontsize=8, color="gray")

ax.set_title("Loss Curves", fontweight="bold")
ax.set_xlabel("Training Step")
ax.set_ylabel("Loss")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.set_ylim(0, max(train_losses) * 1.1)

# --- Plot 2: Learning rate schedule ---
ax2 = axes[1]
ax2.plot(lr_steps, lr_values, color="mediumseagreen", linewidth=2)
ax2.set_title("Learning Rate Schedule (Cosine)", fontweight="bold")
ax2.set_xlabel("Training Step")
ax2.set_ylabel("Learning Rate")
ax2.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
ax2.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
ax2.grid(alpha=0.3)

plt.tight_layout()
Path("results").mkdir(exist_ok=True)
plt.savefig("results/training_loss_curve.png", dpi=150, bbox_inches="tight")
# plt.show()
print("Saved: results/training_loss_curve.png")

# %% [markdown]
# ## Eval Loss Progression (per epoch)

# %%
fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(eval_steps, eval_losses, color="coral", linewidth=2.5,
        marker="o", markersize=7, label="Eval Loss")

# Annotate each point
for s, l in zip(eval_steps, eval_losses):
    ax.annotate(f"{l:.4f}", (s, l), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=8)

ax.set_title("Validation Loss per Checkpoint", fontweight="bold")
ax.set_xlabel("Training Step")
ax.set_ylabel("Eval Loss")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("results/eval_loss_progression.png", dpi=150, bbox_inches="tight")
# plt.show()
print("Saved: results/eval_loss_progression.png")

# %% [markdown]
# ## Gradient Norm (training stability)

# %%
grad_norms = [e["grad_norm"] for e in log_history if "grad_norm" in e]
grad_steps = [e["step"] for e in log_history if "grad_norm" in e]

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(grad_steps, grad_norms, color="mediumpurple", alpha=0.7, linewidth=1)
ax.set_title("Gradient Norm During Training", fontweight="bold")
ax.set_xlabel("Step")
ax.set_ylabel("Gradient Norm")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("results/gradient_norm.png", dpi=150, bbox_inches="tight")
# plt.show()

print(f"Mean grad norm : {np.mean(grad_norms):.4f}")
print(f"Max  grad norm : {max(grad_norms):.4f}")
print(f"Min  grad norm : {min(grad_norms):.4f}")
print("\nStable training — no gradient explosions detected ✓" if max(grad_norms) < 5 else "⚠ High gradient norms detected")

# %% [markdown]
# ## Summary Table

# %%
print("\n" + "="*55)
print(f"{'FINE-TUNING SUMMARY':^55}")
print("="*55)
print(f"{'Model':<30} DeepSeek-Coder-1.3B")
print(f"{'Method':<30} LoRA (r=16, α=32, fp16)")
print(f"{'Trainable params':<30} 14,991,360 (1.10%)")
print(f"{'Total params':<30} 1,361,463,296")
print(f"{'Training samples':<30} 5,844")
print(f"{'Validation samples':<30} 731")
print(f"{'Epochs':<30} 3")
print(f"{'Total steps':<30} 1,095")
print(f"{'Batch size (effective)':<30} 16 (2 × grad_accum 8)")
print(f"{'Initial train loss':<30} {train_losses[0]:.4f}")
print(f"{'Final train loss':<30} {train_losses[-1]:.4f}")
print(f"{'Loss reduction':<30} {((train_losses[0]-train_losses[-1])/train_losses[0]*100):.1f}%")
print(f"{'Initial eval loss':<30} {eval_losses[0]:.4f}")
print(f"{'Final eval loss':<30} {eval_losses[-1]:.4f}")
print(f"{'Best eval loss':<30} {min(eval_losses):.4f}")
print(f"{'Training time':<30} ~3 hours (T4 GPU)")
print(f"{'Adapter size':<30} 424.7 MB")
print("="*55)
