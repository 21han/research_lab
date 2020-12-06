"""
this is the test for helper function in application.py
"""

import application as app
import os
import pytest
from utils import s3_util
from config import S3_LOCATION, S3_BUCKET
from boto3.exceptions import S3UploadFailedError


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
    location = app.get_strategy_location(41)
    assert location.startswith(S3_LOCATION)


def test_allow_file():
    """
    allow_file(filename)
    """

    assert app.allowed_file("test.py")
    assert not app.allowed_file("test")
    assert not app.allowed_file("test.txt")


def test_wrongly_upload_strategy():
    """
    programmers may upload strategy in a wrong way
    """
    prefix = os.path.join('-1/', 'strategy7')

    with pytest.raises(S3UploadFailedError):
        app.upload_strategy_to_s3(
            "tests/uploads/helpers.py",
            "Wrong_S3_PATH",
            prefix
        )


def test_upload_and_delete_strategy():
    """
    test uploading strategies
    also deleting it afterwards
    """
    prefix = os.path.join('-1/', 'strategy7')
    location = app.upload_strategy_to_s3(
        "tests/uploads/helpers.py",
        S3_BUCKET,
        prefix
        )
    assert location == os.path.join(S3_LOCATION, prefix, 'helpers.py')

    # delete
    prefix = os.path.join('-1/', 'strategy7')
    filepath = os.path.join(S3_LOCATION, prefix, 'helpers.py')
    app.delete_strategy_by_user(filepath)
    s3_client = s3_util.init_s3_client()
    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET, Prefix=filepath
    )
    assert response["KeyCount"] == 0


def test_compute_pnl():
    """
    test compute total value
    :return:
    """
    # case 1: when all is None, we just initialized, return PnL for init today (un-traded state) is 0
    assert app.compute_pnl(None, None, None, None) == 0

    # case 2: date is not None, position is non-empty; and we made profit
    assert app.compute_pnl(
        {'BTC': 0.2, 'ETH': 0.8},
        {'BTC': 9, 'ETH': 1.5},
        {'BTC': 10, 'ETH': 2}, 100) == (100*0.2/9)*10+(100*0.8/1.5)*2-100

    # case 3: case we made loss
    assert app.compute_pnl(
        {'BTC': 0.2, 'ETH': 0.8},
        {'BTC': 10, 'ETH': 2},
        {'BTC': 9, 'ETH': 1.5}, 100) == (100*0.2/10)*9+(100*0.8/2)*1.5-100


def test_clean_pylint():
    """
    test if pylint output has clean output
    """

    pylint_message = (
        '''************* Module user\n'''
        '''strategies/2/strategy2/user.py:15: convention (C0103,'''
        '''invalid-name, OAuthUser.__init__) Attribute name "id"'''
        '''doesn't conform to snake_case naming style\n'''
        '''\n'''
        '''--------------------------------'''
        '''----------------------------------\n'''
        '''Your code has been rated at 9.62/10 '''
        '''(previous run: 9.62/10, +0.00)'''
    )

    clean_message = app.clean_pylint_output(pylint_message)
    assert "strategies/2/strategy2/" not in clean_message, \
        "do not clean the pylint output!"
