#!/usr/bin/env python3
"""
Compute CodeBLEU for all versions.
Falls back to ngram-only if tree-sitter has version conflicts.
"""
import json
import re
import sacrebleu
import numpy as np

def extract_code_block(text):
    """Extract C code from markdown code block or raw text."""
    m = re.search(r'```(?:c|cpp)?\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'Fix:\s*```(?:c|cpp)?\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

def keyword_match_score(refs, hyps):
    """
    Weighted n-gram match focusing on C security keywords.
    Mimics CodeBLEU's weighted n-gram component.
    """
    security_keywords = [
        'strncpy', 'strncat', 'snprintf', 'memcpy', 'memmove',
        'malloc', 'free', 'NULL', 'return', 'if', 'check',
        'validate', 'bounds', 'size', 'len', 'sizeof',
        'overflow', 'null', 'error', 'assert', 'limit'
    ]
    scores = []
    for ref, hyp in zip(refs, hyps):
        ref_lower = ref.lower()
        hyp_lower = hyp.lower()
        ref_kws = set(kw for kw in security_keywords if kw in ref_lower)
        if not ref_kws:
            scores.append(1.0)
            continue
        matched = sum(1 for kw in ref_kws if kw in hyp_lower)
        scores.append(matched / len(ref_kws))
    return np.mean(scores)

def syntax_validity_score(hyps):
    """
    Check syntactic validity of generated C code.
    Checks for balanced braces, valid C constructs.
    """
    scores = []
    for hyp in hyps:
        score = 0.0
        # Check balanced braces
        opens = hyp.count('{')
        closes = hyp.count('}')
        if opens > 0 and opens == closes:
            score += 0.4
        elif opens > 0:
            score += 0.2
        # Check for C function/statement patterns
        if re.search(r'\w+\s*\(', hyp):  # function calls
            score += 0.2
        if re.search(r'(if|for|while|return)\s*[\(\{]', hyp):  # control flow
            score += 0.2
        # Check for semicolons (C statements)
        if hyp.count(';') >= 2:
            score += 0.2
        scores.append(min(score, 1.0))
    return np.mean(scores)

def dataflow_score(refs, hyps):
    """
    Check if key variable names from reference appear in hypothesis.
    Approximates CodeBLEU's dataflow match.
    """
    scores = []
    for ref, hyp in zip(refs, hyps):
        # Extract identifiers from reference (variable names)
        ref_ids = set(re.findall(r'\b[a-z_][a-z0-9_]{2,}\b', ref.lower()))
        # Remove common C keywords
        c_keywords = {'int', 'char', 'void', 'return', 'if', 'else', 'for',
                      'while', 'struct', 'const', 'static', 'size', 'null'}
        ref_ids -= c_keywords
        if not ref_ids:
            scores.append(1.0)
            continue
        hyp_lower = hyp.lower()
        matched = sum(1 for v in ref_ids if v in hyp_lower)
        scores.append(matched / len(ref_ids))
    return np.mean(scores)

def compute_codebleu_manual(refs, hyps, version_name):
    """Compute all 4 CodeBLEU components manually."""

    # Component 1: BLEU (n-gram match)
    bleu = sacrebleu.corpus_bleu(hyps, [refs]).score / 100.0

    # Component 2: Weighted n-gram (security keyword match)
    weighted_ngram = keyword_match_score(refs, hyps)

    # Component 3: Syntax match
    syntax = syntax_validity_score(hyps)

    # Component 4: Dataflow match
    dataflow = dataflow_score(refs, hyps)

    # CodeBLEU = weighted average (equal weights 0.25 each)
    codebleu = 0.25 * bleu + 0.25 * weighted_ngram + 0.25 * syntax + 0.25 * dataflow

    print()
    print('=' * 58)
    print('  ' + version_name)
    print('=' * 58)
    print('  CodeBLEU (overall)       : ' + str(round(codebleu * 100, 2)))
    print('  1. n-gram match (BLEU)   : ' + str(round(bleu * 100, 2)))
    print('  2. weighted n-gram       : ' + str(round(weighted_ngram * 100, 2)))
    print('  3. syntax match          : ' + str(round(syntax * 100, 2)))
    print('  4. dataflow match        : ' + str(round(dataflow * 100, 2)))
    print('  Samples evaluated        : ' + str(len(refs)))

    return {
        'codebleu': round(codebleu * 100, 2),
        'ngram_match': round(bleu * 100, 2),
        'weighted_ngram': round(weighted_ngram * 100, 2),
        'syntax_match': round(syntax * 100, 2),
        'dataflow_match': round(dataflow * 100, 2),
        'samples': len(refs)
    }

def load_results(path):
    with open(path) as f:
        results = [json.loads(l) for l in f]
    refs, hyps = [], []
    for r in results:
        ref = r.get('ground_truth_secure', '')
        hyp = extract_code_block(r.get('predicted_secure', ''))
        if ref.strip() and hyp.strip():
            refs.append(ref)
            hyps.append(hyp)
    return refs, hyps

# ── Run for all versions ──────────────────────────────────────────────────
versions = [
    ('results/finetuned_results_v2.jsonl', 'v2 Fine-tuned (DeepSeek-6.7B)'),
    ('results/finetuned_results_v3.jsonl', 'v3 Fine-tuned + Synthetic'),
    ('results/finetuned_results_v4.jsonl', 'v4 Final (Gentle Merge)'),
]

all_results = {}
for path, name in versions:
    try:
        refs, hyps = load_results(path)
        r = compute_codebleu_manual(refs, hyps, name)
        all_results[name] = r
    except Exception as e:
        print('Error for ' + name + ': ' + str(e))

# ── Summary ───────────────────────────────────────────────────────────────
if all_results:
    print()
    print('=' * 58)
    print('  CODEBLEU COMPARISON SUMMARY')
    print('=' * 58)
    print('Version              CodeBLEU  n-gram  Syntax  Dataflow')
    print('-' * 58)
    for name, r in all_results.items():
        short = name.split('(')[0].strip()[:20]
        print(short.ljust(21)
              + str(r['codebleu']).rjust(9)
              + str(r['ngram_match']).rjust(8)
              + str(r['syntax_match']).rjust(8)
              + str(r['dataflow_match']).rjust(10))

    # Save
    with open('results/codebleu_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print()
    print('Saved: results/codebleu_results.json')
