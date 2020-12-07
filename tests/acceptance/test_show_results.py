from .test_baseclass import TestBase


class TestResults(TestBase):
    """
        Test showing results and visualization via Dash.
    """
    def test_view_results(self):
        """
        Common cases 1: Valid user with result page
        '
         User should  be able to see the result page with login.
        '
        """
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")
        response = self.app.get("/results")

        self.assertIn(b"redirect", response.data, "Select Backtest Result")


    def test_invalid_user(self):
        """
        Special cases 1: Invalid user with result page.
        '
         User should not be able to see the selection page without login.
        '
        """
        response = self.app.get("/results")
        self.assertIn(b"redirect", response.data, "Redirect to login.")
