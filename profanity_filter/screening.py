"""Screens text against a content rating without calling an external service."""
from dataclasses import dataclass
from threading import Lock

from .rejection_scorer import RejectionScorer

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
