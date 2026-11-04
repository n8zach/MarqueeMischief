import unittest
from unittest.mock import patch

import flask_app


class RegistrationAuthorizationCodeTests(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_registration_code_from_url_is_hidden(self):
        response = self.client.get("/register?authorization_code=invite-code")

        self.assertIn(b'type="hidden" name="authorization_code" value="invite-code"', response.data)
        self.assertNotIn(b'<label for="authorization_code">', response.data)

    def test_registration_code_field_remains_visible_without_url_code(self):
        response = self.client.get("/register")

        self.assertIn(b'<label for="authorization_code">Authorization code</label>', response.data)
        self.assertNotIn(b'type="hidden" name="authorization_code"', response.data)

    def test_registration_uses_authorization_code_from_url(self):
        with patch("flask_app.add_user", return_value=(True, "success")) as add_user:
            response = self.client.post(
                "/register?authorization_code=invite-code",
                data={"username": "player", "password": "password"},
            )

        add_user.assert_called_once_with("player", "password", "invite-code")
        self.assertEqual(response.status_code, 302)

    def test_registration_uses_manually_entered_authorization_code(self):
        with patch("flask_app.add_user", return_value=(True, "success")) as add_user:
            response = self.client.post(
                "/register",
                data={
                    "username": "player",
                    "password": "password",
                    "authorization_code": "manual-code",
                },
            )

        add_user.assert_called_once_with("player", "password", "manual-code")
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
