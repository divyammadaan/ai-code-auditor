"""
Baseline evaluation: compare zero-shot and few-shot prompting
against the fine-tuned model.

This establishes the performance floor and demonstrates the value
of fine-tuning (requirement iii: Baseline Comparison).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from tqdm import tqdm

from models.inference import AuditResult, CodeAuditorModel


# ---------------------------------------------------------------------------
# Few-shot examples (manually curated, not from test set)
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = [
    {
        "code": """void copy_data(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // No bounds check
    process(buffer);
}""",
        "audit": """## Security Audit Report
**Vulnerability Detected:** CWE-787 (Out-of-bounds Write)
**Severity:** Critical

### Explanation
The `strcpy` function copies `input` into a fixed 64-byte buffer without checking the input length. An attacker can supply input longer than 64 bytes to overflow the buffer, potentially overwriting return addresses and executing arbitrary code.

### Secure Rewrite
```c
void copy_data(const char *input) {
    char buffer[64];
    if (input == NULL) return;
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\\0';
    process(buffer);
}
```

### Fix Summary
Replaced `strcpy` with `strncpy` and added NULL check and explicit null-termination.""",
    },
    {
        "code": """def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)""",
        "audit": """## Security Audit Report
**Vulnerability Detected:** CWE-89 (SQL Injection)
**Severity:** Critical

### Explanation
String concatenation to build SQL queries allows an attacker to inject arbitrary SQL. For example, `user_id = "1 OR 1=1"` would return all users.

### Secure Rewrite
```python
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    return db.execute(query, (user_id,))
```

### Fix Summary
Replaced string concatenation with a parameterized query.""",
    },
]


def build_zero_shot_prompt(code_snippet: str, style_guide: str) -> str:
    """Zero-shot prompt: no examples, just instructions."""
    return f"""{style_guide}

Analyze the following code snippet for security vulnerabilities:

```
{code_snippet}
```

Provide:
1. Vulnerability type (CWE ID and name)
2. Severity (Critical/High/Medium/Low)
3. Explanation of the vulnerability
4. Secure rewrite following the style guide"""


def build_few_shot_prompt(code_snippet: str, style_guide: str, n_shots: int = 2) -> str:
    """Few-shot prompt: include n example audits before the target."""
    examples_text = ""
    for i, ex in enumerate(FEW_SHOT_EXAMPLES[:n_shots], 1):
        examples_text += f"\n### Example {i}\n\nCode:\n```\n{ex['code']}\n```\n\nAudit:\n{ex['audit']}\n\n---\n"

    return f"""{style_guide}

You are an expert security code auditor. Here are some examples of security audits:
{examples_text}

Now audit the following code:

```
{code_snippet}
```

Provide:
1. Vulnerability type (CWE ID and name)
2. Severity (Critical/High/Medium/Low)
3. Explanation of the vulnerability
4. Secure rewrite following the style guide"""


# ---------------------------------------------------------------------------
# Baseline runner
# ---------------------------------------------------------------------------

class BaselineEvaluator:
    """
    Runs zero-shot and few-shot baselines on the test set.
    Results are saved for comparison with the fine-tuned model.
    """

    def __init__(
        self,
        model: CodeAuditorModel,
        style_guide: str,
        output_dir: str = "./results/baseline",
    ):
        self.model = model
        self.style_guide = style_guide
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_zero_shot(
        self, test_records: list[dict], max_samples: Optional[int] = None
    ) -> list[dict]:
        """Run zero-shot evaluation on test records."""
        return self._run_eval(
            test_records,
            prompt_fn=lambda code: build_zero_shot_prompt(code, self.style_guide),
            mode="zero_shot",
            max_samples=max_samples,
        )

    def evaluate_few_shot(
        self, test_records: list[dict], n_shots: int = 2, max_samples: Optional[int] = None
    ) -> list[dict]:
        """Run few-shot evaluation on test records."""
        return self._run_eval(
            test_records,
            prompt_fn=lambda code: build_few_shot_prompt(code, self.style_guide, n_shots),
            mode=f"few_shot_{n_shots}",
            max_samples=max_samples,
        )

    def _run_eval(
        self,
        test_records: list[dict],
        prompt_fn,
        mode: str,
        max_samples: Optional[int],
    ) -> list[dict]:
        samples = test_records[:max_samples] if max_samples else test_records
        results = []

        logger.info(f"Running {mode} evaluation on {len(samples)} samples...")

        for record in tqdm(samples, desc=mode):
            code = record["vulnerable_code"]
            prompt = prompt_fn(code)

            # Use the model's pipe directly with the custom prompt
            outputs = self.model.pipe(
                f"<s>[INST] {prompt} [/INST]",
                max_new_tokens=1024,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self.model.tokenizer.eos_token_id,
                return_full_text=False,
            )
            raw_output = outputs[0]["generated_text"].strip()
            parsed = self.model._parse_output(code, raw_output)

            results.append(
                {
                    "mode": mode,
                    "vulnerable_code": code,
                    "ground_truth_cwe": record.get("cwe"),
                    "ground_truth_secure_code": record.get("secure_code"),
                    "predicted_cwe": parsed.cwe_id,
                    "predicted_severity": parsed.severity,
                    "predicted_secure_code": parsed.secure_code,
                    "raw_output": raw_output,
                    "is_vulnerable_pred": parsed.is_vulnerable,
                }
            )

        # Save results
        output_path = self.output_dir / f"{mode}_results.jsonl"
        with open(output_path, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        logger.info(f"Saved {mode} results to {output_path}")

        return results
