"""Create today's daily game; intended for a once-daily scheduled task."""
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Load env variables FIRST, before importing local modules ---
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path)   

import argparse
from datetime import date, datetime, time, timedelta, timezone
import sys
if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo
from flask_app import app
from mm_game_db import create_daily_game, get_daily_game, get_or_create_puzzle
from marquee_mischief_openAI import generate_new_original_message

PACIFIC = ZoneInfo("America/Los_Angeles")

def create_game_for_day(day):
    existing = get_daily_game(day)
    if existing is not None:
        return existing

    generated_message = generate_new_original_message()
    message = generated_message.sign_message.strip()
    if not message:
        raise ValueError("The generated daily-game message was blank.")

    puzzle = get_or_create_puzzle(message)
    start_local = datetime.combine(day, time.min, tzinfo=PACIFIC)
    end_local = datetime.combine(day + timedelta(days=1), time.min, tzinfo=PACIFIC)
    return create_daily_game(
        day,
        puzzle.id,
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def main():
    parser = argparse.ArgumentParser(description="Create today's daily Marquee Mischief game.")
    parser.add_argument("--date", type=date.fromisoformat, help="Local game date in YYYY-MM-DD format (defaults to today in PST).")
    args = parser.parse_args()

    day = args.date or datetime.now(PACIFIC).date()
    with app.app_context():
        game = create_game_for_day(day)
        print(f"Daily game for {day.isoformat()} is game {game.id}.")


if __name__ == "__main__":
    main()
