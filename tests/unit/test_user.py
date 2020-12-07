"""
test user
"""

from user import OAuthUser
from utils import rds
import pandas as pd
import logging


def test_Oauth_user():
    """
    create user
    :return:
    """
    user = OAuthUser(
        id_="123456", username="test_user", email="test_email", image_file="default.img"
    )
    user.create("123456", "test_user", "test_email", "default.img")
    assert user.get_id() == "123456"


def test_create_Oauth_user():
    """
    create user
    :return:
    """
    user = OAuthUser(
        id_="123456", username="test_user", email="test_email", image_file="default.img"
    )
    user.create("123456", "test_user", "test_email", "default.img")
    conn = rds.get_connection()
    userid = pd.read_sql(
        "select id from backtest.OAuth_user where email = 'test_email';",
        conn
    )
    current_user_id = str(userid['id'].iloc[0])
    cursor = conn.cursor()
    query = "delete from backtest.OAuth_user where username = 'test_user';"
    cursor.execute(
        query
    )
    conn.commit()
    assert current_user_id == "123456"


def test_get_Oauth_user():
    """
    create user
    :return:
    """
    user = OAuthUser(
        id_="123456", username="test_user", email="test_email", image_file="default.img"
    )
    user.create("123456", "test_user", "test_email", "default.img")
    conn = rds.get_connection()
    current_user = user.get("123456")
    current_user_name = current_user.username
    name = str(current_user_name['username'].iloc[0])
    logging.info(type(name))
    cursor = conn.cursor()
    query = "delete from backtest.OAuth_user where username = 'test_user';"
    cursor.execute(
        query
    )
    conn.commit()
    assert name == "test_user"
