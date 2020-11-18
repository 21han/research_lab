"""
/login
"""
from .test_baseclass import TestBase
from urllib.parse import urlparse


class TestLoginLogout(TestBase):
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
            data={"email": "testuser@testuser.com", "password": "testuser"},
        )
        
        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")
        
        parsed_url = urlparse(response.location)
        path = parsed_url.path
        
        # right now, home is redirected to upload page
        self.assertEqual(
            path, "/upload",
            "Redirect location is not /upload"
        )


