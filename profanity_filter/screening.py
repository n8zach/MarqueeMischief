"""Screens text against a content rating using local and OpenAI checks."""
from dataclasses import dataclass
import logging
import time
from threading import Lock, Thread

from .rejection_scorer import RejectionScorer

logger = logging.getLogger(__name__)

DEFAULT_RATING = "PG-13"

_scorers = {}
_lock = Lock()


@dataclass
class ScreeningResult:
    rejected: bool
    rating: str
    reason: str
    tier: str = ""

    @property
    def word_match(self):
        """True when the built-in word detector flagged the text (not the ML model)."""
        return self.tier == "deterministic"

    def to_dict(self):
        return {
            "verdict": "FAIL" if self.rejected else "PASS",
            "rating": self.rating,
            "reason": self.reason,
            "tier": self.tier,
            "word_match": self.word_match,
        }


def _get_scorer(rating):
    with _lock:
        if rating not in _scorers:
            _scorers[rating] = RejectionScorer(rating=rating)
        return _scorers[rating]


class ScreenerUnavailableError(Exception):
    """Raised when the profanity screener cannot be loaded or used."""


_ready = set()
_failed_at = {}
RETRY_SECONDS = 30


def _say(message):
    print(f"[startup {time.strftime('%H:%M:%S')}] {message}", flush=True)


def ensure_ready(rating=DEFAULT_RATING):
    """Initialize the local detector and OpenAI client without making an API call.

    Failures are logged and retried at most every RETRY_SECONDS so a broken
    install doesn't make every request pay the initialization cost.
    """
    if rating in _ready:
        return True
    with _lock:
        if rating in _ready:
            return True
        last_failure = _failed_at.get(rating)
        if last_failure is not None and time.monotonic() - last_failure < RETRY_SECONDS:
            return False
        started = time.monotonic()
        _say(f"Profanity screener: loading (rating={rating})...")
        try:
            _scorers.setdefault(rating, RejectionScorer(rating=rating))
        except Exception as exc:
            _scorers.pop(rating, None)
            _failed_at[rating] = time.monotonic()
            _say(f"Profanity screener: FAILED after {time.monotonic() - started:.1f}s: {type(exc).__name__}: {exc}")
            logger.critical(
                "PROFANITY SCREENER UNAVAILABLE (rating=%s): daily game is disabled until it loads.",
                rating, exc_info=True,
            )
            return False
        _ready.add(rating)
        _failed_at.pop(rating, None)
        _say(f"Profanity screener: ready in {time.monotonic() - started:.1f}s (rating={rating}).")
        return True


def warm_up(rating=DEFAULT_RATING):
    ensure_ready(rating)


def start_background_warm_up(rating=DEFAULT_RATING):
    _say("Profanity screener: background warm-up started.")
    thread = Thread(target=warm_up, args=(rating,), name="profanity-warm-up", daemon=True)
    thread.start()
    return thread


def screen_message(text, rating=DEFAULT_RATING, scorer=None):
    """Return the PASS/FAIL screening result."""
    result = (scorer or _get_scorer(rating)).score(text)
    return ScreeningResult(
        rejected=result.rejected,
        rating=result.rating,
        reason=result.reason,
        tier=result.tier,
    )
