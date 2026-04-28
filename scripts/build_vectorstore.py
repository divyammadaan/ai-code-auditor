"""
One-shot script to build the ChromaDB vector store with all CVE/CWE patterns.
Run this once before starting the API or running evaluations.
"""

import sys
from pathlib import Path

# Ensure project root is on the path when running as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from rag.cve_loader import load_all_patterns, load_nvd_cves
from rag.vectorstore import VectorStore


def main(nvd_json_path: str = None):
    logger.info("Building vector store...")

    store = VectorStore()

    # Load built-in CWE + secure patterns
    patterns = load_all_patterns()
    logger.info(f"Loaded {len(patterns)} built-in patterns")

    # Optionally load NVD CVE feed
    if nvd_json_path:
        nvd_patterns = load_nvd_cves(Path(nvd_json_path))
        patterns.extend(nvd_patterns)
        logger.info(f"Added {len(nvd_patterns)} NVD CVE patterns")

    store.ingest(patterns)
    logger.success(f"Vector store built with {store.count()} total documents")

    # Quick sanity check
    test_results = store.search("buffer overflow strcpy", n_results=3)
    logger.info("Sanity check — top results for 'buffer overflow strcpy':")
    for r in test_results:
        logger.info(f"  {r['id']} (similarity: {r['similarity']:.3f})")


if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def build(nvd_json: str = typer.Option(None, help="Path to NVD JSON feed file")):
        """Build the ChromaDB vector store."""
        main(nvd_json)

    app()
