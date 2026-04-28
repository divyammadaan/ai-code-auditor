"""
Inference module for the fine-tuned code auditor.

Supports:
  - Loading the base model or LoRA-adapted model
  - Generating audit reports with or without RAG context
  - Structured output parsing
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import torch
from loguru import logger
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from rag.retriever import CodeAuditRetriever
from rag.vectorstore import VectorStore


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

@dataclass
class AuditResult:
    """Structured output from the code auditor."""
    vulnerable_code: str
    is_vulnerable: bool
    cwe_id: Optional[str] = None
    cwe_name: Optional[str] = None
    severity: Optional[str] = None
    explanation: Optional[str] = None
    secure_code: Optional[str] = None
    fix_summary: Optional[str] = None
    raw_output: str = ""
    retrieved_patterns: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_vulnerable": self.is_vulnerable,
            "cwe_id": self.cwe_id,
            "cwe_name": self.cwe_name,
            "severity": self.severity,
            "explanation": self.explanation,
            "secure_code": self.secure_code,
            "fix_summary": self.fix_summary,
        }


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

class CodeAuditorModel:
    """
    Wraps a base or LoRA-fine-tuned model for code security auditing.
    """

    def __init__(
        self,
        base_model_id: str,
        lora_adapter_path: Optional[str] = None,
        device: str = "auto",
        load_in_4bit: bool = True,
        vector_store: Optional[VectorStore] = None,
        n_rag_results: int = 3,
    ):
        self.base_model_id = base_model_id
        self.lora_adapter_path = lora_adapter_path
        self.use_rag = vector_store is not None

        logger.info(f"Loading tokenizer: {base_model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        logger.info(f"Loading model: {base_model_id}")
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=bnb_config,
                device_map=device,
                trust_remote_code=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                device_map=device,
                torch_dtype=torch.float16,
                trust_remote_code=True,
            )

        # Load LoRA adapter if provided
        if lora_adapter_path:
            logger.info(f"Loading LoRA adapter from {lora_adapter_path}")
            model = PeftModel.from_pretrained(model, lora_adapter_path)
            model = model.merge_and_unload()  # Merge for faster inference

        self.model = model
        self.model.eval()

        # Build text generation pipeline
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.float16,
            device_map=device,
        )

        # RAG retriever
        self.retriever = (
            CodeAuditRetriever(vector_store, n_results=n_rag_results)
            if vector_store
            else None
        )

        logger.success("Model loaded and ready for inference.")

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def audit(
        self,
        code_snippet: str,
        use_rag: bool = True,
        max_new_tokens: int = 1024,
        temperature: float = 0.1,
        system_prompt: str = "",
        style_guide: str = "",
    ) -> AuditResult:
        """
        Audit a code snippet for security vulnerabilities.

        Args:
            code_snippet: The code to audit.
            use_rag: Whether to augment the prompt with retrieved CVE/CWE context.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (lower = more deterministic).

        Returns:
            AuditResult with structured vulnerability information.
        """
        retrieved = []

        if use_rag and self.retriever:
            prompt = self.retriever.build_augmented_prompt(
                code_snippet, system_prompt, style_guide
            )
            retrieved = self.retriever.retrieve(code_snippet)
        else:
            prompt = self._build_basic_prompt(code_snippet, system_prompt, style_guide)

        # Format as instruction prompt
        full_prompt = (
            f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
        )

        logger.debug(f"Generating audit for {len(code_snippet)} char snippet...")
        outputs = self.pipe(
            full_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=self.tokenizer.eos_token_id,
            return_full_text=False,
        )

        raw_output = outputs[0]["generated_text"].strip()
        result = self._parse_output(code_snippet, raw_output)
        result.retrieved_patterns = retrieved
        return result

    def _build_basic_prompt(
        self, code_snippet: str, system_prompt: str, style_guide: str
    ) -> str:
        return f"""{style_guide}

Analyze the following code snippet for security vulnerabilities:

```c
{code_snippet}
```

Provide:
1. Vulnerability type (CWE ID and name)
2. Severity assessment
3. Detailed explanation of the vulnerability
4. Secure rewrite following the style guide above"""

    def _parse_output(self, code_snippet: str, raw_output: str) -> AuditResult:
        """
        Parse the model's raw text output into a structured AuditResult.
        Uses regex patterns to extract CWE, severity, code blocks, etc.
        """
        result = AuditResult(
            vulnerable_code=code_snippet,
            is_vulnerable=True,  # Default assumption; override if model says otherwise
            raw_output=raw_output,
        )

        # Check if model says no vulnerability
        no_vuln_patterns = [
            r"no vulnerability",
            r"no security issue",
            r"code is secure",
            r"no vulnerabilities detected",
        ]
        if any(re.search(p, raw_output, re.IGNORECASE) for p in no_vuln_patterns):
            result.is_vulnerable = False
            return result

        # Extract CWE ID
        cwe_match = re.search(r"CWE-(\d+)", raw_output, re.IGNORECASE)
        if cwe_match:
            result.cwe_id = f"CWE-{cwe_match.group(1)}"

        # Extract severity
        severity_match = re.search(
            r"\b(Critical|High|Medium|Low)\b", raw_output, re.IGNORECASE
        )
        if severity_match:
            result.severity = severity_match.group(1).capitalize()

        # Extract secure code block
        code_blocks = re.findall(r"```(?:c|cpp|python|java)?\n(.*?)```", raw_output, re.DOTALL)
        if code_blocks:
            # Take the last code block as the secure rewrite
            result.secure_code = code_blocks[-1].strip()

        # Extract explanation (text between vulnerability type and secure rewrite)
        explanation_match = re.search(
            r"(?:explanation|vulnerability explanation|description)[:\s]+(.*?)(?:secure rewrite|fix|```)",
            raw_output,
            re.IGNORECASE | re.DOTALL,
        )
        if explanation_match:
            result.explanation = explanation_match.group(1).strip()[:500]

        # Extract fix summary
        fix_match = re.search(
            r"(?:fix summary|summary of changes|changes made)[:\s]+(.*?)(?:\n\n|$)",
            raw_output,
            re.IGNORECASE | re.DOTALL,
        )
        if fix_match:
            result.fix_summary = fix_match.group(1).strip()[:300]

        return result
