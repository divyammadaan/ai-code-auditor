"""
RAG retriever: given a code snippet, fetch relevant CVE/CWE context
and augment the LLM prompt.
"""

from __future__ import annotations

from loguru import logger

from rag.vectorstore import VectorStore


class CodeAuditRetriever:
    """
    Retrieves relevant vulnerability patterns for a given code snippet
    and builds an augmented prompt for the LLM.
    """

    def __init__(self, vector_store: VectorStore, n_results: int = 3):
        self.store = vector_store
        self.n_results = n_results

    def retrieve(self, code_snippet: str) -> list[dict]:
        """Retrieve top-k relevant patterns for the given code snippet."""
        results = self.store.search(code_snippet, n_results=self.n_results)
        logger.debug(f"Retrieved {len(results)} patterns for code snippet")
        return results

    def build_augmented_prompt(
        self,
        code_snippet: str,
        system_prompt: str,
        style_guide: str,
    ) -> str:
        """
        Build a RAG-augmented prompt by prepending retrieved context.

        The retrieved CVE/CWE patterns give the LLM concrete examples
        of vulnerability types and secure rewrites, reducing hallucination.
        """
        results = self.retrieve(code_snippet)
        context = self.store.format_context(results)

        prompt = f"""{system_prompt}

{style_guide}

{context}

---

Now analyze the following code snippet:

```c
{code_snippet}
```

Provide:
1. Vulnerability type (CWE ID and name)
2. Severity assessment (Critical/High/Medium/Low)
3. Detailed explanation of the vulnerability
4. Secure rewrite following the corporate style guide
5. Summary of changes made"""

        return prompt

    def get_cwe_hints(self, code_snippet: str) -> list[str]:
        """Return a list of likely CWE IDs based on semantic similarity."""
        results = self.retrieve(code_snippet)
        return [
            r["id"]
            for r in results
            if r["metadata"].get("category") == "CWE" and r["similarity"] > 0.4
        ]
