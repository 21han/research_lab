"""
helper method for loading data from rds
"""
import os
import pymysql
import pandas as pd

meta = {
    "host": os.getenv('USER_SERVICE_HOST'),
    "user": os.getenv('USER_SERVICE_USER'),
    "password": os.getenv("USER_SERVICE_PASSWORD"),
    "port": int(os.getenv("USER_SERVICE_PORT")),
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    """
    get sql connection
    :return:
    """
    conn = pymysql.connect(**meta)
    return conn


def get_all_strategies(user_id):
    """
    get all strategies of a user
    :param user_id: current user
    :return: strategies in pd.dataframe
    """
    conn = get_connection()
    strategy_df = pd.read_sql(
        f"select * "
        f"from backtest.strategies  "
        f"where user_id = {user_id}",
        conn
    )
    return strategy_df
