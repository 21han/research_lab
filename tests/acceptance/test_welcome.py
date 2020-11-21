"""
test / or /welcome
"""

from .test_baseclass import TestBase


class TestRoot(TestBase):
    """
    TestRoot
    """
    def test_root_directory(self):
        """
        GET /
        WHEN user go to / directory
        THEN welcome page should appear
        """
        response = self.app.get('/', content_type='html/text')
        self.assertEqual(
            response.status_code,
            200,
            "not able to get to root directory"
        )
        self.assertIn(
            b'Login',
            response.data,
            "not able to find a place to log in"
        )

    def test_welcome_directory(self):
        """
        GET /welcome
        """
        response = self.app.get('/welcome', content_type='html/text')

        self.assertEqual(
            response.status_code,
            200,
            "not able to get to welcome directory"
        )
