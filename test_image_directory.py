import unittest
from unittest.mock import patch

import flask_app


class TestUser:
    id = 7
    is_authenticated = True

    def get_id(self):
        return str(self.id)


class ImageDirectoryTests(unittest.TestCase):
    def setUp(self):
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_site_images_use_configured_subdirectory(self):
        self.assertEqual(flask_app.app.config["IMAGE_DIRECTORY"], flask_app.IMAGE_DIRECTORY)

        with self.client.session_transaction() as session:
            session["_user_id"] = "7"
            session["_fresh"] = True

        with patch("flask_app.get_user_from_id", return_value=TestUser()):
            home_response = self.client.get("/")
            coming_soon_response = self.client.get("/coming-soon/")

        for filename in (
            "MainBanner.JPG",
            "evil.png",
            "laughingcolor.jfif",
            "Laughing.jfif",
            "friendly.jfif",
            "dancing.jfif",
        ):
            self.assertIn(f"/static/images/primary/{filename}".encode(), home_response.data)

        self.assertIn(b"/static/images/primary/b&wLaughing.png", coming_soon_response.data)

        for filename in (
            "MainBanner.JPG",
            "evil.png",
            "laughingcolor.jfif",
            "Laughing.jfif",
            "friendly.jfif",
            "dancing.jfif",
            "b&wLaughing.png",
            "laughing.jpg",
            "evil.jpg",
            "thinking.gif",
        ):
            response = self.client.get(f"/static/images/primary/{filename}")
            self.assertEqual(response.status_code, 200, filename)

        original_directory = flask_app.app.config["IMAGE_DIRECTORY"]
        try:
            flask_app.app.config["IMAGE_DIRECTORY"] = "alternate"
            response = self.client.get("/coming-soon/")
            self.assertIn(b"/static/images/alternate/b&wLaughing.png", response.data)
        finally:
            flask_app.app.config["IMAGE_DIRECTORY"] = original_directory


if __name__ == "__main__":
    unittest.main()
