import unittest

from original_message_display import message_to_marquee_html, uses_all_letters


class FullLetterAnswerTests(unittest.TestCase):
    def test_requires_the_same_letter_counts(self):
        self.assertTrue(uses_all_letters("BOX LETTER!", "LETTER BOX"))
        self.assertFalse(uses_all_letters("LET BOX", "LETTER BOX"))
        self.assertFalse(uses_all_letters("BOX LETTERS", "LETTER BOX"))
        self.assertFalse(uses_all_letters("ANYTHING", ""))

    def test_marquee_can_show_full_letter_star(self):
        html = message_to_marquee_html("BOX LETTER", include_assets=False, all_letters_used=True)

        self.assertIn('class="marquee-full-letter-star"', html)
        self.assertIn("★", html)

    def test_marquee_without_full_letter_use_has_no_star(self):
        html = message_to_marquee_html("BOX", include_assets=False)

        self.assertNotIn("marquee-full-letter-star", html)
