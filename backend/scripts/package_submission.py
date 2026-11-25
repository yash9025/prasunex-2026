"""Automated submission packaging script for PRASUNEX Innovathon 2026.

Creates a clean, production-grade ZIP archive excluding heavy, unportable directories
(like node_modules, __pycache__, and test caches), while preserving all source code,
compiled assets, seed fixtures, pre-configured database, and comprehensive documentation.
"""

import os
import sys
import zipfile
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_ZIP = ROOT_DIR / "LearningBridge_Prasunex2026_Submission.zip"

EXCLUDE_DIRS = {
    "node_modules",
    ".pytest_cache",
    "__pycache__",
    ".git",
    ".vscode",
    ".idea",
    ".venv",
    "venv",
    "video_assets",
}

EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".log"}
EXCLUDE_FILES = {"test_learningbridge.db", "LearningBridge_Prasunex2026_Submission.zip"}


def build_submission_zip() -> None:
    print(f"📦 Packaging LearningBridge submission from {ROOT_DIR}...")
    
    file_count = 0
    total_uncompressed = 0
    
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
            
            # Keep only the latest verified backup in backups/
            if "backups" in root:
                files = [f for f in files if f == "learningbridge_backup_20261119_065026.db"]
            
            for file in files:
                if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                
                full_path = Path(root) / file
                rel_path = full_path.relative_to(ROOT_DIR)
                
                zipf.write(full_path, str(rel_path))
                file_count += 1
                total_uncompressed += full_path.stat().st_size

    # Calculate SHA-256 checksum
    hasher = hashlib.sha256()
    with open(OUTPUT_ZIP, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    sha256_hash = hasher.hexdigest()
    
    zip_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    uncompressed_mb = total_uncompressed / (1024 * 1024)
    
    print("\n✅ Submission ZIP generated successfully!")
    print(f"   • File Name:     {OUTPUT_ZIP.name}")
    print(f"   • Full Path:     {OUTPUT_ZIP}")
    print(f"   • File Size:     {zip_size_mb:.2f} MB (compressed from {uncompressed_mb:.2f} MB)")
    print(f"   • Total Files:   {file_count}")
    print(f"   • SHA-256:       {sha256_hash}")


if __name__ == "__main__":
    build_submission_zip()
