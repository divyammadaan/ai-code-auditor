"""
Prepares v2 training dataset with 3 improvements:
1. Top-10 CWEs only (simpler classification, more samples per class)
2. CWE as first token in output (forces model to predict it immediately)
3. CWE-specific explanations (not generic boilerplate)
4. Balanced classes (cap dominant, oversample rare)

Reads from existing processed JSONL — no raw CSV needed.
"""

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

random.seed(42)

# ── Top-10 CWEs to keep ────────────────────────────────────────────────────
TOP10_CWES = {
    'CWE-119', 'CWE-20',  'CWE-399', 'CWE-264', 'CWE-200',
    'CWE-125', 'CWE-190', 'CWE-416', 'CWE-362', 'CWE-189',
}

# ── CWE-specific explanations ──────────────────────────────────────────────
CWE_EXPLANATIONS = {
    'CWE-119': 'The code performs a buffer operation without proper bounds checking. An attacker can supply input larger than the buffer to overflow it, corrupting adjacent memory, overwriting return addresses, or executing arbitrary code.',
    'CWE-20':  'The code does not properly validate user-supplied input before using it. An attacker can supply malformed, unexpected, or malicious input to trigger crashes, bypass security checks, or cause unintended behavior.',
    'CWE-399': 'The code does not properly manage resources such as memory, file handles, or network connections. Resources are leaked or not released, eventually causing denial of service or resource exhaustion.',
    'CWE-264': 'The code does not properly enforce access control permissions. An attacker can gain unauthorized access to resources, escalate privileges, or bypass security restrictions.',
    'CWE-200': 'The code exposes sensitive information to unauthorized actors through error messages, debug output, or return values. An attacker can use this information to plan further attacks.',
    'CWE-125': 'The code reads data from a memory location beyond the end of the allocated buffer. This out-of-bounds read can expose sensitive memory contents or cause a program crash.',
    'CWE-190': 'The code performs arithmetic that can overflow the integer type. The wrapped-around value is then used in a security-sensitive context such as buffer allocation or array indexing, leading to heap corruption.',
    'CWE-416': 'The code accesses a memory region after it has been freed with free(). The freed memory may be reallocated and contain attacker-controlled data, leading to code execution or information disclosure.',
    'CWE-362': 'The code contains a race condition where multiple threads access shared data without proper synchronization. An attacker can exploit the timing window between check and use to corrupt state or bypass security checks.',
    'CWE-189': 'The code contains a numeric error such as integer truncation, sign conversion, or wraparound. The resulting incorrect value is used in a security-sensitive operation like memory allocation or array access.',
}

SYSTEM_PROMPT = (
    "You are an expert security code auditor. "
    "Analyze C/C++ code for vulnerabilities, classify them using CWE, "
    "and rewrite the code securely."
)


def severity_label(cvss):
    try:
        s = float(cvss)
        return 'CRITICAL' if s >= 9 else 'HIGH' if s >= 7 else 'MEDIUM' if s >= 4 else 'LOW'
    except:
        return 'UNKNOWN'


def diff_summary(vuln, secure):
    v = set(vuln.splitlines())
    s = set(secure.splitlines())
    removed = [l.strip() for l in (v - s) if l.strip()][:2]
    added   = [l.strip() for l in (s - v) if l.strip()][:2]
    parts = []
    if removed: parts.append('Removed: ' + '; '.join(removed))
    if added:   parts.append('Added: '   + '; '.join(added))
    return ' | '.join(parts) if parts else 'Refactored for safety.'


def reformat(r):
    cwe  = r['cwe']
    cve  = r.get('cve_id', 'N/A')
    cvss = r.get('cvss_score', 'N/A')
    sev  = severity_label(cvss)
    vuln = r['vulnerable_code']
    sec  = r['secure_code']
    expl = CWE_EXPLANATIONS[cwe]
    diff = diff_summary(vuln, sec)

    user = (
        f'Analyze the following C/C++ code and identify the security vulnerability.\n\n'
        f'```c\n{vuln}\n```\n\n'
        f'Respond with the CWE type first, then explain and provide a secure rewrite.'
    )

    # CWE is ALWAYS the first line — critical for classification accuracy
    assistant = (
        f'CWE: {cwe}\n'
        f'CVE: {cve}\n'
        f'Severity: {cvss} ({sev})\n\n'
        f'Reason: {expl}\n\n'
        f'Fix:\n```c\n{sec}\n```\n\n'
        f'Changes: {diff}'
    )

    full_text = (
        f'<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n'
        f'{user} [/INST] {assistant} </s>'
    )

    return {**r, 'prompt': user, 'completion': assistant, 'text': full_text}


def balance(records, max_per=350, min_per=50):
    by_cwe = defaultdict(list)
    for r in records:
        by_cwe[r['cwe']].append(r)

    out = []
    for cwe, samples in by_cwe.items():
        if len(samples) > max_per:
            out.extend(random.sample(samples, max_per))
        elif len(samples) < min_per:
            over = samples * (min_per // len(samples) + 1)
            out.extend(over[:min_per])
        else:
            out.extend(samples)

    random.shuffle(out)
    return out


def process_split(path, is_train=False):
    with open(path, encoding='utf-8') as f:
        records = [json.loads(l) for l in f]

    # Filter to top-10 CWEs only
    records = [r for r in records if r['cwe'] in TOP10_CWES]

    # Reformat with new prompt structure
    records = [reformat(r) for r in records]

    # Token budget filter (train only)
    if is_train:
        records = [r for r in records if len(r['text']) <= 3200]
        records = balance(records)

    return records


# ── Process all splits ─────────────────────────────────────────────────────
print('Processing splits...')
train = process_split('data/processed/train.jsonl', is_train=True)
val   = process_split('data/processed/val.jsonl')
test  = process_split('data/processed/test.jsonl')

# ── Save v2 dataset ────────────────────────────────────────────────────────
out_dir = Path('data/processed_v2')
out_dir.mkdir(exist_ok=True)

for split, records in [('train', train), ('val', val), ('test', test)]:
    path = out_dir / f'{split}.jsonl'
    with open(path, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'Saved {split}: {len(records)} samples → {path}')

# ── Stats ──────────────────────────────────────────────────────────────────
print()
print('='*55)
print('V2 DATASET SUMMARY')
print('='*55)
print(f'Train: {len(train)} | Val: {len(val)} | Test: {len(test)}')
print()
print('Train CWE distribution:')
dist = Counter(r['cwe'] for r in train)
for cwe, count in sorted(dist.items(), key=lambda x: -x[1]):
    print(f'  {cwe}: {count}')
print()
print('Sample completion (first 300 chars):')
print(train[0]['completion'][:300])
print()
print('V1 vs V2 comparison:')
print(f'  V1: 39 CWEs, 3,162 train samples, generic explanations')
print(f'  V2: 10 CWEs, {len(train)} train samples, CWE-specific explanations, CWE-first format')
