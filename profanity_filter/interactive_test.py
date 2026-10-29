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
    parser.add_argument("--threshold", type=float, default=50.0,
                        help="reject when rejection_probability >= this percent (default: 50)")
    args = parser.parse_args()
    rating, threshold = args.rating, args.threshold

    if not ensure_ready(rating):
        raise SystemExit("Profanity screener failed to load.")
    print(f"rating={rating} threshold={threshold}%. Blank line or Ctrl+C to quit.")
    while True:
        try:
            text = input("\ntext> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not text.strip():
            break
        try:
            result = screen_message(text, rating=rating, threshold=threshold)
        except Exception as exc:
            print(f"Screening failed: {type(exc).__name__}: {exc}")
            continue
        print(json.dumps(result.to_dict(), indent=2))
        print(f"-> {'REJECTED' if result.rejected else 'ACCEPTED'} "
              f"({result.rejection_probability:.1f}% vs {threshold}% threshold)")


if __name__ == "__main__":
    main()