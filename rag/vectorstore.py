"""
ChromaDB vector store setup and ingestion for CVE/CWE patterns.

Uses sentence-transformers for embedding (all-MiniLM-L6-v2 by default),
which is fast and effective for code-related semantic search.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from loguru import logger
from sentence_transformers import SentenceTransformer

from rag.cve_loader import VulnerabilityPattern, load_all_patterns


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/vectorstore")
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "secure_code_patterns")
DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast, good for semantic search


# ---------------------------------------------------------------------------
# VectorStore class
# ---------------------------------------------------------------------------

class VectorStore:
    """
    Wrapper around ChromaDB for storing and retrieving vulnerability patterns.

    Usage:
        store = VectorStore()
        store.ingest(patterns)
        results = store.search("buffer overflow in C", n_results=5)
    """

    def __init__(
        self,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        embed_model: str = DEFAULT_EMBED_MODEL,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        logger.info(f"Initializing ChromaDB at {persist_dir}")
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        logger.info(f"Loading embedding model: {embed_model}")
        self.embedder = SentenceTransformer(embed_model)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Cosine similarity for semantic search
        )
        logger.info(
            f"Collection '{collection_name}' ready. "
            f"Current document count: {self.collection.count()}"
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, patterns: list[VulnerabilityPattern], batch_size: int = 64) -> None:
        """
        Embed and store vulnerability patterns in ChromaDB.
        Skips patterns that are already in the collection (by ID).
        """
        existing_ids = set(self.collection.get(include=[])["ids"])
        new_patterns = [p for p in patterns if p.id not in existing_ids]

        if not new_patterns:
            logger.info("All patterns already in vector store. Nothing to ingest.")
            return

        logger.info(f"Ingesting {len(new_patterns)} new patterns...")

        for i in range(0, len(new_patterns), batch_size):
            batch = new_patterns[i : i + batch_size]
            documents = [p.to_document() for p in batch]
            metadatas = [p.to_metadata() for p in batch]
            ids = [p.id for p in batch]

            embeddings = self.embedder.encode(documents, show_progress_bar=False).tolist()

            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            logger.debug(f"Ingested batch {i // batch_size + 1}: {len(batch)} patterns")

        logger.success(
            f"Ingestion complete. Total documents in store: {self.collection.count()}"
        )

    def ingest_default_patterns(self) -> None:
        """Convenience method to ingest all built-in CWE/CVE patterns."""
        patterns = load_all_patterns()
        self.ingest(patterns)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 5,
        category_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search for relevant vulnerability patterns.

        Args:
            query: Natural language or code snippet to search against.
            n_results: Number of results to return.
            category_filter: Filter by "CWE", "CVE", or "SECURE_PATTERN".
            severity_filter: Filter by "Critical", "High", "Medium", "Low".

        Returns:
            List of dicts with keys: id, document, metadata, distance.
        """
        query_embedding = self.embedder.encode([query]).tolist()

        where_filter = {}
        if category_filter:
            where_filter["category"] = {"$eq": category_filter}
        if severity_filter:
            where_filter["severity"] = {"$eq": severity_filter}

        query_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": min(n_results, self.collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        # Flatten ChromaDB's nested result format
        output = []
        for doc, meta, dist, doc_id in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            results["ids"][0],
        ):
            output.append(
                {
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta,
                    "similarity": 1 - dist,  # Convert cosine distance to similarity
                }
            )

        return output

    def format_context(self, results: list[dict]) -> str:
        """
        Format search results into a context string for LLM prompts.
        """
        if not results:
            return "No relevant vulnerability patterns found."

        lines = ["## Relevant Vulnerability Patterns from Knowledge Base\n"]
        for i, r in enumerate(results, 1):
            meta = r["metadata"]
            lines.append(
                f"### {i}. {meta.get('title', r['id'])} ({r['id']})\n"
                f"Similarity: {r['similarity']:.2f} | Severity: {meta.get('severity', 'N/A')}\n"
                f"{r['document']}\n"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def count(self) -> int:
        return self.collection.count()

    def delete_collection(self) -> None:
        """Drop and recreate the collection (use with caution)."""
        logger.warning(f"Deleting collection '{self.collection_name}'")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
