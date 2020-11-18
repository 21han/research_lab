"""
this is the test for helper function in app.py
"""

import app
import os
from utils import s3_util
from config import S3_LOCATION, S3_BUCKET

def test_get_strategies():
    """
    get_user_strategies(user_id)
    NOTE: user_id 0 should be fixed
    """
    strategies = app.get_user_strategies(0)
    assert len(strategies.columns) > 0


def test_get_strategy_location():
    """
    get_strategy_location(strategy_id)
    NOTE: strategy_id 15 should be fixed
    """
    location = app.get_strategy_location(15)
    assert location.startswith(S3_LOCATION)


def test_allow_file():
    """
    allow_file(filename)
    """

    assert app.allowed_file("test.py")
    assert not app.allowed_file("test")
    assert not app.allowed_file("test.txt")


def test_upload_strategy():
    """
    test uploading strategies
    """
    prefix = os.path.join('-1/', 'strategy7')
    location = app.upload_strategy_to_s3(
        "tests/uploads/helpers.py",
        S3_BUCKET,
        prefix
        )
    print(location)
    assert location == os.path.join(S3_LOCATION, prefix, 'helpers.py')


def test_delete_strategy():
    """
    test delete strategies
    """
    prefix = os.path.join('-1/', 'strategy7')
    filepath = os.path.join(S3_LOCATION, prefix, 'helpers.py')
    app.delete_strategy_by_user(filepath)
    s3_client = s3_util.init_s3_client()
    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET, Prefix=filepath
    )
    assert response["KeyCount"] == 0

