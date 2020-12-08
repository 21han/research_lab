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
        """test register a user with valid input info"""
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "12345",
                "email": "12345@0.com",
                "password": "abc.1234567890",
                "confirm_password": "abc.1234567890"
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
        query = "delete from backtest.user where username = '12345';"
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
                "password": "12345678900",
                "confirm_password": "12345678900"
            },
        )
        self.assertEqual(response.status_code, 200,
                         "register a user with username shorter than 2 characters")

    def test_register_long_username(self):
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
                "password": "12345678900",
                "confirm_password": "12345678900"
            },
        )
        self.assertEqual(response.status_code, 200,
                         "register a user with username longer than 20 characters")

    def test_register_with_valide_password(self):
        """
        test register a user with valid password
        """
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "12345",
                "email": "12345@0.com",
                "password": "abc.1234567890",
                "confirm_password": "abc.1234567890"
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
        query = "delete from backtest.user where username = '12345';"
        cursor.execute(
            query
        )
        conn.commit()

    def test_register_short_password(self):
        """
        test register a user with password shorter than 10 characters
        """
        self.app.get(
            "/register"
        )
        response = self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@testuser.com",
                "password": "123",
                "confirm_password": "123"
            },
        )
        self.assertEqual(response.status_code, 200,
                         "register a user with password shorter than 10 characters")

    def test_register_long_password(self):
        """
        test register a user with password longer than 100 characters
        """
        self.app.get(
            "/register"
        )
        response = self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@testuser.com",
                "password": "1234567"*100,
                "confirm_password": "1234567"*100
            },
        )
        self.assertEqual(response.status_code, 200,
                         "register a user with password longer than 100 characters")

    def test_register_unique_characters_password(self):
        """
        test register a user with password contains at least 5 unique characters
        """
        """
        test register a user with valid password
        """
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "12345",
                "email": "12345@0.com",
                "password": "abc.1234567890",
                "confirm_password": "abc.1234567890"
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
        query = "delete from backtest.user where username = '12345';"
        cursor.execute(
            query
        )
        conn.commit()


    def test_register_duplicate_characters_password(self):
        """
        test register a user with password contains less than 5 unique characters
        """
        """
        test register a user with valid password
        """
        self.app.get(
            "/register"
        )

        response = self.app.post(
            "/register",
            data={
                "username": "12345",
                "email": "12345@0.com",
                "password": "123123123123",
                "confirm_password": "123123123123"
            },
        )
        self.assertEqual(response.status_code, 200,
                         "Unable to register for the test user")
