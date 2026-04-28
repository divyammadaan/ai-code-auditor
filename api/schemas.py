"""
Pydantic schemas for the Code Auditor API.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    """Request body for the /audit endpoint."""
    code: str = Field(..., description="Code snippet to audit", min_length=10)
    language: str = Field(default="c", description="Programming language (c, python, java, etc.)")
    use_rag: bool = Field(default=True, description="Whether to use RAG context retrieval")
    max_new_tokens: int = Field(default=1024, ge=64, le=4096)

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "void copy(char *src) {\n    char buf[64];\n    strcpy(buf, src);\n}",
                "language": "c",
                "use_rag": True,
            }
        }
    }


class VulnerabilityInfo(BaseModel):
    """Structured vulnerability information."""
    cwe_id: Optional[str] = None
    cwe_name: Optional[str] = None
    severity: Optional[str] = None
    explanation: Optional[str] = None


class AuditResponse(BaseModel):
    """Response from the /audit endpoint."""
    is_vulnerable: bool
    vulnerability: Optional[VulnerabilityInfo] = None
    secure_code: Optional[str] = None
    fix_summary: Optional[str] = None
    retrieved_patterns: list[dict] = Field(default_factory=list)
    model_used: str = ""
    rag_enabled: bool = False


class SearchRequest(BaseModel):
    """Request body for the /search endpoint."""
    query: str = Field(..., description="Search query for vulnerability patterns", min_length=3)
    n_results: int = Field(default=5, ge=1, le=20)
    category: Optional[str] = Field(default=None, description="Filter by CWE, CVE, or SECURE_PATTERN")


class SearchResponse(BaseModel):
    """Response from the /search endpoint."""
    results: list[dict]
    total: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    vectorstore_count: int
    version: str = "0.1.0"
