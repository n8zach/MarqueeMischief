import unittest
from unittest.mock import patch

from .rejection_scorer import (
    ModerationVerdict,
    RejectionScorer,
    _OpenAIModerationAdapter,
)
from .screening import ensure_ready, screen_message


class StubDetector:
    def __init__(self, blocked=False):
        self.blocked = blocked

    def contains_profanity(self, text):
        return self.blocked


class StubModel:
    def __init__(self, verdict):
        self.verdict = verdict
        self.calls = []

    def moderate(self, text, rating):
        self.calls.append((text, rating))
        return self.verdict


class RejectionScorerTests(unittest.TestCase):
    def test_word_list_rejection_skips_openai(self):
        model = StubModel(ModerationVerdict(verdict="PASS", reason="No issue found."))
        scorer = RejectionScorer(detector=StubDetector(blocked=True), model=model)

        result = scorer.score("blocked content")

        self.assertTrue(result.rejected)
        self.assertEqual(result.tier, "deterministic")
        self.assertEqual(model.calls, [])

    def test_openai_pass_fail_results_have_no_scores(self):
        for verdict, rejected in (("PASS", False), ("FAIL", True)):
            with self.subTest(verdict=verdict):
                model = StubModel(ModerationVerdict(verdict=verdict, reason="Reviewed."))
                scorer = RejectionScorer(detector=StubDetector(), model=model)

                result = scorer.score("candidate message")

                self.assertEqual(result.rejected, rejected)
                self.assertEqual(result.tier, "openai")
                self.assertEqual(result.to_dict()["reason"], "Reviewed.")
                self.assertEqual(result.to_dict()["verdict"], verdict)
                self.assertNotIn("rejected", result.to_dict())
                self.assertNotIn("score", result.to_dict())
                self.assertNotIn("rejection_probability", result.to_dict())
                self.assertEqual(model.calls, [("candidate message", "PG-13")])

    def test_screening_response_uses_verdict(self):
        scorer = RejectionScorer(
            detector=StubDetector(),
            model=StubModel(ModerationVerdict(verdict="PASS", reason="Suitable.")),
        )

        result = screen_message("candidate message", scorer=scorer).to_dict()

        self.assertEqual(result["verdict"], "PASS")
        self.assertNotIn("rejected", result)
        self.assertNotIn("score", result)

    def test_empty_text_does_not_call_openai(self):
        model = StubModel(ModerationVerdict(verdict="PASS", reason="No issue found."))
        scorer = RejectionScorer(detector=StubDetector(), model=model)

        result = scorer.score("  ")

        self.assertFalse(result.rejected)
        self.assertEqual(result.tier, "empty")
        self.assertEqual(model.calls, [])

    @patch("profanity_filter.screening.RejectionScorer")
    def test_readiness_does_not_make_an_openai_request(self, scorer_class):
        self.assertTrue(ensure_ready("TEST-NO-API-WARMUP"))
        scorer_class.return_value.score.assert_not_called()

    def test_openai_adapter_uses_structured_responses(self):
        expected = ModerationVerdict(verdict="FAIL", reason="Graphic violence.")

        class FakeResponses:
            def parse(self, **kwargs):
                self.kwargs = kwargs
                return type("Response", (), {"output_parsed": expected})()

        responses = FakeResponses()
        adapter = _OpenAIModerationAdapter(
            client=type("Client", (), {"responses": responses})()
        )

        actual = adapter.moderate("message", "PG-13")

        self.assertEqual(actual, expected)
        self.assertEqual(responses.kwargs["model"], "gpt-4.1-mini")
        self.assertIs(responses.kwargs["text_format"], ModerationVerdict)
        self.assertFalse(responses.kwargs["store"])


if __name__ == "__main__":
    unittest.main()
