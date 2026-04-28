"""
Unit tests for evaluation metrics.
"""

import pytest

from evaluation.metrics import (
    compute_bleu,
    compute_cwe_accuracy,
    compute_detection_metrics,
    compute_rouge,
    compute_severity_metrics,
)
from evaluation.qualitative import (
    compute_hallucination_rate,
    detect_vulnerabilities_in_code,
    is_hallucinated_rewrite,
)


# ---------------------------------------------------------------------------
# Detection metrics
# ---------------------------------------------------------------------------

class TestDetectionMetrics:
    def test_perfect_predictions(self):
        y_true = [1, 1, 0, 1, 0]
        y_pred = [1, 1, 0, 1, 0]
        metrics = compute_detection_metrics(y_true, y_pred)
        assert metrics["f1"] == pytest.approx(1.0)
        assert metrics["accuracy"] == pytest.approx(1.0)

    def test_all_wrong(self):
        y_true = [1, 1, 1]
        y_pred = [0, 0, 0]
        metrics = compute_detection_metrics(y_true, y_pred)
        assert metrics["recall"] == pytest.approx(0.0)
        assert metrics["f1"] == pytest.approx(0.0)

    def test_all_positive_predictions(self):
        y_true = [1, 0, 1, 0]
        y_pred = [1, 1, 1, 1]
        metrics = compute_detection_metrics(y_true, y_pred)
        assert metrics["recall"] == pytest.approx(1.0)
        assert metrics["precision"] == pytest.approx(0.5)

    def test_returns_required_keys(self):
        metrics = compute_detection_metrics([1], [1])
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics
        assert "accuracy" in metrics


# ---------------------------------------------------------------------------
# CWE classification
# ---------------------------------------------------------------------------

class TestCweAccuracy:
    def test_perfect_classification(self):
        y_true = ["CWE-787", "CWE-89", "CWE-79"]
        y_pred = ["CWE-787", "CWE-89", "CWE-79"]
        metrics = compute_cwe_accuracy(y_true, y_pred)
        assert metrics["top1_accuracy"] == pytest.approx(1.0)

    def test_all_wrong(self):
        y_true = ["CWE-787", "CWE-89"]
        y_pred = ["CWE-79", "CWE-416"]
        metrics = compute_cwe_accuracy(y_true, y_pred)
        assert metrics["top1_accuracy"] == pytest.approx(0.0)

    def test_partial_correct(self):
        y_true = ["CWE-787", "CWE-89", "CWE-79", "CWE-416"]
        y_pred = ["CWE-787", "CWE-89", "CWE-416", "CWE-79"]
        metrics = compute_cwe_accuracy(y_true, y_pred)
        assert metrics["top1_accuracy"] == pytest.approx(0.5)

    def test_empty_input(self):
        metrics = compute_cwe_accuracy([], [])
        assert metrics["top1_accuracy"] == 0.0


# ---------------------------------------------------------------------------
# BLEU / ROUGE
# ---------------------------------------------------------------------------

class TestBleuRouge:
    def test_identical_strings(self):
        refs = ["void safe_copy(char *src) { strncpy(buf, src, 63); }"]
        hyps = ["void safe_copy(char *src) { strncpy(buf, src, 63); }"]
        bleu = compute_bleu(refs, hyps)
        assert bleu["bleu4"] > 90  # sacrebleu returns 0-100

    def test_empty_hypothesis(self):
        refs = ["some reference code"]
        hyps = [""]
        bleu = compute_bleu(refs, hyps)
        assert bleu["bleu4"] == pytest.approx(0.0, abs=1.0)

    def test_rouge_identical(self):
        refs = ["void safe_copy() { strncpy(buf, src, 63); }"]
        hyps = ["void safe_copy() { strncpy(buf, src, 63); }"]
        rouge = compute_rouge(refs, hyps)
        assert rouge["rougeL"] == pytest.approx(1.0)

    def test_rouge_different(self):
        refs = ["int add(int a, int b) { return a + b; }"]
        hyps = ["SELECT * FROM users WHERE id = %s"]
        rouge = compute_rouge(refs, hyps)
        assert rouge["rougeL"] < 0.3


# ---------------------------------------------------------------------------
# Severity metrics
# ---------------------------------------------------------------------------

class TestSeverityMetrics:
    def test_perfect_severity(self):
        y_true = ["Critical", "High", "Medium"]
        y_pred = ["Critical", "High", "Medium"]
        metrics = compute_severity_metrics(y_true, y_pred)
        assert metrics["severity_accuracy"] == pytest.approx(1.0)

    def test_empty_predictions(self):
        metrics = compute_severity_metrics([], [])
        assert metrics["severity_accuracy"] == 0.0

    def test_filters_none_values(self):
        y_true = ["Critical", None, "High"]
        y_pred = ["Critical", None, "Medium"]
        metrics = compute_severity_metrics(y_true, y_pred)
        # Only 2 valid pairs: Critical/Critical (correct), High/Medium (wrong)
        assert metrics["severity_accuracy"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Hallucination detection
# ---------------------------------------------------------------------------

class TestHallucinationDetection:
    def test_detects_strcpy_vulnerability(self):
        code = "void f() { strcpy(buf, input); }"
        vulns = detect_vulnerabilities_in_code(code)
        assert "buffer_overflow" in vulns

    def test_detects_sql_injection(self):
        code = "query = 'SELECT * FROM users WHERE id = ' + user_id"
        vulns = detect_vulnerabilities_in_code(code)
        assert "sql_injection" in vulns

    def test_clean_code_no_vulns(self):
        code = "void f() { strncpy(buf, input, sizeof(buf)-1); buf[sizeof(buf)-1]='\\0'; }"
        vulns = detect_vulnerabilities_in_code(code)
        assert "buffer_overflow" not in vulns

    def test_hallucination_detected(self):
        original = "void f() { int x = 5; return x; }"
        rewrite = "void f() { char buf[10]; strcpy(buf, input); return 0; }"
        is_halluc, new_vulns = is_hallucinated_rewrite(original, rewrite)
        assert is_halluc is True
        assert "buffer_overflow" in new_vulns

    def test_no_hallucination_in_good_rewrite(self):
        original = "void f() { strcpy(buf, input); }"
        rewrite = "void f() { strncpy(buf, input, sizeof(buf)-1); buf[sizeof(buf)-1]='\\0'; }"
        is_halluc, _ = is_hallucinated_rewrite(original, rewrite)
        assert is_halluc is False

    def test_hallucination_rate_zero(self):
        results = [
            {
                "vulnerable_code": "void f() { strcpy(buf, src); }",
                "predicted_secure_code": "void f() { strncpy(buf, src, 63); }",
            }
        ]
        stats = compute_hallucination_rate(results)
        assert stats["hallucination_rate"] == pytest.approx(0.0)

    def test_hallucination_rate_nonzero(self):
        results = [
            {
                "vulnerable_code": "int x = 5;",
                "predicted_secure_code": "void f() { strcpy(buf, input); }",
            }
        ]
        stats = compute_hallucination_rate(results)
        assert stats["hallucination_rate"] > 0
