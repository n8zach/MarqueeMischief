"""Generates 40 original messages to show variety and the rolling history file.

Run: python test_original_message_history.py
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

from marquee_mischief_openAI import generate_new_original_message, load_message_history, HISTORY_FILE

COUNT = 40

if __name__ == "__main__":
    seen = []
    for i in range(1, COUNT + 1):
        result = generate_new_original_message()
        seen.append(result.sign_message)
        print(f"{i:2}. {result.sign_message}  |  {result.caption}")

    print(f"\nUnique messages: {len(set(m.lower() for m in seen))} of {COUNT}")
    