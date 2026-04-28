"""
Data preprocessing pipeline for the Big-Vul dataset.

Big-Vul contains ~265K C/C++ functions labeled with CVE/CWE information.
This module handles:
  - Loading and cleaning the raw CSV
  - Deduplication
  - Stratified train/val/test split by CWE category
  - Prompt formatting for instruction fine-tuning
  - Saving as JSONL files
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml
from loguru import logger
from sklearn.model_selection import train_test_split
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RAW_CSV = Path("./data/raw/MSR_data_cleaned.csv")
PROCESSED_DIR = Path("./data/processed")

SYSTEM_PROMPT = (
    "You are an expert security code auditor. Analyze the provided code snippet, "
    "identify any security vulnerabilities, classify them using CWE, and rewrite "
    "the code into a secure version following the corporate style guide."
)

STYLE_GUIDE = """Corporate Secure Coding Style Guide:
1. Validate and sanitize all external inputs before use.
2. Use parameterized queries for all database operations.
3. Never store sensitive data in plaintext.
4. Apply the principle of least privilege.
5. Use memory-safe functions; avoid strcpy, sprintf, gets.
6. Check all return values from security-critical functions.
7. Use HTTPS/TLS for all network communications.
8. Implement proper error handling without leaking internal details."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_bigvul(csv_path: Path = RAW_CSV) -> pd.DataFrame:
    """
    Load the raw Big-Vul CSV, reading only the columns we need.
    The full CSV is ~10GB; selecting columns upfront cuts memory and load time
    from ~5 minutes to ~30 seconds.
    """
    logger.info(f"Loading Big-Vul dataset from {csv_path}")

    # Only load the columns we actually use — ignore the other 30+
    NEEDED_COLS = ["func_before", "func_after", "vul", "CWE ID", "CVE ID", "Score", "lang"]

    # Peek at headers first to confirm columns exist
    header = pd.read_csv(csv_path, nrows=0)
    available = set(header.columns)
    use_cols = [c for c in NEEDED_COLS if c in available]
    missing = set(NEEDED_COLS) - available
    if missing:
        logger.warning(f"Columns not found (will skip): {missing}")

    df = pd.read_csv(csv_path, usecols=use_cols, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows with columns: {list(df.columns)}")
    return df


def clean_dataset(df: pd.DataFrame, min_cwe_samples: int = 10) -> pd.DataFrame:
    """
    Clean and filter the Big-Vul dataset.

    Steps:
      1. Keep only rows with a valid CWE label (vulnerable functions).
      2. Drop duplicates based on function body.
      3. Remove functions that are too short (< 5 lines) or too long (> 200 lines).
      4. Drop CWE categories with fewer than `min_cwe_samples` examples.
    """
    logger.info("Cleaning dataset...")

    # Actual Big-Vul column names (confirmed from MSR_data_cleaned.csv):
    #   func_before  — vulnerable function body
    #   func_after   — fixed/secure function body
    #   vul          — 1 = vulnerable, 0 = non-vulnerable
    #   CWE ID       — CWE identifier (capitalized with space)
    #   CVE ID       — CVE identifier (capitalized with space)
    #   Score        — CVSS score (capitalized)
    col_map = {
        "func_before": "vulnerable_code",
        "func_after": "secure_code",
        "CWE ID": "cwe",
        "CVE ID": "cve_id",
        "Score": "cvss_score",
        "vul": "is_vulnerable",
    }
    # Only rename columns that exist
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Keep only vulnerable functions that have a secure rewrite
    required_cols = {"vulnerable_code", "secure_code", "cwe", "is_vulnerable"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}\n"
            f"Make sure you downloaded the split-functions CSV (not the raw CVE CSV)."
        )

    df = df[df["is_vulnerable"] == 1].copy()
    logger.info(f"After filtering vulnerable-only: {len(df):,} rows")

    # Drop rows with null code
    df = df.dropna(subset=["vulnerable_code", "secure_code", "cwe"])
    logger.info(f"After dropping nulls: {len(df):,} rows")

    # Deduplicate on vulnerable code body
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["vulnerable_code"])
    logger.info(f"After deduplication: {len(df):,} rows (removed {before_dedup - len(df):,})")

    # Filter by code length (lines)
    df["code_lines"] = df["vulnerable_code"].apply(lambda x: len(str(x).splitlines()))
    df = df[(df["code_lines"] >= 5) & (df["code_lines"] <= 200)]
    logger.info(f"After length filter (5–200 lines): {len(df):,} rows")

    # Normalize CWE format: extract numeric ID, e.g. "CWE-119" -> "CWE-119"
    df["cwe"] = df["cwe"].apply(_normalize_cwe)
    df = df.dropna(subset=["cwe"])

    # Drop rare CWE categories
    cwe_counts = df["cwe"].value_counts()
    valid_cwes = cwe_counts[cwe_counts >= min_cwe_samples].index
    df = df[df["cwe"].isin(valid_cwes)]
    logger.info(
        f"After dropping rare CWEs (< {min_cwe_samples} samples): "
        f"{len(df):,} rows, {df['cwe'].nunique()} unique CWEs"
    )

    return df.reset_index(drop=True)


