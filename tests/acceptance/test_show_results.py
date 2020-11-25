from .test_baseclass import TestBase


class TestResults(TestBase):
    """
        Test showing results and visualization via Dash.
    """

    def test_view_results(self):
        """
        Common cases 1: Valid user with selection page.
        '
        Investment professionals can see all the backtest results
        and choose which one to display.
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

        self.assertIn(b"Select backtest result(s) to visualize, "
                      b"max 5 results can be selected.", response.data,
                      "Selection page.")

    def test_invalid_user(self):
        """
        Special cases 1: Invalid user with selection page.
        '
         User should not be able to see the selection page without login.
        '
        """
        response = self.app.get("/results")
        self.assertIn(b"redirect", response.data, "Redirect to login.")
