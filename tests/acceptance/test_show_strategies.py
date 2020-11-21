"""
/login
"""
from .test_baseclass import TestBase


class TestStrategies(TestBase):
    """
        Test Strategies
    """
    def test_view_strategies(self):
        """
        Common cases 2: view tests:
        '
        Investment professionals should choose which strategies to run backtesting.  
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
        response = self.app.get("/strategies")
        self.assertIn(b"Backtest", response.data,
                      "could not run backtests")
