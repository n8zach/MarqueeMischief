"""Interactive CLI for the profanity screener used by the web app."""
import argparse
import json
import sys
from pathlib import Path

# Allow running this file directly from inside the package folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from profanity_filter import ensure_ready, screen_message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rating", default="PG-13", help="G, PG, PG-13, R or NC-17 (default: PG-13)")
    args = parser.parse_args()
    rating = args.rating

    if not ensure_ready(rating):
        raise SystemExit("Profanity screener failed to load.")
    print(f"rating={rating}. Blank line or Ctrl+C to quit.")
    while True:
        try:
            text = input("\ntext> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not text.strip():
            break
        try:
            result = screen_message(text, rating=rating)
        except Exception as exc:
            print(f"Screening failed: {type(exc).__name__}: {exc}")
            continue
        print(json.dumps(result.to_dict(), indent=2))
        print(f"-> {'FAIL' if result.rejected else 'PASS'}")


if __name__ == "__main__":
    main()