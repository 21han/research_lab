"""
/login
"""
import io

import pandas as pd
import time
from config import S3_BUCKET
from random import randint
from utils import rds, s3_util
from .test_baseclass import TestBase


class TestUpload(TestBase):
    """
    TestUpload
    """

    def login(self):
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )
        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")

    def test_can_access_upload_page(self):
        """
        User story:
        User should be able to upload strategy: go to /upload
        endpoint
        """
        self.login()
        response = self.app.get(
            "/upload"
        )
        self.assertIn(b"Upload Your File", response.data,
                      "cannot get to /upload endpoint")

    def test_upload_valid_strategy_and_delete(self):
        """
        Common cases 1.1: valid upload:
        '
        Investment professionals should be able to upload valid strategies and corresponding data with the strategy successfully.
 
        AND

        Common cases 4: delete
        Investment professionals should be able to delete any strategies/data/results they don’t want anymore.
        '
        """
        self.login()
        data = {'strategy_name': 'strategy'}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, 'helpers.py')

        s3 = s3_util.init_s3_client()
        test_id = randint(-1000, -1)

        start = time.time()
        created = False  # if the loop success
        while time.time() - start < 60:
            # 1 minutes in total
            # 11 is testuser
            s3_path = "s3://coms4156-strategies/11/strategy" + str(test_id)
            response = s3.list_objects(
                Bucket=S3_BUCKET,
                Prefix=s3_path
            )
            if "Contents" not in response or \
                    len(response["Contents"] == 0):
                # not exist, create
                created = True
                break
            test_id = randint(-1000, -1)

        if not created:
            assert False, "there is no available spots to create test file"

        response = self.app.post(
            "/upload?test_id=" + str(test_id),
            data=data,
        )

        self.assertEqual(response.status_code, 200,
                         "User cannot upload a valid file")
        self.assertIn(b"successfully", response.data,
                      "file upload is not shown as successful")

        s3_loc = "s3://coms4156-strategies/11/strategy" + str(test_id) + '/helpers.py'
        conn = rds.get_connection()
        strategies = pd.read_sql(
            f"select * from backtest.strategies where strategy_location='{s3_loc}';",
            conn
        )
        s_id = strategies['strategy_id'].iloc[0]
        response = self.app.post(
            "/strategy?id=" + str(s_id),
        )

        # redirect
        self.assertEqual(response.status_code, 302,
                         "User cannot delete file")

    def test_upload_invalid_strategy(self):
        """
        Common cases 1.2 + special case 1: invalid upload:
        '
        Investment professionals should be able to upload valid strategies and corresponding data with the strategy successfully.   
        
        Investment professionals can’t upload invalid strategies and empty data/invalid data files.
        '
        """
        self.login()
        data = {'strategy_name': 'strategy', 'user_file': (io.BytesIO(b"invalid file"), 'helpers.py')}
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertEqual(response.status_code, 200,
                         "User cannot upload a valid file")
        self.assertIn(b"error", response.data,
                      "file error cannot be checked")

    def test_upload_no_strategy_name(self):
        """
        The test strategy name is not there
        """
        self.login()
        data = {}  # no strategy name
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertIn(b"No strategy name specified", response.data,
                      "cannot check no strategy_name field")

    def test_upload_long_strategy_name(self):
        """
        The test strategy name is too long
        """
        self.login()
        data = {'strategy_name': 'a' * 50}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertIn(b"Strategy name should not be greater than 50 characters", response.data,
                      "cannot detect long name")

    def test_upload_lower_boundary_strategy_name(self):
        """
        test strategy name has length 49, boundary is 50.
        """
        self.login()
        data = {'strategy_name': 'a' * 49}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )
        self.assertEqual(response.status_code, 200, "uploaded valid strategy")

    def test_upload_upper_boundary_strategy_name(self):
        """
        test strategy name has length 51, boundary is 50.
        """
        self.login()
        data = {'strategy_name': 'a' * 51}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )
        self.assertIn(b"Strategy name should not be greater than 50 characters", response.data,
                      "cannot detect long name")

    def test_upload_normal_length_strategy_name(self):
        """
        The test strategy with normal length
        """
        self.login()
        data = {'strategy_name': 'a' * 30}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )
        self.assertEqual(response.status_code, 200, "uploaded valid strategy")

    def test_upload_very_long_strategy_name(self):
        """
        The test strategy with very long name
        """
        self.login()
        data = {'strategy_name': 'a' * 100}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertIn(b"Strategy name should not be greater than 50 characters", response.data,
                      "cannot detect very long name")

    def test_upload_empty_file(self):
        """
        special case 1: empty file
        '
        Investment professionals should be able to upload valid strategies and corresponding data with the strategy successfully.
        
        Investment professionals can’t upload invalid strategies and empty data/invalid data files.   
        '
        """
        self.login()
        data = {'strategy_name': 'strategy'}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertEqual(response.status_code, 200,
                         "User cannot upload a valid file")
        self.assertIn(b"select a file", response.data,
                      "cannot check empty file")

    def test_upload_no_user_file(self):
        """
        user cannot upload a data without file
        """
        self.login()
        data = {'strategy_name': 'strategy'}  # no user_file fields
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertIn(b"No user_file is specified", response.data,
                      "cannot check no user_file fiels")

    def test_upload_empty_strategy_name(self):
        """
        strategy name cannot be empty
        """
        self.login()
        data = {'strategy_name': ''}  # no strategy name
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, '')
        response = self.app.post(
            "/upload",
            data=data,
        )

        self.assertIn(b"Strategy name may not be empty", response.data,
                      "cannot check empty strategy_name field")
