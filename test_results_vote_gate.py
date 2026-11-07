import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import flask_app


class TestUser:
    id = 7
    is_authenticated = True

    def get_id(self):
        return str(self.id)


class ResultsVoteGateTests(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = "7"
            session["_fresh"] = True

    def test_private_results_require_a_vote(self):
        game = SimpleNamespace(id=42, code="private-game")
        with (
            patch("flask_app.get_user_from_id", return_value=TestUser()),
            patch("flask_app.get_game_with_puzzle", return_value=(game, "PUZZLE")),
            patch("flask_app.has_submitted_in_game", return_value=True),
            patch("flask_app.has_voted_in_game", return_value=False),
            patch("flask_app.message_to_marquee_html", return_value=""),
            patch("flask_app.get_game_results_text") as get_results,
        ):
            response = self.client.get("/results?gameId=42")

        self.assertIn(b"You must vote on this game before viewing the results.", response.data)
        self.assertIn(b'href="/vote/?gameId=42"', response.data)
        get_results.assert_not_called()

    def test_daily_results_are_available_without_a_vote(self):
        selected_day = date(2026, 11, 1)
        game = SimpleNamespace(id=43)
        answers = [(None, None, None, False)]
        with (
            patch("flask_app.get_user_from_id", return_value=TestUser()),
            patch("flask_app._daily_today", return_value=selected_day + timedelta(days=2)),
            patch("flask_app.get_daily_game", return_value=game),
            patch("flask_app.has_voted_in_game", return_value=False) as has_voted,
            patch("flask_app.get_game_with_puzzle", return_value=(game, "PUZZLE")),
            patch("flask_app.message_to_marquee_html", return_value=""),
            patch("flask_app.get_game_user_answer_votes", return_value=answers) as get_answers,
            patch("flask_app.get_game_results_text", return_value="DAILY RESULTS") as get_results,
            patch(
                "flask_app._daily_calendar_context",
                return_value={
                    "calendar_month": selected_day,
                    "calendar_weeks": [],
                    "previous_month": "2026-10",
                    "next_month": "2026-12",
                },
            ),
        ):
            response = self.client.get(f"/daily/results/?date={selected_day.isoformat()}")

        self.assertNotIn(b"You must vote on this game before viewing the results.", response.data)
        self.assertNotIn(b'href="/daily/vote/"', response.data)
        self.assertIn(b"DAILY RESULTS", response.data)
        has_voted.assert_not_called()
        get_answers.assert_called_once_with(game.id)
        get_results.assert_called_once_with(game.id)


if __name__ == "__main__":
    unittest.main()
