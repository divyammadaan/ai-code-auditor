import json, re

with open('results/finetuned_results.jsonl', encoding='utf-8') as f:
    results = [json.loads(l) for l in f]

unknown = [r for r in results if r['predicted_cwe'] == 'Unknown']
print(f'Unknown predictions: {len(unknown)} / {len(results)}')
print()

for i, r in enumerate(unknown[:8]):
    raw = r['raw_output']
    m1 = re.search(r'CWE-\d+', raw)
    m2 = re.search(r'\*\*Vulnerability:\*\*\s*(.+)', raw)
    print(f"Sample {i+1} | GT: {r['ground_truth_cwe']}")
    print(f"  CWE-\\d+ found: {m1.group() if m1 else 'NONE'}")
    print(f"  Vulnerability line: {m2.group(1)[:60] if m2 else 'NONE'}")
    print(f"  Raw (first 150): {raw[:150]}")
    print()
