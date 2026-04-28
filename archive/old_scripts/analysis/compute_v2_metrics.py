"""
Computes all v2 evaluation metrics from downloaded JSONL files.
No GPU needed.
"""
import json
import re
import numpy as np
from collections import Counter
from pathlib import Path

# Load results
with open('results/finetuned_results_v2.jsonl', encoding='utf-8') as f:
    ft = [json.loads(l) for l in f]

with open('results/baseline_results_v2.jsonl', encoding='utf-8') as f:
    bl = [json.loads(l) for l in f]

print(f'Fine-tuned samples : {len(ft)}')
print(f'Baseline samples   : {len(bl)}')

# Check raw output format
print('\nSample fine-tuned outputs:')
for r in ft[:5]:
    print(f'  GT: {r["ground_truth_cwe"]} | Pred: {r["predicted_cwe"]} | Raw: {r["raw_output"][:80]}')

print('\nSample baseline outputs:')
for r in bl[:5]:
    print(f'  GT: {r["ground_truth_cwe"]} | Pred: {r["predicted_cwe"]} | Raw: {r["raw_output"][:80]}')

def compute_metrics(results, name):
    gt   = [r['ground_truth_cwe'] for r in results]
    pred = [r['predicted_cwe']    for r in results]

    # CWE accuracy
    correct = sum(1 for g, p in zip(gt, pred) if g == p)
    unknown = sum(1 for p in pred if p == 'Unknown')
    cwe_acc = correct / len(gt)

    # Valid responses only (not Unknown)
    valid = [(g, p) for g, p in zip(gt, pred) if p != 'Unknown']
    valid_acc = sum(1 for g, p in valid if g == p) / len(valid) if valid else 0

    # ROUGE-L
    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
        refs = [r['ground_truth_secure'] for r in results]
        hyps = [r['predicted_secure'] or '' for r in results]
        rougeL = np.mean([scorer.score(r, h)['rougeL'].fmeasure for r, h in zip(refs, hyps)])
    except Exception as e:
        rougeL = 0.0
        print(f'ROUGE failed: {e}')

    # BLEU
    try:
        import sacrebleu
        refs = [r['ground_truth_secure'] for r in results]
        hyps = [r['predicted_secure'] or '' for r in results]
        bleu = sacrebleu.corpus_bleu(hyps, [refs]).score
    except Exception as e:
        bleu = 0.0
        print(f'BLEU failed: {e}')

    print(f'\n{"="*55}')
    print(f'  {name}')
    print(f'{"="*55}')
    print(f'  BLEU-4              : {bleu:.2f}')
    print(f'  ROUGE-L             : {rougeL:.3f}')
    print(f'  CWE Accuracy (all)  : {cwe_acc:.1%} ({correct}/{len(gt)})')
    print(f'  CWE Accuracy (valid): {valid_acc:.1%} ({sum(1 for g,p in valid if g==p)}/{len(valid)})')
    print(f'  Unknown predictions : {unknown}')
    print(f'\n  Per-CWE accuracy:')
    for cwe, count in Counter(gt).most_common():
        c = sum(1 for g, p in zip(gt, pred) if g == cwe and g == p)
        print(f'    {cwe:<12}: {c}/{count} ({c/count*100:.0f}%)')

    return {
        'bleu4': round(bleu, 2),
        'rougeL': round(rougeL, 3),
        'cwe_accuracy': round(cwe_acc, 3),
        'cwe_accuracy_valid': round(valid_acc, 3),
        'unknown_count': unknown,
        'correct': correct,
        'total': len(gt),
    }

bl_metrics = compute_metrics(bl, 'Baseline (Zero-shot DeepSeek-6.7B)')
ft_metrics = compute_metrics(ft, 'Fine-tuned (QLoRA DeepSeek-6.7B, top-10 CWEs)')

# Save metrics
metrics = {'baseline': bl_metrics, 'finetuned': ft_metrics}
with open('results/evaluation_metrics_v2.json', 'w') as f:
    json.dump(metrics, f, indent=2)
print('\nSaved: results/evaluation_metrics_v2.json')

# Summary comparison
print(f'\n{"="*55}')
print(f'{"FINAL COMPARISON":^55}')
print(f'{"="*55}')
print(f'{"Metric":<30} {"Baseline":>10} {"Fine-tuned":>12}')
print(f'{"-"*55}')
for k, label in [('bleu4','BLEU-4'), ('rougeL','ROUGE-L'),
                  ('cwe_accuracy','CWE Acc (all)'),
                  ('cwe_accuracy_valid','CWE Acc (valid)')]:
    b = bl_metrics[k]
    f = ft_metrics[k]
    delta = f - b
    arrow = '↑' if delta > 0 else '↓' if delta < 0 else '='
    print(f'{label:<30} {b:>10.3f} {f:>12.3f}  {arrow}{abs(delta):.3f}')
print(f'{"="*55}')
