#!/usr/bin/env python3
"""CLI utility for rapid demonstration state resets per Section 15.1.

Usage:
    python backend/scripts/demo_reset.py
    python backend/scripts/demo_reset.py --preload
"""

import argparse
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.modules.demo.service import DemoResetService
from seeds.run_seed import OAKRIDGE_SCHOOL_ID, TEACHER_PRIYA_ID


def main():
    parser = argparse.ArgumentParser(description="LearningBridge Demonstration Reset Utility")
    parser.add_argument(
        "--preload",
        action="store_true",
        help="Preload synthetic Class 6 Term 1 baseline dataset after reset for instant demonstration",
    )
    args = parser.parse_args()

    print(f"🔄 Initiating controlled reset of demo tenant '{OAKRIDGE_SCHOOL_ID}'...")

    with SessionLocal() as db:
        res = DemoResetService.reset_demo_tenant(
            db=db,
            school_id=OAKRIDGE_SCHOOL_ID,
            actor_id=TEACHER_PRIYA_ID,
            actor_name="Priya Sharma (Demo Reset Script)",
            preload_baseline=args.preload,
        )

    print(f"✅ {res['message']}")
    print(f"   • Target School: {res['school_name']} ({res['school_id']})")
    print(f"   • Baseline Preloaded: {res['preloaded_baseline']}")
    print(f"   • Timestamp: {res['timestamp']}")
    if res['preloaded_baseline']:
        print("📢 NOTE: Baseline dataset has been preloaded for concise live demonstration.")
    else:
        print("💡 Ready for live question-level CSV assessment import drill.")


if __name__ == "__main__":
    main()
