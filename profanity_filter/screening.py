"""Screens text against a content rating without calling an external service."""
from dataclasses import dataclass
import logging
import time
from threading import Lock, Thread

from .rejection_scorer import RejectionScorer

logger = logging.getLogger(__name__)

DEFAULT_RATING = "PG-13"
DEFAULT_THRESHOLD = 90.0

_scorers = {}
_lock = Lock()


@dataclass
class ScreeningResult:
    rejected: bool
    rating: str
    rejection_probability: float
    score: float
    reason: str

    def to_dict(self):
        return {
            "rejected": self.rejected,
            "rating": self.rating,
            "rejection_probability": self.rejection_probability,
            "score": self.score,
            "reason": self.reason,
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
    """Load the scorer and run one prediction. Returns True when screening is usable.

    Failures are logged and retried at most every RETRY_SECONDS so a broken
    install doesn't make every request pay the load cost.
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
            _scorers[rating].score("warm up")
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


def screen_message(text, rating=DEFAULT_RATING, threshold=DEFAULT_THRESHOLD, scorer=None):
    """Return a ScreeningResult; rejected when rejection_probability (percent) >= threshold."""
    result = (scorer or _get_scorer(rating)).score(text)
    probability = result.rejection_probability or 0.0
    return ScreeningResult(
        rejected=probability >= threshold,
        rating=result.rating,
        rejection_probability=probability,
        score=result.score or 0.0,
        reason=result.reason,
    )
