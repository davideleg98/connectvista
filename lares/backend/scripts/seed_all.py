"""Run with: ./.venv/bin/python scripts/seed_all.py
Seeds source_registry rows and the QA dataset. Idempotent-ish for the
source registry (skips existing names); the QA seed is meant for a fresh
database (see DEVELOPMENT.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import SessionLocal
from app.seed.qa_seed import load_qa_seed
from app.seed.source_registry_seed import seed_source_registry

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_source_registry(db)
        print("source_registry seeded")
        counts = load_qa_seed(db)
        print(f"QA seed loaded: {counts}")
    finally:
        db.close()
