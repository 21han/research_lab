"""
tset OAuth login
"""
from .test_baseclass import TestBase
import pytest


class TestOauthLogin(TestBase):
    """
    Test Oauth Login
    """

    def test_oauth_redirect(self):
        """
        GET /OAuth_login
        """
        response = self.app.get("/OAuth_login")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to google login page when user\
                          is not logged in")

    def test_invalid_oauth_callback(self):
        """
        GET /OAuth_login/callback with invalid code
        """
        with pytest.raises(Exception):
            self.app.get("/OAuth_login/callback?code=123", base_url="https://localhost")
