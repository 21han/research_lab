"""
/register
"""
from urllib.parse import urlparse

from utils import rds
from .test_baseclass import TestBase


class TestRegister(TestBase):
    """
    Test register a user
    """

    def test_register_directory(self):
        """
        GET /register
        """
        response = self.app.get('/register', content_type='html/text')

        self.assertEqual(
            response.status_code,
            200,
            "not able to get to register directory"
        )

    def test_register_page(self):
        """Verify links and form on /register/ page."""
        response = self.app.get("/register")
        self.assertEqual(response.status_code, 200,
                         "Could not access /register route")
        self.assertIn(b"Register", response.data,
                      "Couldn't find link to /register")

    def test_register(self):
        """test register users"""
        response = self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "000",
                "email": "000@0.com",
                "password": "000",
                "confirm_password": "000"
            },
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to register for the test user")

        parsed_url = urlparse(response.location)
        path = parsed_url.path

        self.assertEqual(
            path, "/login",
            "Redirect location is not /login"
        )

        conn = rds.get_connection()
        cursor = conn.cursor()
        query = "delete from backtest.user where username = '000';"
        cursor.execute(
            query
        )
        conn.commit()

    def test_register_short_username(self):
        """
        test register a user with username shorter than 2 characters
        """
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "1",
                "email": "1@1.com",
                "password": "1234567",
                "confirm_password": "1234567"
            },
        )

        self.assertEqual(response.status_code, 200,
                         "can register a test user with username shorter than 2 characters")

    def test_register_longer_username(self):
        """
        test register a user with username longer than 20 characters
        """
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "abcdefghijklmnopqrstuvwxyz",
                "email": "abcdefghijklmnopqrstuvwxyz@1.com",
                "password": "1234567",
                "confirm_password": "1234567"
            },
        )

        self.assertEqual(response.status_code, 200,
                         "can register a test user with username longer than 20 characters")
