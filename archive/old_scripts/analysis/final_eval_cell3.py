from tqdm import tqdm
import json, re, torch

def build_prompt(code):
    sys = 'You are an expert security code auditor. Analyze C/C++ code for vulnerabilities, classify them using CWE, and rewrite the code securely.'
    return '<s>[INST] <<SYS>>\n' + sys + '\n<</SYS>>\n\nAnalyze the following C/C++ code and identify the security vulnerability.\n\n```c\n' + code + '\n```\n\nRespond with the CWE type first, then explain and provide a secure rewrite. [/INST] CWE:'

def extract_cwe(text):
    m = re.search(r'CWE-\d+', text)
    return m.group(0) if m else 'Unknown'

print('Running inference...')
results = []
for i, record in enumerate(tqdm(test_records)):
    inputs = tokenizer(build_prompt(record['vulnerable_code']), return_tensors='pt', truncation=True, max_length=450).to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=150, do_sample=False, repetition_penalty=1.1, eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.eos_token_id)
    raw = tokenizer.decode(out[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    results.append({'sample_id': i, 'ground_truth_cwe': record['cwe'], 'predicted_cwe': extract_cwe(raw), 'ground_truth_secure': record['secure_code'], 'predicted_secure': raw, 'raw_output': raw, 'vulnerable_code': record['vulnerable_code']})

with open('/kaggle/working/finetuned_results_v2_final.jsonl', 'w') as f:
    for r in results:
        f.write(json.dumps(r) + '\n')

correct = sum(1 for r in results if r['ground_truth_cwe'] == r['predicted_cwe'])
unknown = sum(1 for r in results if r['predicted_cwe'] == 'Unknown')
print(f'CWE Accuracy: {correct}/100 = {correct}%')
print(f'Unknown: {unknown}')
print()
for r in results[:3]:
    print(f'GT: {r["ground_truth_cwe"]} | Pred: {r["predicted_cwe"]} | Raw: {r["raw_output"][:60]}')
