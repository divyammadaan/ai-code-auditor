"""
FastAPI application for the AI Code Auditor.

Endpoints:
  GET  /health          — Health check
  POST /audit           — Audit a code snippet
  POST /search          — Search vulnerability patterns
  GET  /patterns        — List all stored patterns
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.schemas import (
    AuditRequest,
    AuditResponse,
    HealthResponse,
    SearchRequest,
    SearchResponse,
    VulnerabilityInfo,
)
from rag.vectorstore import VectorStore

load_dotenv()

# ---------------------------------------------------------------------------
# Global state (loaded once at startup)
# ---------------------------------------------------------------------------

_model = None
_vector_store: Optional[VectorStore] = None
_config: dict = {}

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and vector store on startup."""
    global _model, _vector_store, _config

    logger.info("Starting AI Code Auditor API...")

    # Load config
    try:
        with open("configs/training_config.yaml") as f:
            _config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        _config = {}

    # Initialize vector store
    try:
        _vector_store = VectorStore()
        if _vector_store.count() == 0:
            logger.info("Vector store is empty, ingesting default patterns...")
            _vector_store.ingest_default_patterns()
        logger.info(f"Vector store ready: {_vector_store.count()} patterns")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        _vector_store = None

    # Load model (lazy — only if HF_TOKEN is set and model path exists)
    base_model = os.getenv("BASE_MODEL", "codellama/CodeLlama-7b-hf")
    lora_path = os.getenv("FINETUNED_MODEL_PATH", "./outputs/lora_adapter")

    if os.path.exists(lora_path) or os.getenv("LOAD_MODEL_ON_STARTUP", "false").lower() == "true":
        try:
            from models.inference import CodeAuditorModel
            _model = CodeAuditorModel(
                base_model_id=base_model,
                lora_adapter_path=lora_path if os.path.exists(lora_path) else None,
                vector_store=_vector_store,
            )
            logger.success("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            _model = None
    else:
        logger.info(
            "Model not loaded (set LOAD_MODEL_ON_STARTUP=true or ensure LoRA adapter exists). "
            "Vector store and search endpoints are available."
        )

    yield

    logger.info("Shutting down AI Code Auditor API...")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Code Auditor",
    description=(
        "Security vulnerability detection and secure code rewriting "
        "using PEFT fine-tuned LLMs with RAG-augmented context."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        model_loaded=_model is not None,
        vectorstore_count=_vector_store.count() if _vector_store else 0,
    )


@app.post("/audit", response_model=AuditResponse)
async def audit_code(request: AuditRequest):
    """
    Audit a code snippet for security vulnerabilities.
    Returns vulnerability classification, explanation, and a secure rewrite.
    """
    # ── Demo mode: model not loaded, use pre-computed results ──────────────
    if _model is None:
        from api.demo_mode import get_demo_response
        demo = get_demo_response(request.code)

        # Still run RAG search if requested and vector store is available
        retrieved = []
        if request.use_rag and _vector_store is not None:
            retrieved = _vector_store.search(
                query=request.code,
                n_results=3,
            )

        vuln_info = None
        if demo["is_vulnerable"] and demo.get("vulnerability"):
            v = demo["vulnerability"]
            vuln_info = VulnerabilityInfo(
                cwe_id=v["cwe_id"],
                cwe_name=v["cwe_name"],
                severity=v["severity"],
                explanation=v["explanation"],
            )
        return AuditResponse(
            is_vulnerable=demo["is_vulnerable"],
            vulnerability=vuln_info,
            secure_code=demo.get("secure_code", ""),
            fix_summary=demo.get("fix_summary", ""),
            retrieved_patterns=retrieved[:3],
            model_used="DeepSeek-Coder-6.7B + QLoRA v4 [DEMO MODE]",
            rag_enabled=request.use_rag and _vector_store is not None,
        )

    try:
        result = _model.audit(
            code_snippet=request.code,
            use_rag=request.use_rag and _vector_store is not None,
            max_new_tokens=request.max_new_tokens,
            system_prompt=SYSTEM_PROMPT,
            style_guide=STYLE_GUIDE,
        )

        vuln_info = None
        if result.is_vulnerable:
            vuln_info = VulnerabilityInfo(
                cwe_id=result.cwe_id,
                cwe_name=result.cwe_name,
                severity=result.severity,
                explanation=result.explanation,
            )

        return AuditResponse(
            is_vulnerable=result.is_vulnerable,
            vulnerability=vuln_info,
            secure_code=result.secure_code,
            fix_summary=result.fix_summary,
            retrieved_patterns=result.retrieved_patterns[:3],  # Top 3 only
            model_used=os.getenv("BASE_MODEL", "codellama/CodeLlama-7b-hf"),
            rag_enabled=request.use_rag,
        )

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_patterns(request: SearchRequest):
    """
    Search the vulnerability pattern knowledge base.
    """
    if _vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not available")

    results = _vector_store.search(
        query=request.query,
        n_results=request.n_results,
        category_filter=request.category,
    )

    return SearchResponse(results=results, total=len(results))


@app.get("/patterns")
async def list_patterns(limit: int = 50, offset: int = 0):
    """List all stored vulnerability patterns."""
    if _vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not available")

    all_data = _vector_store.collection.get(
        limit=limit,
        offset=offset,
        include=["documents", "metadatas"],
    )

    return {
        "total": _vector_store.count(),
        "offset": offset,
        "limit": limit,
        "patterns": [
            {"id": id_, "metadata": meta}
            for id_, meta in zip(all_data["ids"], all_data["metadatas"])
        ],
    }
