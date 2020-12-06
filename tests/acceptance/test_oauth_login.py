"""
tset OAuth login
"""
from .test_baseclass import TestBase


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

    def test_oauth_callback(self):
        """
        GET /OAuth_login/callback
        """
        response = self.app.get("/OAuth_login")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to google login callback page when user\
                          is not logged in")
