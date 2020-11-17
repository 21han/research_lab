"""
base class for pytest

alchemist

"""

import unittest
# import sh
from app import app


class TestBase(unittest.TestCase):
    def setUp(self):
        """
        start app test client, and login to linxiaow 
        This function runs once before each member function unit test.
        """
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
        somethin to restore
        like reset db if necessary
        """
        self.app_context.pop()
