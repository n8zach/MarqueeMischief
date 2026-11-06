import re
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

    def test_daily_results_require_a_vote(self):
        selected_day = date(2026, 11, 1)
        game = SimpleNamespace(id=43)
        with (
            patch("flask_app.get_user_from_id", return_value=TestUser()),
            patch("flask_app._daily_today", return_value=selected_day + timedelta(days=2)),
            patch("flask_app.get_daily_game", return_value=game),
            patch("flask_app.has_voted_in_game", return_value=False),
            patch("flask_app.get_game_with_puzzle", return_value=(game, "PUZZLE")),
            patch("flask_app.message_to_marquee_html", return_value=""),
            patch("flask_app.get_game_user_answer_votes") as get_answers,
            patch("flask_app.get_game_results_text") as get_results,
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

        self.assertIn(b"You must vote on this game before viewing the results.", response.data)
        self.assertIn(b'href="/daily/vote/"', response.data)
        get_answers.assert_not_called()
        get_results.assert_not_called()

    def test_calendar_highlights_results_and_yesterday(self):
        today = date(2026, 1, 1)
        result_day = date(2025, 12, 30)
        yesterday = date(2025, 12, 31)
        result_game = SimpleNamespace(id=42)
        yesterday_game = SimpleNamespace(id=43)
        games = {result_day: result_game, yesterday: yesterday_game}

        for voted in (False, True):
            with (
                self.subTest(voted=voted),
                patch("flask_app.get_user_from_id", return_value=TestUser()),
                patch("flask_app._daily_today", return_value=today),
                patch("flask_app.get_daily_game", side_effect=games.get),
                patch("flask_app.get_daily_game_dates", return_value=set(games)),
                patch("flask_app.has_voted_in_game", side_effect=lambda user_id, game_id: voted if game_id == 43 else True),
                patch("flask_app.get_game_with_puzzle", return_value=None),
                patch("flask_app.get_game_user_answer_votes", return_value=[]),
                patch("flask_app.get_game_results_text", return_value=""),
            ):
                response = self.client.get("/daily/results/?date=2025-12-30&month=2026-01")
                redirect_response = self.client.get("/daily/date/2025-12-30")

            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            result_cell = re.search(r'<td class="([^"]*results-date[^"]*)">\s*(.*?)\s*</td>', html, re.DOTALL)
            voting_cell = re.search(r'<td class="([^"]*voting-date[^"]*)">\s*(.*?)\s*</td>', html, re.DOTALL)
            self.assertIsNotNone(result_cell)
            self.assertIn('href="/daily/date/2025-12-30"><strong>30</strong>', result_cell.group(2))
            self.assertIsNotNone(voting_cell)
            self.assertIn("outside-month", voting_cell.group(1))
            self.assertIn('href="/daily/vote/"', voting_cell.group(2))
            self.assertEqual("<strong>31</strong>" in voting_cell.group(2), not voted)
            self.assertLess(html.index("Blue dates"), html.index('<table class="daily-calendar"'))
            self.assertEqual(redirect_response.location, "/daily/results/?date=2025-12-30")

    def test_yesterday_without_a_game_still_links_to_voting(self):
        with (
            patch("flask_app.get_user_from_id", return_value=TestUser()),
            patch("flask_app._daily_today", return_value=date(2026, 1, 1)),
            patch("flask_app.get_daily_game", return_value=None),
            patch("flask_app.get_daily_game_dates", return_value=set()),
            patch("flask_app.has_voted_in_game") as has_voted,
        ):
            response = self.client.get("/daily/results/")

        self.assertIn(b'href="/daily/vote/"><strong>31</strong></a>', response.data)
        has_voted.assert_not_called()


if __name__ == "__main__":
    unittest.main()
