"""
/reset_password
"""
from urllib.parse import urlparse
from .test_baseclass import TestBase


class TestResetPassword(TestBase):
    """
    Test /reset_password
    """
    def test_reset_password_redirect(self):
        """
        GET /reset_password redirects to /reset_password page when user click forget password tab

        """
        response = self.app.get("/reset_password")
        self.assertEqual(response.status_code, 200,
                         "/ did not redirect to reset page")


    def test_reset_pasword(self):
        """post requirest for test users"""
        response = self.app.post(
            "/reset_password",
            data={
                "email": "testuser@testuser.com"}
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to reset password for the test user")

        parsed_url = urlparse(response.location)
        path = parsed_url.path

        # right now, reset page is redirected to login page
        self.assertEqual(
            path, "/login",
            "Redirect location is not /login"
        )

    def test_reset_password_invalid_token(self):
        """
        GET /reset_password redirects to /reset_password page when user click forget password tab

        """
        response = self.app.get("/reset_password/random_token")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to reset page")
