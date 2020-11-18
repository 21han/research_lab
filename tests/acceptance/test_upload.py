"""
/login
"""
from .test_baseclass import TestBase
from urllib.parse import urlparse
from utils import rds
import pandas as pd
import io


class TestUpload(TestBase):
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
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )
        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")
        
        data = {'strategy_name': 'strategy'}
        with open('tests/uploads/helpers.py', 'rb') as fh:
            buf = io.BytesIO(fh.read())
            data['user_file'] = (buf, 'helpers.py')
        response = self.app.post(
            "/upload",
            data=data,
        )
        
        self.assertEqual(response.status_code, 200,
                         "User cannot upload a valid file")
        self.assertIn(b"successful", response.data,
                      "file upload is not shown as successful")
        
         # 11 is testuser
        s3_path = "s3://coms4156-strategies/11/strategy3/helpers.py"
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )
        
        conn = rds.get_connection()
        strategies = pd.read_sql(
            f"select * from backtest.strategies where strategy_location = '{s3_path}';",
            conn
        )
        s_id = strategies['strategy_id'].iloc[0]
        response = self.app.post(
            "/strategy?id="+str(s_id),
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
        response = self.app.post(
            "/login",
            data={
                "email": "testuser@testuser.com",
                "password": "testuser"},
        )
        self.assertEqual(response.status_code, 302,
                         "Unable to login for the test user")
        
        data = {'strategy_name': 'strategy'}
        data['user_file'] = (io.BytesIO(b"invalid file"), 'helpers.py')
        response = self.app.post(
            "/upload",
            data=data,
        )
        
        self.assertEqual(response.status_code, 200,
                         "User cannot upload a valid file")
        self.assertIn(b"error", response.data,
                      "file error cannot be checked")

    def test_upload_empty_file(self):
        """
        special case 1: empty file
        '
        Investment professionals should be able to upload valid strategies and corresponding data with the strategy successfully.
        
        Investment professionals can’t upload invalid strategies and empty data/invalid data files.   
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
        
    # def test_delete_file(self):
    #     """
    #     there is no invalid request at this point
    #     '
    #     Investment professionals should be able to delete any strategies/data/results they don’t want anymore. 
        
    #     NOTE: order matters
    #     '
    #     """
    #     # 11 is testuser
    #     s3_path = "s3://coms4156-strategies/11/strategy2/helpers.py"
    #     response = self.app.post(
    #         "/login",
    #         data={
    #             "email": "testuser@testuser.com",
    #             "password": "testuser"},
    #     )
        
    #     conn = rds.get_connection()
    #     strategies = pd.read_sql(
    #         f"select * from backtest.strategies where strategy_location = '{s3_path}';",
    #         conn
    #     )
    #     s_id = strategies['strategy_id'].iloc[0]
    #     response = self.app.post(
    #         "/strategy?id="+str(s_id),
    #     )
        
    #     # redirect
    #     self.assertEqual(response.status_code, 302,
    #                      "User cannot delete file")