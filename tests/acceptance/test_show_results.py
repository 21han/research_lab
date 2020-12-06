from .test_baseclass import TestBase


class TestResults(TestBase):
    """
        Test showing results and visualization via Dash.
    """

    def test_invalid_user(self):
        """
        Special cases 1: Invalid user with selection page.
        '
         User should not be able to see the selection page without login.
        '
        """
        response = self.app.get("/results")
        self.assertIn(b"redirect", response.data, "Redirect to login.")
