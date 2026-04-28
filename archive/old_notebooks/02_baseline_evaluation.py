# %% [markdown]
# # Notebook 2: Baseline Evaluation
#
# Evaluates the base CodeLlama model (zero-shot and few-shot) on the test set.
# This establishes the performance floor before fine-tuning.

# %%
import json
import sys
from pathlib import Path

sys.path.insert(0, "..")

from models.baseline import BaselineEvaluator, build_few_shot_prompt, build_zero_shot_prompt
from models.inference import CodeAuditorModel
from rag.vectorstore import VectorStore

# %% [markdown]
# ## Load test data

# %%
test_records = []
with open("../data/processed/test.jsonl") as f:
    for line in f:
        test_records.append(json.loads(line.strip()))

# Use a small subset for quick evaluation
EVAL_SUBSET = 100
test_subset = test_records[:EVAL_SUBSET]
print(f"Evaluating on {len(test_subset)} samples")

# %% [markdown]
# ## Load model

# %%
STYLE_GUIDE = """Corporate Secure Coding Style Guide:
1. Validate and sanitize all external inputs.
2. Use parameterized queries for database operations.
3. Never store sensitive data in plaintext.
4. Apply the principle of least privilege.
5. Use memory-safe functions; avoid strcpy, sprintf, gets."""

vector_store = VectorStore(persist_dir="../data/vectorstore")
model = CodeAuditorModel(
    base_model_id="codellama/CodeLlama-7b-hf",
    vector_store=vector_store,
    load_in_4bit=True,
)

# %% [markdown]
# ## Zero-shot evaluation

# %%
evaluator = BaselineEvaluator(model, STYLE_GUIDE, output_dir="../results/baseline")
zero_shot_results = evaluator.evaluate_zero_shot(test_subset, max_samples=EVAL_SUBSET)

# %% [markdown]
# ## Few-shot evaluation

# %%
few_shot_results = evaluator.evaluate_few_shot(test_subset, n_shots=2, max_samples=EVAL_SUBSET)

# %% [markdown]
# ## Quick metrics

# %%
from evaluation.metrics import evaluate_results, print_metrics_summary

print("\n=== ZERO-SHOT METRICS ===")
zs_metrics = evaluate_results(zero_shot_results, output_dir="../results/baseline/zero_shot")
print_metrics_summary(zs_metrics)

print("\n=== FEW-SHOT METRICS ===")
fs_metrics = evaluate_results(few_shot_results, output_dir="../results/baseline/few_shot")
print_metrics_summary(fs_metrics)
