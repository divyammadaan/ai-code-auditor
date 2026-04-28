"""
Qualitative and error analysis for the AI Code Auditor.

Covers requirement vi: Qualitative and error analysis including
hallucination and failure cases.

Analysis types:
  1. Hallucination detection — rewrites that introduce NEW vulnerabilities
  2. False negative analysis — missed vulnerabilities
  3. False positive analysis — flagging secure code as vulnerable
  4. CWE misclassification patterns
  5. Failure case categorization
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Hallucination detection
# ---------------------------------------------------------------------------

# Patterns that indicate a potential vulnerability in code
VULNERABILITY_INDICATORS = {
    "buffer_overflow": [
        r"\bstrcpy\s*\(",
        r"\bstrcat\s*\(",
        r"\bsprintf\s*\(",
        r"\bgets\s*\(",
        r"\bscanf\s*\(%s",
    ],
    "sql_injection": [
        r'["\'].*\+.*user',
        r'["\'].*\+.*input',
        r'f["\'].*SELECT.*{',
        r'f["\'].*INSERT.*{',
    ],
    "null_dereference": [
        r"->.*without.*null",
        r"\*ptr.*without.*check",
    ],
    "hardcoded_secrets": [
        r'password\s*=\s*["\'][^"\']{4,}["\']',
        r'secret\s*=\s*["\'][^"\']{4,}["\']',
        r'api_key\s*=\s*["\'][^"\']{4,}["\']',
    ],
    "use_after_free": [
        r"free\s*\(.*\).*\n.*\1",  # free then use same pointer
    ],
}


def detect_vulnerabilities_in_code(code: str) -> dict[str, list[str]]:
    """
    Heuristic scan for vulnerability patterns in a code snippet.
    Returns a dict of {vulnerability_type: [matched_patterns]}.
    """
    found = defaultdict(list)
    for vuln_type, patterns in VULNERABILITY_INDICATORS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                found[vuln_type].append(pattern)
    return dict(found)


def is_hallucinated_rewrite(
    original_code: str, rewritten_code: str
) -> tuple[bool, list[str]]:
    """
    Check if the rewritten code introduces NEW vulnerabilities
    that were not present in the original.

    Returns (is_hallucinated, list_of_new_vulnerability_types).
    """
    if not rewritten_code:
        return False, []

    original_vulns = set(detect_vulnerabilities_in_code(original_code).keys())
    rewrite_vulns = set(detect_vulnerabilities_in_code(rewritten_code).keys())

    new_vulns = rewrite_vulns - original_vulns
    return len(new_vulns) > 0, list(new_vulns)


# ---------------------------------------------------------------------------
# Error categorization
# ---------------------------------------------------------------------------

@dataclass
class ErrorCase:
    """A single failure case with categorization."""
    sample_id: int
    error_type: str
    description: str
    vulnerable_code: str
    ground_truth_cwe: Optional[str]
    predicted_cwe: Optional[str]
    ground_truth_secure: Optional[str]
    predicted_secure: Optional[str]
    raw_output: str
    severity: str = "unknown"
    tags: list[str] = field(default_factory=list)


ERROR_TYPES = {
    "missed_vulnerability": "Model failed to detect a real vulnerability (false negative)",
    "false_alarm": "Model flagged secure code as vulnerable (false positive)",
    "wrong_cwe": "Vulnerability detected but CWE misclassified",
    "poor_rewrite": "Vulnerability detected but secure rewrite is inadequate",
    "hallucinated_rewrite": "Secure rewrite introduces new vulnerabilities",
    "incomplete_output": "Model output is truncated or malformed",
    "wrong_severity": "Severity level incorrectly assessed",
}


def categorize_errors(results: list[dict]) -> list[ErrorCase]:
    """
    Categorize prediction errors into failure types.
    """
    error_cases = []

    for i, r in enumerate(results):
        errors = []

        # Missed vulnerability (false negative)
        if not r.get("is_vulnerable_pred", True):
            errors.append("missed_vulnerability")

        # Wrong CWE
        gt_cwe = r.get("ground_truth_cwe")
        pred_cwe = r.get("predicted_cwe")
        if gt_cwe and pred_cwe and gt_cwe != pred_cwe:
            errors.append("wrong_cwe")

        # Hallucinated rewrite
        orig = r.get("vulnerable_code", "")
        rewrite = r.get("predicted_secure_code", "")
        if rewrite:
            is_halluc, new_vulns = is_hallucinated_rewrite(orig, rewrite)
            if is_halluc:
                errors.append("hallucinated_rewrite")

        # Incomplete output
        raw = r.get("raw_output", "")
        if len(raw) < 50 or not rewrite:
            errors.append("incomplete_output")

        for error_type in errors:
            error_cases.append(
                ErrorCase(
                    sample_id=i,
                    error_type=error_type,
                    description=ERROR_TYPES.get(error_type, "Unknown error"),
                    vulnerable_code=orig,
                    ground_truth_cwe=gt_cwe,
                    predicted_cwe=pred_cwe,
                    ground_truth_secure=r.get("ground_truth_secure_code"),
                    predicted_secure=rewrite,
                    raw_output=raw,
                    tags=[error_type],
                )
            )

    return error_cases


# ---------------------------------------------------------------------------
# Hallucination rate
# ---------------------------------------------------------------------------

def compute_hallucination_rate(results: list[dict]) -> dict:
    """
    Compute the hallucination rate across all predictions.

    Hallucination = secure rewrite introduces a new vulnerability type.
    """
    total_with_rewrite = 0
    hallucinated = 0
    hallucination_types = Counter()

    for r in results:
        orig = r.get("vulnerable_code", "")
        rewrite = r.get("predicted_secure_code", "")
        if not rewrite:
            continue

        total_with_rewrite += 1
        is_halluc, new_vulns = is_hallucinated_rewrite(orig, rewrite)
        if is_halluc:
            hallucinated += 1
            hallucination_types.update(new_vulns)

    rate = hallucinated / total_with_rewrite if total_with_rewrite > 0 else 0.0

    return {
        "hallucination_rate": rate,
        "hallucinated_count": hallucinated,
        "total_with_rewrite": total_with_rewrite,
        "hallucination_types": dict(hallucination_types),
    }


# ---------------------------------------------------------------------------
# Full qualitative analysis report
# ---------------------------------------------------------------------------

def run_qualitative_analysis(
    results: list[dict],
    output_dir: str = "./results",
    model_name: str = "model",
) -> dict:
    """
    Run full qualitative analysis and save a report.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Error categorization
    error_cases = categorize_errors(results)
    error_type_counts = Counter(e.error_type for e in error_cases)

    # Hallucination analysis
    hallucination_stats = compute_hallucination_rate(results)

    # CWE misclassification patterns
    cwe_confusion = defaultdict(Counter)
    for r in results:
        gt = r.get("ground_truth_cwe")
        pred = r.get("predicted_cwe")
        if gt and pred and gt != pred:
            cwe_confusion[gt][pred] += 1

    # Most common failure cases
    top_errors = error_type_counts.most_common()

    report = {
        "model": model_name,
        "total_samples": len(results),
        "error_summary": dict(top_errors),
        "hallucination": hallucination_stats,
        "cwe_confusion_top": {
            k: dict(v.most_common(3)) for k, v in list(cwe_confusion.items())[:10]
        },
        "sample_failure_cases": [
            {
                "sample_id": e.sample_id,
                "error_type": e.error_type,
                "ground_truth_cwe": e.ground_truth_cwe,
                "predicted_cwe": e.predicted_cwe,
                "code_snippet": e.vulnerable_code[:200] + "...",
            }
            for e in error_cases[:20]  # Top 20 failure cases
        ],
    }

    # Save report
    report_path = output_path / f"{model_name}_qualitative_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Qualitative report saved to {report_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"QUALITATIVE ANALYSIS: {model_name}")
    print(f"{'='*60}")
    print(f"Total samples: {len(results)}")
    print(f"\nError breakdown:")
    for error_type, count in top_errors:
        pct = count / len(results) * 100
        print(f"  {error_type:<30} {count:>4} ({pct:.1f}%)")
    print(f"\nHallucination rate: {hallucination_stats['hallucination_rate']:.1%}")
    print(f"  ({hallucination_stats['hallucinated_count']} / "
          f"{hallucination_stats['total_with_rewrite']} rewrites)")
    print(f"{'='*60}\n")

    return report
