"""
/account
"""
from urllib.parse import urlparse
from .test_baseclass import TestBase


class TestAccount(TestBase):
    """
    Test /Account
    """
    def test_account_redirect(self):
        """
        GET /account redirects to /account page when user click account tab

        """
        response = self.app.get("/account")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to account when user\
                          is not logged in")

        parsed_url = urlparse(response.location)
        path = parsed_url.path
        self.assertEqual(
            path, "/login",
            "Redirect location is not /login"
        )

    def test_account(self):
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

        response = self.app.get(
            "/account"
        )

        self.assertEqual(response.status_code, 200,
                         "Unable to go to account page for the test user")

        response = self.app.post(
            "/account",
            data={
                "username": "testuser",
                "email": "testuser@testuser.com"}
        )
        self.assertEqual(response.status_code, 302,
                         "Unable to update user info for the test user")


