"""
/login
"""
from .test_baseclass import TestBase
import logging

class TestStrategies(TestBase):
    """
        Test Strategies
    """
    def login(self):
        self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

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

    def test_display_strategy(self):
        """
        test display strategy
        :return:
        """
        self.login()
        resp = self.app.get('/strategy?id=371')
        self.assertEqual(resp.status_code, 200)

    def test_backtest_progress(self):
        """
        test backtest progress
        :return:
        """
        self.login()
        resp = self.app.get("/backtest_progress?id=371")
        self.assertEqual(resp.status_code, 200)
