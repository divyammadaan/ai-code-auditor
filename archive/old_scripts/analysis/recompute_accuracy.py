"""
Recomputes CWE accuracy with improved extraction logic.
Handles cases where model outputs code instead of a report.
"""
import json, re
from collections import Counter

def extract_cwe_improved(raw_output):
    """Try multiple patterns to extract CWE from model output."""
    if not raw_output:
        return 'Unknown'

    # Pattern 1: **Vulnerability:** CWE-119
    m = re.search(r'\*\*Vulnerability:\*\*\s*(CWE-\d+)', raw_output)
    if m: return m.group(1)

    # Pattern 2: bare CWE-119 anywhere
    m = re.search(r'\bCWE-(\d+)\b', raw_output)
    if m: return f'CWE-{m.group(1)}'

    # Pattern 3: "CWE 119" with space
    m = re.search(r'\bCWE\s+(\d+)\b', raw_output, re.IGNORECASE)
    if m: return f'CWE-{m.group(1)}'

    # Pattern 4: "cwe119" no separator
    m = re.search(r'\bcwe(\d+)\b', raw_output, re.IGNORECASE)
    if m: return f'CWE-{m.group(1)}'

    return 'Unknown'

# Load results
with open('results/finetuned_results.jsonl', encoding='utf-8') as f:
    ft_results = [json.loads(l) for l in f]

with open('results/baseline_results.jsonl', encoding='utf-8') as f:
    bl_results = [json.loads(l) for l in f]

# Recompute with improved extraction
ft_improved = 0
bl_improved = 0
ft_unknown_before = 0
ft_unknown_after  = 0

for r in ft_results:
    old_pred = r['predicted_cwe']
    new_pred = extract_cwe_improved(r['raw_output'])

    if old_pred == 'Unknown': ft_unknown_before += 1
    if new_pred == 'Unknown': ft_unknown_after  += 1

    if new_pred == r['ground_truth_cwe']:
        ft_improved += 1

for r in bl_results:
    new_pred = extract_cwe_improved(r['raw_output'])
    if new_pred == r['ground_truth_cwe']:
        bl_improved += 1

n = len(ft_results)
print('='*55)
print('RECOMPUTED CWE ACCURACY')
print('='*55)
print(f'Baseline  (original) : {sum(1 for r in bl_results if r["predicted_cwe"]==r["ground_truth_cwe"])}/{n} = {sum(1 for r in bl_results if r["predicted_cwe"]==r["ground_truth_cwe"])/n*100:.1f}%')
print(f'Baseline  (improved) : {bl_improved}/{n} = {bl_improved/n*100:.1f}%')
print()
print(f'Fine-tuned (original): {sum(1 for r in ft_results if r["predicted_cwe"]==r["ground_truth_cwe"])}/{n} = {sum(1 for r in ft_results if r["predicted_cwe"]==r["ground_truth_cwe"])/n*100:.1f}%')
print(f'Fine-tuned (improved): {ft_improved}/{n} = {ft_improved/n*100:.1f}%')
print()
print(f'Unknown reduced: {ft_unknown_before} → {ft_unknown_after}')
print()

# Show what the 24 unknown cases actually contain now
print('Previously Unknown — now resolved:')
resolved = 0
for r in ft_results:
    old = r['predicted_cwe']
    new = extract_cwe_improved(r['raw_output'])
    if old == 'Unknown' and new != 'Unknown':
        resolved += 1
        correct = '✓' if new == r['ground_truth_cwe'] else '✗'
        print(f'  GT: {r["ground_truth_cwe"]} | New pred: {new} {correct}')
print(f'\nResolved {resolved} previously Unknown predictions')
