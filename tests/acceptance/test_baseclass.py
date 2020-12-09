"""
base class for pytest

alchemist

"""

import unittest
from application import application


class TestBase(unittest.TestCase):
    """
    Test Base
    """

    def setUp(self):
        """
        start application test client,
        This function runs once before each member function unit test.
        """
        application.config['TESTING'] = True
        application.config['WTF_CSRF_ENABLED'] = False
        self.app = application.test_client()
        self.app_context = application.app_context()
        self.app_context.push()
        self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@testuser.com",
                "password": "testusertestuser",
                "confirm_password": "testusertestuser"
            },
        )

    def tearDown(self):
        """
        something to restore
        like reset db if necessary
        """
        self.app_context.pop()