def _normalize_cwe(cwe_raw: str) -> Optional[str]:
    """Extract and normalize CWE ID from various formats."""
    if pd.isna(cwe_raw):
        return None
    cwe_str = str(cwe_raw).strip()
    # Match patterns like "CWE-119", "119", "CWE119"
    match = re.search(r"(\d+)", cwe_str)
    if match:
        return f"CWE-{match.group(1)}"
    return None


# ---------------------------------------------------------------------------
# CWE-specific explanation templates (Fix 2: discriminative explanations)
# ---------------------------------------------------------------------------

CWE_EXPLANATIONS = {
    "CWE-119": "The code performs a buffer operation without proper bounds checking, allowing writes or reads beyond the allocated memory region. An attacker can overflow the buffer to corrupt adjacent memory, overwrite return addresses, or execute arbitrary code.",
    "CWE-120": "The code uses an unsafe string copy function (strcpy, strcat, gets) that does not check the destination buffer size. An attacker supplying input longer than the buffer can overwrite adjacent memory.",
    "CWE-125": "The code reads data from a memory location beyond the end of the allocated buffer. This out-of-bounds read can expose sensitive memory contents or cause a crash.",
    "CWE-787": "The code writes data past the end of the allocated buffer (out-of-bounds write). An attacker can use this to corrupt memory, overwrite control data, and potentially execute arbitrary code.",
    "CWE-20":  "The code does not properly validate or sanitize user-supplied input before using it. An attacker can supply malformed input to trigger unexpected behavior, bypass security checks, or cause crashes.",
    "CWE-416": "The code accesses a memory region after it has been freed with free(). The freed memory may be reallocated and contain attacker-controlled data, leading to code execution or information disclosure.",
    "CWE-476": "The code dereferences a pointer without checking if it is NULL. If the pointer is NULL, this causes a null pointer dereference, crashing the program or potentially allowing privilege escalation.",
    "CWE-190": "The code performs an arithmetic operation that can overflow the integer type. The wrapped value is then used in a security-sensitive context such as a buffer allocation or array index, leading to heap corruption.",
    "CWE-189": "The code contains a numeric error such as integer truncation, sign conversion, or wraparound. The resulting incorrect value is used in a security-sensitive operation.",
    "CWE-362": "The code contains a race condition where multiple threads access shared data without proper synchronization. An attacker can exploit the timing window to corrupt state or bypass security checks.",
    "CWE-399": "The code does not properly manage resources such as memory, file handles, or network connections. Resources are leaked or not released, leading to denial of service or resource exhaustion.",
    "CWE-264": "The code does not properly enforce access control permissions. An attacker can gain unauthorized access to resources, escalate privileges, or bypass security restrictions.",
    "CWE-200": "The code exposes sensitive information to unauthorized actors through error messages, logs, or return values. An attacker can use this information to plan further attacks.",
    "CWE-284": "The code does not properly control access to a resource. Missing or incorrect authorization checks allow attackers to access or modify resources they should not be able to.",
    "CWE-400": "The code does not limit resource consumption, allowing an attacker to cause excessive CPU, memory, or disk usage, resulting in denial of service.",
    "CWE-415": "The code calls free() on a memory region that has already been freed. This double-free corrupts the heap allocator's internal state and can lead to arbitrary code execution.",
    "CWE-404": "The code does not properly close or release a resource after use. File descriptors, sockets, or memory handles are leaked, eventually exhausting system resources.",
    "CWE-254": "The code has a security feature that is incorrectly implemented or can be bypassed. The protection mechanism does not provide the intended security guarantee.",
    "CWE-310": "The code uses weak or broken cryptographic algorithms, incorrect key sizes, or improper cryptographic practices, making encrypted data vulnerable to attack.",
    "CWE-732": "The code sets incorrect permissions on a resource, allowing unauthorized users to read, write, or execute it.",
    "CWE-22":  "The code constructs a file path using user input without sanitizing path traversal sequences (../, ..). An attacker can access files outside the intended directory.",
    "CWE-59":  "The code follows symbolic links without checking whether the link target is safe. An attacker can create a symlink to redirect file operations to sensitive files.",
    "CWE-79":  "The code includes user-supplied data in web output without proper escaping, allowing attackers to inject malicious scripts that execute in victims' browsers.",
    "CWE-77":  "The code constructs a command string using user input without proper sanitization, allowing attackers to inject additional commands that execute with the application's privileges.",
    "CWE-78":  "The code passes user-supplied input to an OS command without sanitization, allowing attackers to execute arbitrary system commands.",
    "CWE-134": "The code uses a user-controlled format string in a printf-style function. An attacker can use format specifiers to read memory or write to arbitrary addresses.",
    "CWE-285": "The code does not verify that the authenticated user has authorization to perform the requested operation.",
    "CWE-287": "The code contains a flaw in the authentication mechanism that allows an attacker to bypass authentication or impersonate another user.",
    "CWE-311": "The code transmits or stores sensitive data without encryption, exposing it to interception or unauthorized access.",
    "CWE-358": "The code has an implementation weakness that violates the intended security policy in a subtle way.",
    "CWE-369": "The code performs a division operation without checking if the divisor is zero, causing a divide-by-zero crash.",
    "CWE-617": "The code contains an assertion that can be triggered by attacker-controlled input, causing the program to abort.",
    "CWE-704": "The code performs an incorrect type conversion that changes the value or interpretation of data in a security-sensitive context.",
    "CWE-772": "The code acquires a resource but does not release it in all code paths, leading to resource exhaustion.",
    "CWE-835": "The code contains a loop that never terminates under certain conditions, causing the program to hang and consume CPU indefinitely.",
    "CWE-834": "The code contains excessive iteration that can be triggered by attacker input, causing denial of service.",
    "CWE-17":  "The code has a configuration or code generation issue that introduces a security weakness.",
    "CWE-18":  "The code has a source code issue that introduces a security weakness during development.",
    "CWE-19":  "The code has a data handling issue where data is processed incorrectly, leading to security vulnerabilities.",
    "CWE-269": "The code does not properly manage privilege levels, allowing operations to run with more privileges than necessary.",
}

