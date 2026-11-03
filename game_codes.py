import os
import random

WORDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dictionary-weird.txt")


def load_words(path=WORDS_PATH):
    with open(path, encoding="utf-8") as handle:
        return [line.strip().upper() for line in handle if line.strip()]


def generate_game_code(words=None, existing=()):
    """Return WORD-WORD built from two distinct random dictionary words not in `existing`."""
    words = words or load_words()
    while True:
        first, second = random.choice(words), random.choice(words)
        code = f"{first}-{second}"
        if first != second and code not in existing:
            return code


def normalize_game_code(code):
    return "-".join(part for part in (code or "").upper().replace("-", " ").split())
