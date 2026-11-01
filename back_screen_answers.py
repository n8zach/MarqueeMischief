"""Run every stored answer through the profanity screener and print PASS/FAIL.

Uses the same database config, text normalization, and rating as the Flask
app's daily-answer check.

Usage: python screen_all_answers.py [--failures-only]
Exit code: 0 if all pass, 1 if any fail, 2 if the screener is unavailable.
"""
import argparse
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
# --- Load env variables FIRST, before importing local modules ---
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path)   

from flask_app import app
from mm_game_db import Answers
from profanity_filter import (
    DEFAULT_RATING, ensure_ready, screen_message,
)


def normalize(text):
    # Mirrors flask_app._screen_daily_answer
    return " ".join((text or "").replace("\xa0", " ").split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--failures-only", action="store_true", help="only print rejected answers")
    args = parser.parse_args()

    if not ensure_ready():
        print("Profanity screener failed to load.", file=sys.stderr)
        return 2

    passed = failed = skipped = 0
    with app.app_context():
        for answer in Answers.query.order_by(Answers.id).all():
            text = normalize(answer.text)
            if not text:
                skipped += 1
                continue
            result = screen_message(text)
            if result.rejected:
                failed += 1
            else:
                passed += 1
            if result.rejected or not args.failures_only:
                status = "FAIL" if result.rejected else "PASS"
                print(
                    f"{status}  id={answer.id} tier={result.tier or '-'} | {text} | Reason: {result.reason}",
                    flush=True,
                )

    print(f"\n{passed} passed, {failed} failed, {skipped} empty skipped "
          f"(rating={DEFAULT_RATING})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())