def _get_cwe_explanation(cwe: str) -> str:
    """Return CWE-specific explanation or a generic fallback."""
    return CWE_EXPLANATIONS.get(cwe, f"This code contains a {cwe} vulnerability that allows an attacker to exploit a weakness in the implementation, potentially leading to code execution, data leakage, or denial of service.")


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

def _severity_label(cvss) -> str:
    """Convert CVSS score to human-readable severity label."""
    try:
        score = float(cvss)
        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
    except (ValueError, TypeError):
        return "UNKNOWN"


def _diff_summary(vuln_code: str, secure_code: str) -> str:
    """
    Generate a concise human-readable summary of what changed between
    vulnerable and secure code by comparing line sets.
    """
    vuln_lines  = set(vuln_code.splitlines())
    secure_lines = set(secure_code.splitlines())

    removed = [l.strip() for l in (vuln_lines - secure_lines)  if l.strip()]
    added   = [l.strip() for l in (secure_lines - vuln_lines)  if l.strip()]

    parts = []
    if removed:
        parts.append("Removed: " + "; ".join(removed[:3]))
    if added:
        parts.append("Added: "   + "; ".join(added[:3]))
    return " | ".join(parts) if parts else "Refactored for safety."


def format_prompt(row: pd.Series) -> dict:
    """
    Format a single Big-Vul row into an instruction-following prompt.

    v3 improvements:
    - CWE is the FIRST token in the response (forces model to predict it first)
    - CWE-specific explanations (not generic boilerplate)
    - Instruction-style format for cleaner learning signal
    """
    cwe      = row.get("cwe", "Unknown")
    cve      = row.get("cve_id", "N/A")
    cvss     = row.get("cvss_score", "N/A")
    severity = _severity_label(cvss)
    diff     = _diff_summary(row["vulnerable_code"], row["secure_code"])
    explanation = _get_cwe_explanation(cwe)

    user_message = (
        f"Analyze the following C/C++ code and identify the security vulnerability.\n\n"
        f"```c\n{row['vulnerable_code']}\n```\n\n"
        f"Respond with the CWE type first, then explain the vulnerability and provide a secure rewrite."
    )

    # CWE is ALWAYS the first line — forces model to predict it immediately
    assistant_message = (
        f"CWE: {cwe}\n"
        f"CVE: {cve}\n"
        f"Severity: {cvss} ({severity})\n\n"
        f"Reason: {explanation}\n\n"
        f"Fix:\n"
        f"```c\n{row['secure_code']}\n```\n\n"
        f"Changes: {diff}"
    )

    # Full text for causal LM training
    full_text = (
        f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n"
        f"{user_message} [/INST] {assistant_message} </s>"
    )

    return {
        "prompt": user_message,
        "completion": assistant_message,
        "text": full_text,
        "cwe": cwe,
        "cve_id": cve,
        "cvss_score": str(cvss),
        "vulnerable_code": row["vulnerable_code"],
        "secure_code": row["secure_code"],
    }


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def split_dataset(
    df: pd.DataFrame,
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Stratified split by CWE category to ensure all vulnerability types
    are represented in each split.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1"

    logger.info(f"Splitting dataset: {train_ratio:.0%} train / {val_ratio:.0%} val / {test_ratio:.0%} test")

    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df,
        test_size=(val_ratio + test_ratio),
        stratify=df["cwe"],
        random_state=random_seed,
    )

    # Second split: val vs test
    relative_val = val_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - relative_val),
        stratify=temp_df["cwe"],
        random_state=random_seed,
    )

    logger.info(
        f"Split sizes — Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}"
    )
    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_jsonl(records: list[dict], path: Path) -> None:
    """Save a list of dicts as a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(records):,} records to {path}")


def save_split_stats(train_df, val_df, test_df, output_dir: Path) -> None:
    """Save dataset statistics for reproducibility and reporting."""
    stats = {
        "total_samples": len(train_df) + len(val_df) + len(test_df),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "unique_cwes": int(train_df["cwe"].nunique()),
        "cwe_distribution_train": train_df["cwe"].value_counts().to_dict(),
        "cwe_distribution_val": val_df["cwe"].value_counts().to_dict(),
        "cwe_distribution_test": test_df["cwe"].value_counts().to_dict(),
    }
    stats_path = output_dir / "dataset_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Dataset statistics saved to {stats_path}")


# ---------------------------------------------------------------------------
# Dataset balancing (Fix 3: cap dominant CWEs, oversample rare ones)
# ---------------------------------------------------------------------------

def balance_dataset(
    records: list[dict],
    max_per_cwe: int = 400,
    min_per_cwe: int = 20,
) -> list[dict]:
    """
    Balance the dataset by:
    1. Capping dominant CWEs at max_per_cwe samples
    2. Oversampling rare CWEs to min_per_cwe samples (with repetition)
    """
    import random
    from collections import defaultdict

    random.seed(42)

    # Group by CWE
    by_cwe = defaultdict(list)
    for r in records:
        by_cwe[r["cwe"]].append(r)

    balanced = []
    for cwe, samples in by_cwe.items():
        if len(samples) > max_per_cwe:
            # Cap dominant classes
            balanced.extend(random.sample(samples, max_per_cwe))
        elif len(samples) < min_per_cwe:
            # Oversample rare classes with repetition
            oversampled = samples * (min_per_cwe // len(samples) + 1)
            balanced.extend(oversampled[:min_per_cwe])
        else:
            balanced.extend(samples)

    random.shuffle(balanced)

    # Log distribution
    final_dist = defaultdict(int)
    for r in balanced:
        final_dist[r["cwe"]] += 1
    logger.info("Balanced CWE distribution (top 10):")
    for cwe, count in sorted(final_dist.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"  {cwe}: {count}")

    return balanced


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_preprocessing(config_path: str = "configs/training_config.yaml") -> None:
    """Full preprocessing pipeline: load → clean → split → format → save."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    dataset_cfg = config["dataset"]
    raw_path = Path(dataset_cfg["raw_path"])
    processed_dir = Path(dataset_cfg["processed_path"])

    # Load
    df = load_bigvul(raw_path)

    # Clean
    df = clean_dataset(df, min_cwe_samples=dataset_cfg.get("min_cwe_samples", 10))

    # Split
    train_df, val_df, test_df = split_dataset(
        df,
        train_ratio=dataset_cfg["train_ratio"],
        val_ratio=dataset_cfg["val_ratio"],
        test_ratio=dataset_cfg["test_ratio"],
        random_seed=dataset_cfg["random_seed"],
    )

    # Format prompts
    logger.info("Formatting prompts...")
    train_records = [format_prompt(row) for _, row in tqdm(train_df.iterrows(), total=len(train_df))]
    val_records   = [format_prompt(row) for _, row in tqdm(val_df.iterrows(),   total=len(val_df))]
    test_records  = [format_prompt(row) for _, row in tqdm(test_df.iterrows(),  total=len(test_df))]

    # Filter samples that exceed token budget (800 tokens ≈ 3200 chars)
    # Keeps ~60% of data with clean, complete training signal
    MAX_CHARS = 3200
    before = len(train_records)
    train_records = [r for r in train_records if len(r["text"]) <= MAX_CHARS]
    logger.info(f"Token filter: {before:,} → {len(train_records):,} train samples (removed {before-len(train_records):,} long samples)")

    # Balance dataset: cap dominant CWEs, oversample rare ones
    train_records = balance_dataset(train_records)
    logger.info(f"After balancing: {len(train_records):,} train samples")

    # Save
    save_jsonl(train_records, processed_dir / "train.jsonl")
    save_jsonl(val_records, processed_dir / "val.jsonl")
    save_jsonl(test_records, processed_dir / "test.jsonl")
    save_split_stats(train_df, val_df, test_df, processed_dir)

    logger.success("Preprocessing complete!")


if __name__ == "__main__":
    run_preprocessing()
