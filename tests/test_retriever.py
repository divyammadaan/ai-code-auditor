"""
Unit tests for the RAG vector store and retriever.
Uses an in-memory ChromaDB instance to avoid disk I/O.
"""

import pytest

from rag.cve_loader import VulnerabilityPattern, load_all_patterns
from rag.vectorstore import VectorStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_store(tmp_path):
    """Create a temporary VectorStore for testing."""
    store = VectorStore(
        persist_dir=str(tmp_path / "chroma"),
        collection_name="test_collection",
    )
    return store


@pytest.fixture
def populated_store(temp_store):
    """VectorStore pre-populated with default patterns."""
    temp_store.ingest_default_patterns()
    return temp_store


@pytest.fixture
def sample_patterns():
    return [
        VulnerabilityPattern(
            id="TEST-001",
            title="Test Buffer Overflow",
            description="A test buffer overflow vulnerability using strcpy without bounds checking.",
            category="CWE",
            severity="Critical",
            tags=["buffer-overflow", "C"],
        ),
        VulnerabilityPattern(
            id="TEST-002",
            title="Test SQL Injection",
            description="A test SQL injection via string concatenation in database queries.",
            category="CWE",
            severity="Critical",
            tags=["sql-injection"],
        ),
        VulnerabilityPattern(
            id="TEST-003",
            title="Test XSS",
            description="Cross-site scripting via unescaped user input in HTML output.",
            category="CWE",
            severity="High",
            tags=["xss", "web"],
        ),
    ]


# ---------------------------------------------------------------------------
# VectorStore tests
# ---------------------------------------------------------------------------

class TestVectorStore:
    def test_empty_store(self, temp_store):
        assert temp_store.count() == 0

    def test_ingest_patterns(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        assert temp_store.count() == 3

    def test_no_duplicate_ingestion(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        temp_store.ingest(sample_patterns)  # Second ingest should be skipped
        assert temp_store.count() == 3

    def test_search_returns_results(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        results = temp_store.search("buffer overflow strcpy", n_results=2)
        assert len(results) > 0
        assert "id" in results[0]
        assert "document" in results[0]
        assert "similarity" in results[0]

    def test_search_relevance(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        results = temp_store.search("SQL injection database query", n_results=3)
        # The SQL injection pattern should be most relevant
        top_result = results[0]
        assert "sql" in top_result["id"].lower() or "sql" in top_result["document"].lower()

    def test_search_similarity_range(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        results = temp_store.search("test query", n_results=3)
        for r in results:
            assert 0.0 <= r["similarity"] <= 1.0

    def test_format_context(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        results = temp_store.search("buffer overflow", n_results=2)
        context = temp_store.format_context(results)
        assert "Relevant Vulnerability Patterns" in context
        assert len(context) > 50

    def test_format_context_empty(self, temp_store):
        context = temp_store.format_context([])
        assert "No relevant" in context

    def test_ingest_default_patterns(self, temp_store):
        temp_store.ingest_default_patterns()
        # Should have at least the built-in CWE + secure patterns
        assert temp_store.count() >= 10

    def test_delete_collection(self, temp_store, sample_patterns):
        temp_store.ingest(sample_patterns)
        assert temp_store.count() == 3
        temp_store.delete_collection()
        assert temp_store.count() == 0


class TestCveLoader:
    def test_load_all_patterns_returns_list(self):
        patterns = load_all_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_patterns_have_required_fields(self):
        patterns = load_all_patterns()
        for p in patterns:
            assert p.id
            assert p.title
            assert p.description
            assert p.category in ("CWE", "CVE", "SECURE_PATTERN")

    def test_to_document_format(self):
        patterns = load_all_patterns()
        for p in patterns:
            doc = p.to_document()
            assert p.id in doc
            assert p.title in doc

    def test_to_metadata_format(self):
        patterns = load_all_patterns()
        for p in patterns:
            meta = p.to_metadata()
            assert "id" in meta
            assert "title" in meta
            assert "category" in meta
