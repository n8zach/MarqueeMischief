"""Multi-tier, configurable text rejection scoring.

The built-in deterministic tier uses better-profanity's maintained word list.
The optional probabilistic tier uses alt-profanity-check's predict_prob model.
No project-owned profanity whitelist or blacklist is required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping, Protocol, Sequence


# These are starting policy thresholds for the model's raw offensive-language
# score, not official MPAA rules and not calibrated probabilities. Tune them
# against your own accepted/rejected examples when those become available.
DEFAULT_RATING_THRESHOLDS: dict[str, float] = {
    "G": 0.04,
    "PG": 0.10,
    "PG-13": 0.20,
    "R": 0.40,
    "NC-17": 0.65,
}

_RATING_ALIASES = {
    "STRICT": "G",
    "STANDARD": "PG-13",
    "MODERATE": "PG-13",
    "LENIENT": "R",
}


class ProfanityDetector(Protocol):
    """Adapter interface for deterministic detectors."""

    def contains_profanity(self, text: str) -> bool: ...


class ProbabilityModel(Protocol):
    """Adapter interface for a model returning one [0, 1] score per input."""

    def predict_prob(self, texts: Sequence[str]) -> Iterable[float]: ...


@dataclass(frozen=True, slots=True)
class RejectionResult:
    """Result of scoring one text.

    Attributes:
        rejection_probability: Estimated chance of rejection, in percent (0-100).
        score: Raw offensive-language model score in percent (0-100). A hard
            deterministic hit always has score 100. This is not the same as a
            rating-specific rejection probability for non-hard-hit texts.
        reason: Short, user-facing explanation.
        tier: ``deterministic``, ``machine_learning``, or ``empty``.
        would_reject: Whether rejection_probability is at least 50%.
        model_probability: Raw model output in [0, 1], or None if no ML ran.
    """

    text: str
    rating: str
    rejection_probability: float | None
    score: float | None
    reason: str
    tier: str
    would_reject: bool | None
    model_probability: float | None = None

    @property
    def probability(self) -> float | None:
        """Alias for rejection_probability (percentage from 0 to 100)."""
        return self.rejection_probability

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


class RejectionScoringError(RuntimeError):
    """Base error for scoring failures."""


class ModelUnavailableError(RejectionScoringError):
    """Raised when the optional ML dependency is unavailable."""


class ModelOutputError(RejectionScoringError):
    """Raised when the ML model fails or returns invalid scores."""


class _BetterProfanityAdapter:
    def __init__(self) -> None:
        try:
            from better_profanity import profanity
        except ImportError as exc:  # pragma: no cover - depends on installation
            raise ImportError(
                "The deterministic tier requires better-profanity. Install it with "
                "`pip install better-profanity`."
            ) from exc
        # Explicitly load the library's built-in list. No custom list is supplied.
        profanity.load_censor_words()
        self._profanity = profanity

    def contains_profanity(self, text: str) -> bool:
        return bool(self._profanity.contains_profanity(text))


class _AltProfanityAdapter:
    def __init__(self) -> None:
        try:
            # The distribution is named alt-profanity-check, but its documented
            # import-compatible module is profanity_check.
            from profanity_check import predict_prob
        except ImportError as exc:  # pragma: no cover - depends on installation
            raise ModelUnavailableError(
                "The ML tier requires alt-profanity-check. Install it with "
                "`pip install alt-profanity-check`."
            ) from exc
        self._predict_prob = predict_prob

    def predict_prob(self, texts: Sequence[str]) -> list[float]:
        try:
            raw = self._predict_prob(list(texts))
            return [float(value) for value in raw]
        except Exception as exc:  # turn third-party failures into a stable API error
            raise ModelOutputError(f"The profanity model failed to score the text: {exc}") from exc


class RejectionScorer:
    """Score the probability that text will be rejected for a target rating.

    Args:
        rating: ``G``, ``PG``, ``PG-13``, ``R``, or ``NC-17``. Also accepts
            ``strict`` (G), ``standard``/``moderate`` (PG-13), or ``lenient`` (R).
        use_ml: Run alt-profanity-check after deterministic checks. If True and
            its optional dependency is missing, construction raises a helpful error.
        rating_thresholds: Overrides for the raw model-score threshold at which
            the estimated rejection probability is 50%. Values must be in (0, 1).
        temperature: Controls how quickly rejection probability changes around
            the threshold. Must be greater than zero. This is a heuristic link,
            not a substitute for calibrating against real moderation outcomes.
        detector: Optional injected deterministic detector, mainly for testing or
            integrating a detector with the same interface.
        model: Optional injected probability model, mainly for testing or replacing
            alt-profanity-check with a compatible model.

    A deterministic hit is treated as a hard rejection and always yields 100%.
    That rule intentionally takes precedence over rating profile and ML output.
    """

    def __init__(
        self,
        rating: str = "PG-13",
        *,
        use_ml: bool = True,
        rating_thresholds: Mapping[str, float] | None = None,
        temperature: float = 0.70,
        detector: ProfanityDetector | None = None,
        model: ProbabilityModel | None = None,
    ) -> None:
        self.rating = self._normalize_rating(rating)
        if not math.isfinite(temperature) or temperature <= 0:
            raise ValueError("temperature must be a finite number greater than zero")
        self.temperature = float(temperature)

        thresholds = dict(DEFAULT_RATING_THRESHOLDS)
        if rating_thresholds:
            for key, value in rating_thresholds.items():
                normalized_key = self._normalize_rating(key)
                numeric_value = float(value)
                if not math.isfinite(numeric_value) or not 0 < numeric_value < 1:
                    raise ValueError(
                        f"Threshold for {key!r} must be a finite number strictly between 0 and 1"
                    )
                thresholds[normalized_key] = numeric_value
        self.rating_thresholds = thresholds
        self._detector = detector if detector is not None else _BetterProfanityAdapter()
        self._model = None
        if use_ml:
            self._model = model if model is not None else _AltProfanityAdapter()
        elif model is not None:
            self._model = model

    @staticmethod
    def _normalize_rating(rating: str) -> str:
        if not isinstance(rating, str):
            raise TypeError("rating must be a string such as 'PG-13'")
        normalized = rating.strip().upper().replace(" ", "")
        normalized = _RATING_ALIASES.get(normalized, normalized)
        if normalized not in DEFAULT_RATING_THRESHOLDS:
            accepted = ", ".join(DEFAULT_RATING_THRESHOLDS)
            raise ValueError(f"Unsupported rating {rating!r}. Choose one of: {accepted}")
        return normalized

    @staticmethod
    def _percentage(value: float) -> float:
        return round(min(100.0, max(0.0, value)), 2)

    def score(self, text: str, *, rating: str | None = None) -> RejectionResult:
        """Score one string. ``rating`` overrides this scorer's default rating."""
        selected_rating = self.rating if rating is None else self._normalize_rating(rating)
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        if not text.strip():
            return RejectionResult(
                text=text,
                rating=selected_rating,
                rejection_probability=0.0,
                score=0.0,
                reason="There is no text to review, so no rejection signal was found.",
                tier="empty",
                would_reject=False,
                model_probability=None,
            )

        if self._detector.contains_profanity(text):
            return RejectionResult(
                text=text,
                rating=selected_rating,
                rejection_probability=100.0,
                score=100.0,
                reason=(
                    "Rejected: the text contains language flagged by the built-in "
                    "profanity detector. No custom word list is used."
                ),
                tier="deterministic",
                would_reject=True,
                model_probability=None,
            )

        if self._model is None:
            return RejectionResult(
                text=text,
                rating=selected_rating,
                rejection_probability=None,
                score=None,
                reason=(
                    "The built-in detector did not flag this text, but the ML tier is "
                    "disabled; a probabilistic rejection estimate is unavailable."
                ),
                tier="deterministic_only",
                would_reject=None,
                model_probability=None,
            )

        return self._score_many_after_deterministic([(text, selected_rating)])[0]

    def score_many(
        self,
        texts: Sequence[str],
        *,
        rating: str | Sequence[str] | None = None,
    ) -> list[RejectionResult]:
        """Batch-score texts, batching the ML call for efficiency.

        ``rating`` can be one rating shared by all texts, a per-text sequence of
        ratings with the same length as ``texts``, or omitted to use the default.
        """
        if isinstance(texts, (str, bytes)) or not isinstance(texts, Sequence):
            raise TypeError("texts must be a sequence of strings, not a single string")
        for text in texts:
            if not isinstance(text, str):
                raise TypeError("every item in texts must be a string")

        if rating is None:
            ratings = [self.rating] * len(texts)
        elif isinstance(rating, str):
            ratings = [self._normalize_rating(rating)] * len(texts)
        else:
            if len(rating) != len(texts):
                raise ValueError("A per-text rating sequence must match the number of texts")
            ratings = [self._normalize_rating(item) for item in rating]

        results: list[RejectionResult | None] = [None] * len(texts)
        candidates: list[tuple[str, str]] = []
        candidate_indexes: list[int] = []

        for index, (text, selected_rating) in enumerate(zip(texts, ratings)):
            if not text.strip():
                results[index] = RejectionResult(
                    text=text,
                    rating=selected_rating,
                    rejection_probability=0.0,
                    score=0.0,
                    reason="There is no text to review, so no rejection signal was found.",
                    tier="empty",
                    would_reject=False,
                    model_probability=None,
                )
            elif self._detector.contains_profanity(text):
                results[index] = RejectionResult(
                    text=text,
                    rating=selected_rating,
                    rejection_probability=100.0,
                    score=100.0,
                    reason=(
                        "Rejected: the text contains language flagged by the built-in "
                        "profanity detector. No custom word list is used."
                    ),
                    tier="deterministic",
                    would_reject=True,
                    model_probability=None,
                )
            elif self._model is None:
                results[index] = RejectionResult(
                    text=text,
                    rating=selected_rating,
                    rejection_probability=None,
                    score=None,
                    reason=(
                        "The built-in detector did not flag this text, but the ML tier is "
                        "disabled; a probabilistic rejection estimate is unavailable."
                    ),
                    tier="deterministic_only",
                    would_reject=None,
                    model_probability=None,
                )
            else:
                candidates.append((text, selected_rating))
                candidate_indexes.append(index)

        if candidates:
            candidate_results = self._score_many_after_deterministic(candidates)
            for index, result in zip(candidate_indexes, candidate_results):
                results[index] = result

        # All indices are filled in the loops above.
        return [result for result in results if result is not None]

    def _score_many_after_deterministic(
        self, candidates: Sequence[tuple[str, str]]
    ) -> list[RejectionResult]:
        assert self._model is not None
        texts = [text for text, _ in candidates]
        try:
            raw_probabilities = [float(p) for p in self._model.predict_prob(texts)]
        except RejectionScoringError:
            raise
        except Exception as exc:
            raise ModelOutputError(f"The profanity model failed to score the text: {exc}") from exc

        if len(raw_probabilities) != len(candidates):
            raise ModelOutputError(
                "The profanity model returned a different number of scores than inputs"
            )

        results: list[RejectionResult] = []
        for (text, selected_rating), model_probability in zip(candidates, raw_probabilities):
            if not math.isfinite(model_probability) or not 0.0 <= model_probability <= 1.0:
                raise ModelOutputError(
                    "The profanity model must return finite probabilities between 0 and 1"
                )
            raw_score = self._percentage(model_probability * 100.0)
            rejection_probability = self._rating_probability_for(
                model_probability, selected_rating
            )
            if rejection_probability >= 80:
                reason = (
                    f"The model detected a strong signal for profanity or offensive language "
                    f"for the {selected_rating} profile. Estimated rejection likelihood: "
                    f"{rejection_probability:.2f}%."
                )
            elif rejection_probability >= 50:
                reason = (
                    f"The text is borderline-to-likely to be rejected for the "
                    f"{selected_rating} profile. The model detected potentially offensive "
                    f"language; estimated rejection likelihood: {rejection_probability:.2f}%."
                )
            elif rejection_probability >= 20:
                reason = (
                    f"The model found some signal for potentially offensive language, but "
                    f"not enough to make rejection likely under the {selected_rating} profile. "
                    f"Estimated rejection likelihood: {rejection_probability:.2f}%."
                )
            else:
                reason = (
                    f"The built-in detector found no explicit blocked term, and the model "
                    f"found little evidence of profanity for the {selected_rating} profile. "
                    f"Estimated rejection likelihood: {rejection_probability:.2f}%."
                )
            results.append(
                RejectionResult(
                    text=text,
                    rating=selected_rating,
                    rejection_probability=rejection_probability,
                    score=raw_score,
                    reason=reason,
                    tier="machine_learning",
                    would_reject=rejection_probability >= 50.0,
                    model_probability=round(model_probability, 6),
                )
            )
        return results

    def _rating_probability_for(self, model_probability: float, rating: str) -> float:
        """Same mapping as _rating_probability, for an item-level rating."""
        epsilon = 1e-6
        p = min(1.0 - epsilon, max(epsilon, model_probability))
        threshold = self.rating_thresholds[rating]
        z = (
            math.log(p / (1.0 - p))
            - math.log(threshold / (1.0 - threshold))
        ) / self.temperature
        if z >= 0:
            result = 1.0 / (1.0 + math.exp(-min(z, 700.0)))
        else:
            ez = math.exp(max(z, -700.0))
            result = ez / (1.0 + ez)
        return self._percentage(result * 100.0)


def score_rejection(
    text: str,
    rating: str = "PG-13",
    **scorer_options: Any,
) -> RejectionResult:
    """Convenience function for a one-off assessment.

    For repeated calls, instantiate :class:`RejectionScorer` once so its adapters
    and model are reused.
    """
    return RejectionScorer(rating=rating, **scorer_options).score(text)
