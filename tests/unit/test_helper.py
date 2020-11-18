"""
this is the test for helper function in app.py
"""

import app
from config import S3_LOCATION

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
    need local file , pass for now
    """
    pass

def 

