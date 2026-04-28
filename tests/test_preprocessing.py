"""
Unit tests for the data preprocessing pipeline.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data.preprocessing import (
    _normalize_cwe,
    clean_dataset,
    format_prompt,
    save_jsonl,
    split_dataset,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Minimal Big-Vul-like DataFrame for testing."""
    return pd.DataFrame(
        {
            "vulnerable_code": [
                "void f() { char buf[10]; strcpy(buf, input); }",
                "def q(uid): return db.execute('SELECT * FROM u WHERE id=' + uid)",
                "int* p = malloc(4); free(p); *p = 1;",
                "void g() { int arr[5]; return arr[10]; }",
                "char* gets_input() { char buf[64]; gets(buf); return buf; }",
            ],
            "secure_code": [
                "void f() { char buf[10]; strncpy(buf, input, 9); buf[9]='\\0'; }",
                "def q(uid): return db.execute('SELECT * FROM u WHERE id=%s', (uid,))",
                "int* p = malloc(4); free(p); p = NULL;",
                "void g() { int arr[5]; if(i<5) return arr[i]; }",
                "char* gets_input() { char buf[64]; fgets(buf, 64, stdin); return buf; }",
            ],
            "cwe": ["CWE-787", "CWE-89", "CWE-416", "CWE-125", "CWE-119"],
            "is_vulnerable": [1, 1, 1, 1, 1],
            "cve_id": ["CVE-2021-001", "CVE-2021-002", "CVE-2021-003", "CVE-2021-004", "CVE-2021-005"],
            "cvss_score": [9.8, 9.8, 8.1, 7.5, 7.5],
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNormalizeCwe:
    def test_standard_format(self):
        assert _normalize_cwe("CWE-787") == "CWE-787"

    def test_numeric_only(self):
        assert _normalize_cwe("787") == "CWE-787"

    def test_no_dash(self):
        assert _normalize_cwe("CWE787") == "CWE-787"

    def test_none_input(self):
        assert _normalize_cwe(None) is None

    def test_nan_input(self):
        import numpy as np
        assert _normalize_cwe(np.nan) is None

    def test_no_number(self):
        assert _normalize_cwe("unknown") is None


class TestCleanDataset:
    def test_removes_non_vulnerable(self, sample_df):
        df = sample_df.copy()
        df.loc[0, "is_vulnerable"] = 0
        cleaned = clean_dataset(df, min_cwe_samples=1)
        assert len(cleaned) == 4

    def test_removes_nulls(self, sample_df):
        df = sample_df.copy()
        df.loc[0, "vulnerable_code"] = None
        cleaned = clean_dataset(df, min_cwe_samples=1)
        assert len(cleaned) == 4

    def test_deduplication(self, sample_df):
        df = pd.concat([sample_df, sample_df.iloc[:1]], ignore_index=True)
        cleaned = clean_dataset(df, min_cwe_samples=1)
        assert len(cleaned) == 5  # Duplicate removed

    def test_min_cwe_samples_filter(self, sample_df):
        # With min_cwe_samples=2, all CWEs (each with 1 sample) should be dropped
        cleaned = clean_dataset(sample_df, min_cwe_samples=2)
        assert len(cleaned) == 0

    def test_preserves_all_with_low_threshold(self, sample_df):
        cleaned = clean_dataset(sample_df, min_cwe_samples=1)
        assert len(cleaned) == 5


class TestSplitDataset:
    def test_split_ratios(self, sample_df):
        # Need enough samples per CWE for stratified split
        # Duplicate to have 3 per CWE
        df = pd.concat([sample_df] * 3, ignore_index=True)
        df = clean_dataset(df, min_cwe_samples=1)
        train, val, test = split_dataset(df, 0.6, 0.2, 0.2, random_seed=42)
        total = len(train) + len(val) + len(test)
        assert total == len(df)
        assert len(train) > len(val)
        assert len(train) > len(test)

    def test_no_overlap(self, sample_df):
        df = pd.concat([sample_df] * 4, ignore_index=True)
        df = clean_dataset(df, min_cwe_samples=1)
        train, val, test = split_dataset(df, 0.6, 0.2, 0.2, random_seed=42)
        train_idx = set(train.index)
        val_idx = set(val.index)
        test_idx = set(test.index)
        assert len(train_idx & val_idx) == 0
        assert len(train_idx & test_idx) == 0
        assert len(val_idx & test_idx) == 0


class TestFormatPrompt:
    def test_output_keys(self, sample_df):
        row = sample_df.iloc[0]
        result = format_prompt(row)
        assert "prompt" in result
        assert "completion" in result
        assert "text" in result
        assert "cwe" in result
        assert "vulnerable_code" in result
        assert "secure_code" in result

    def test_cwe_in_completion(self, sample_df):
        row = sample_df.iloc[0]
        result = format_prompt(row)
        assert "CWE-787" in result["completion"]

    def test_code_in_prompt(self, sample_df):
        row = sample_df.iloc[0]
        result = format_prompt(row)
        assert "strcpy" in result["prompt"]

    def test_llama_format_in_text(self, sample_df):
        row = sample_df.iloc[0]
        result = format_prompt(row)
        assert "[INST]" in result["text"]
        assert "[/INST]" in result["text"]


class TestSaveJsonl:
    def test_saves_and_loads(self, sample_df):
        records = [format_prompt(row) for _, row in sample_df.iterrows()]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            save_jsonl(records, path)
            assert path.exists()
            loaded = []
            with open(path) as f:
                for line in f:
                    loaded.append(json.loads(line))
            assert len(loaded) == len(records)
            assert loaded[0]["cwe"] == records[0]["cwe"]
