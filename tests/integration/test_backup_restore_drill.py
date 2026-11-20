"""Automated verification test for Phase 7 database backup and disposable restore drill (Section 14.3)."""

from pathlib import Path
import sqlite3
import pytest

from backend.scripts.backup_restore import backup_sqlite, verify_restore_sqlite
from app.core.config import settings


def test_phase7_backup_and_disposable_restore_drill(tmp_path: Path):
    """Executes live backup of test database and verifies restore in disposable database."""
    # Find database file
    root_dir = Path(__file__).resolve().parent.parent.parent
    db_path = root_dir / "learningbridge.db"
    if not db_path.exists():
        pytest.skip("learningbridge.db not found on disk")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create live snapshot
    backup_file, digest = backup_sqlite(db_path, backup_dir)
    assert backup_file.exists()
    assert len(digest) == 64

    # 2. Verify restore into disposable database
    is_valid = verify_restore_sqlite(backup_file)
    assert is_valid is True
