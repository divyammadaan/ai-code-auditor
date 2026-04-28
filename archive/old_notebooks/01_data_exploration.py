# %% [markdown]
# # Notebook 1: Big-Vul Dataset Exploration
#
# Explores the preprocessed Big-Vul dataset:
# - Dataset size and structure
# - CWE distribution across splits
# - Code length distribution
# - Sample examples

# %%
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import Counter
from pathlib import Path

sns.set_theme(style="whitegrid")
PROCESSED_DIR = Path("data/processed")
Path("results").mkdir(exist_ok=True)

# Load all splits
def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

train_records = load_jsonl(PROCESSED_DIR / "train.jsonl")
val_records   = load_jsonl(PROCESSED_DIR / "val.jsonl")
test_records  = load_jsonl(PROCESSED_DIR / "test.jsonl")

print(f"Train : {len(train_records):,} samples")
print(f"Val   : {len(val_records):,} samples")
print(f"Test  : {len(test_records):,} samples")
print(f"Total : {len(train_records)+len(val_records)+len(test_records):,} samples")

# %% [markdown]
# ## CWE Distribution (Top 20)

# %%
cwe_counts = Counter(r["cwe"] for r in train_records)
top_cwes = cwe_counts.most_common(20)
cwes, counts = zip(*top_cwes)

fig, ax = plt.subplots(figsize=(14, 6))
colors = sns.color_palette("husl", len(cwes))
bars = ax.bar(cwes, counts, color=colors)
ax.set_title("Top 20 CWE Categories in Training Set (Big-Vul)", fontsize=14, fontweight="bold")
ax.set_xlabel("CWE ID")
ax.set_ylabel("Number of Samples")
ax.tick_params(axis="x", rotation=45)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            str(count), ha="center", va="bottom", fontsize=8)
plt.tight_layout()
plt.savefig("results/cwe_distribution_train.png", dpi=150, bbox_inches="tight")
print("Saved: results/cwe_distribution_train.png")
print(f"\nTotal unique CWEs: {len(cwe_counts)}")
print(f"Top 5: {top_cwes[:5]}")

# %% [markdown]
# ## CWE Distribution Across Splits

# %%
top10_cwes = [c for c, _ in cwe_counts.most_common(10)]
train_counts = [Counter(r["cwe"] for r in train_records)[c] for c in top10_cwes]
val_counts   = [Counter(r["cwe"] for r in val_records)[c]   for c in top10_cwes]
test_counts  = [Counter(r["cwe"] for r in test_records)[c]  for c in top10_cwes]

x = np.arange(len(top10_cwes))
width = 0.28

fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(x - width, train_counts, width, label="Train", color="steelblue",  alpha=0.85)
ax.bar(x,         val_counts,   width, label="Val",   color="mediumseagreen", alpha=0.85)
ax.bar(x + width, test_counts,  width, label="Test",  color="coral",      alpha=0.85)
ax.set_title("CWE Distribution Across Train/Val/Test Splits (Top 10)", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(top10_cwes, rotation=30, ha="right")
ax.set_ylabel("Count")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("results/cwe_split_distribution.png", dpi=150, bbox_inches="tight")
print("Saved: results/cwe_split_distribution.png")

# %% [markdown]
# ## Code Length Distribution

# %%
code_lengths = [len(r["vulnerable_code"].splitlines()) for r in train_records]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Vulnerable Code Length Distribution (Training Set)", fontweight="bold")

axes[0].hist(code_lengths, bins=50, color="steelblue", edgecolor="white", alpha=0.8)
axes[0].axvline(np.median(code_lengths), color="red", linestyle="--",
                label=f"Median: {np.median(code_lengths):.0f} lines")
axes[0].axvline(np.mean(code_lengths), color="orange", linestyle="--",
                label=f"Mean: {np.mean(code_lengths):.0f} lines")
axes[0].set_title("Histogram")
axes[0].set_xlabel("Lines of Code")
axes[0].set_ylabel("Count")
axes[0].legend()

axes[1].boxplot(code_lengths, vert=True, patch_artist=True,
                boxprops=dict(facecolor="steelblue", alpha=0.6))
axes[1].set_title("Boxplot")
axes[1].set_ylabel("Lines of Code")

plt.tight_layout()
plt.savefig("results/code_length_distribution.png", dpi=150, bbox_inches="tight")
print("Saved: results/code_length_distribution.png")
print(f"\nMean   : {np.mean(code_lengths):.1f} lines")
print(f"Median : {np.median(code_lengths):.1f} lines")
print(f"Max    : {max(code_lengths)} lines")
print(f"Min    : {min(code_lengths)} lines")

# %% [markdown]
# ## CVSS Score Distribution

# %%
scores = []
for r in train_records:
    try:
        s = float(r.get("cvss_score", 0))
        if s > 0:
            scores.append(s)
    except (ValueError, TypeError):
        pass

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(scores, bins=30, color="mediumpurple", edgecolor="white", alpha=0.8)
ax.axvline(np.mean(scores), color="red", linestyle="--", label=f"Mean: {np.mean(scores):.1f}")
ax.set_title("CVSS Score Distribution (Training Set)", fontweight="bold")
ax.set_xlabel("CVSS Score")
ax.set_ylabel("Count")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("results/cvss_distribution.png", dpi=150, bbox_inches="tight")
print("Saved: results/cvss_distribution.png")
print(f"\nMean CVSS  : {np.mean(scores):.2f}")
print(f"Median CVSS: {np.median(scores):.2f}")

# %% [markdown]
# ## Dataset Summary

# %%
print("\n" + "="*50)
print(f"{'DATASET SUMMARY':^50}")
print("="*50)
print(f"{'Source':<30} Big-Vul (MSR 2020)")
print(f"{'Language':<30} C / C++")
print(f"{'Total samples':<30} {len(train_records)+len(val_records)+len(test_records):,}")
print(f"{'Train':<30} {len(train_records):,} (80%)")
print(f"{'Validation':<30} {len(val_records):,} (10%)")
print(f"{'Test':<30} {len(test_records):,} (10%)")
print(f"{'Unique CWE categories':<30} {len(cwe_counts)}")
print(f"{'Most common CWE':<30} {top_cwes[0][0]} ({top_cwes[0][1]} samples)")
print(f"{'Split strategy':<30} Stratified by CWE")
print(f"{'Avg code length':<30} {np.mean(code_lengths):.0f} lines")
print("="*50)
