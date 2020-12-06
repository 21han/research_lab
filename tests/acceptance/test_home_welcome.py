"""
/login
"""
import io

import pandas as pd
import time
from config import S3_BUCKET
from utils import rds, s3_util
from .test_baseclass import TestBase


class TestHomeWelcome(TestBase):
    """
    Test home page and welcome page

    no need to test home redirect because it is in
    test_login_logout.py
    """
    def test_go_home(self):
        """
        user has logged in. should be redirected
        to upload
        """
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )

        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

        response = self.app.get("/home")
        self.assertEqual(response.status_code, 302,
                         "Unable to login and redirect")
        self.assertIn(b"upload", response.data,
                      "cannot get to /upload endpoint")
