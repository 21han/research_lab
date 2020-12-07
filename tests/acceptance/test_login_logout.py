"""
/login
"""
from urllib.parse import urlparse

from .test_baseclass import TestBase
from utils import rds

class TestLoginLogout(TestBase):
    """
    TestLoginLogout
    """
    def test_home_redirect(self):
        """
        GET /home redirects to /login when user is not logged in.

        Functions that start with "test" are automatically run by the unittest
        framwork.  The framework also takes care of running setUp() before each
        member function test begins and running tearDown() after each ends.
        """
        response = self.app.get("/home")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to login when user\
                          is not logged in")

        parsed_url = urlparse(response.location)
        path = parsed_url.path
        self.assertEqual(
            path, "/login",
            "Redirect location is not /login"
        )

    def test_login_content_page(self):
        """Verify links and form on /login/ page."""
        response = self.app.get("/login")
        self.assertEqual(response.status_code, 200,
                         "Could not access /login route")
        self.assertIn(b"Register", response.data,
                      "Couldn't find link to /register")

    def test_login(self):
        """login test users"""
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

        parsed_url = urlparse(response.location)
        path = parsed_url.path

        # right now, home is redirected to upload page
        self.assertEqual(
            path, "/home",
            "Redirect location is not /home"
        )

    def test_login_fail(self):
        """login test users"""
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "wrong"},
        )

        self.assertEqual(response.status_code, 200,
                         "Can login the test user with wrong password")


    def test_admin_login(self):
        """login test users"""
        response = self.app.post(
            "/login",
            data={
                "email": "admin@admin.com",
                "password": "admin"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the admin user")

        parsed_url = urlparse(response.location)
        path = parsed_url.path

        # right now, home is redirected to upload page
        self.assertEqual(
            path, "/admin",
            "Redirect location is not /admin"
        )

    def test_persiste_login(self):
        """login test users"""
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

        response = self.app.get("/login")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to login when user\
                          is not logged in")

        parsed_url = urlparse(response.location)
        path = parsed_url.path
        self.assertEqual(
            path, "/home",
            "Redirect location is not /home"
        )

    def test_logout(self):
        """logout test user"""
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

        logout_response = self.app.get('/logout', content_type='html/text')

        self.assertEqual(
                logout_response.status_code,
                302,
                "not able to logout"
        )

    def test_login_without_approve(self):
        """
        test user login without admin approved
        :return:
        """
        response = self.app.post(
            "/register",
            data={
                "username": "not_approve",
                "email": "need@approve.com",
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

        response = self.app.post(
            "/login",
            data={
                "email": "need@approve.com",
                "password": "000"},
        )

        conn = rds.get_connection()
        cursor = conn.cursor()
        query = "delete from backtest.user where username = 'not_approve';"
        cursor.execute(
            query
        )
        conn.commit()

        self.assertEqual(response.status_code, 200,
                         "can login for the unapproved user")

