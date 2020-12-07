"""
 admin
"""
from urllib.parse import urlparse
from .test_baseclass import TestBase
import os

class TestAdmin(TestBase):
    """
    Test /Admin
    """

    def test_admin_redirect(self):
        """
        GET /admin redirects to /admin page

        """
        response = self.app.get("/admin")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to admin when admin\
                          is not logged in")

        response = self.app.post(
            "/login",
            data={
                "email": os.getenv('ADMIN_EMAIL'),
                "password": os.getenv('ADMIN_PASSWORD')

            },
        )

        response = self.app.get("/admin")
        self.assertEqual(response.status_code, 302,
                         "/ did not redirect to admin when admin\
                          is not logged in")

        parsed_url = urlparse(response.location)
        path = parsed_url.path

        # right now, admin is redirected to admin home page
        self.assertEqual(
            path, "/admin/",
            "Redirect location is not /admin/"
        )

    def test_admin_user_fail(self):
        """login test users"""
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

        response = self.app.get("/admin/user")
        self.assertEqual(response.status_code, 308,
                         "/ did not redirect to test user to access warning page")

