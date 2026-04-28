"""
Download the Big-Vul dataset from Google Drive.

Big-Vul paper: https://dl.acm.org/doi/10.1145/3379597.3387501
Dataset: MSR_data_cleaned.csv (~265K C/C++ functions with CVE/CWE labels)

Uses gdown which handles Google Drive's virus-scan confirmation for large files.
Install: pip install gdown
"""

import sys
from pathlib import Path

from loguru import logger

# Google Drive file ID for the cleaned split-functions CSV
# Source: https://github.com/ZeoVan/MSR_20_Code_vulnerability_CSV_Dataset
GDRIVE_FILE_ID = "1-0VhnHBp9IGh90s2wCNjeCMuy70HPl8X"
OUTPUT_PATH = Path("./data/raw/MSR_data_cleaned.csv")


def download_from_gdrive(file_id: str, dest: Path) -> None:
    """Download a file from Google Drive using gdown (handles auth/confirmation)."""
    try:
        import gdown
    except ImportError:
        logger.error(
            "gdown is not installed. Run: pip install gdown\n"
            "Or download manually from: "
            "https://drive.google.com/file/d/1-0VhnHBp9IGh90s2wCNjeCMuy2ws-n2H"
        )
        sys.exit(1)

    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        logger.info(f"Dataset already exists at {dest}. Skipping download.")
        return

    logger.info(f"Downloading Big-Vul dataset to {dest}...")
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, str(dest), quiet=False)
    logger.success(f"Download complete: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def verify_download(path: Path) -> bool:
    """Basic sanity check — must be a real CSV, not an HTML error page."""
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False

    size_mb = path.stat().st_size / 1e6
    if size_mb < 10:
        logger.warning(f"File seems too small ({size_mb:.1f} MB). Download may have failed.")
        return False

    # Peek at first bytes — HTML means Drive returned an error page
    with open(path, "rb") as f:
        header = f.read(10)
    if header.startswith(b"<!DOCTYPE") or header.startswith(b"<html"):
        logger.error(
            "Downloaded file is an HTML page, not a CSV. "
            "Download manually from: "
            "https://drive.google.com/file/d/1-0VhnHBp9IGh90s2wCNjeCMuy2ws-n2H"
        )
        path.unlink()  # Remove the bad file
        return False

    logger.info(f"File size: {size_mb:.1f} MB — looks good.")
    return True


if __name__ == "__main__":
    download_from_gdrive(GDRIVE_FILE_ID, OUTPUT_PATH)

    if not verify_download(OUTPUT_PATH):
        sys.exit(1)

    logger.info("Next step: run `python data/preprocessing.py` to process the dataset.")
