"""
helper method for loading data from rds
"""
import os

import pandas as pd
import pymysql

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
        f"SELECT bs.user_id, bs.strategy_id, "
        f"bs.last_modified_date, bs.last_modified_user, bs.strategy_name "
        f"FROM backtest.strategies bs "
        f"JOIN ("
        f" SELECT strategy_name, "
        f" MAX(last_modified_date) as last_modified_date "
        f" FROM backtest.strategies "
        f" GROUP BY strategy_name "
        f") AS lm on bs.strategy_name = lm.strategy_name "
        f"AND bs.last_modified_date=lm.last_modified_date "
        f"WHERE user_id = {user_id}",
        conn
    )
    return strategy_df


def get_all_backtests(user_id):
    """
    get all backtest results of a user
    :param user_id: current user
    :return: backtest results in pd.dataframe
    """
    conn = get_connection()

    backtest_df = pd.read_sql(
        f" SELECT s.strategy_name, s.strategy_id, b.backtest_id,"
        f" b.pnl_location, b.last_modified_date "
        f" FROM backtest.strategies s "
        f" LEFT JOIN backtest.backtests b ON s.strategy_id = b.strategy_id "
        f" WHERE s.user_id = {user_id} AND b.pnl_location is not null"
        f" ORDER BY b.last_modified_date;",
        conn
    )

    return backtest_df


def get_all_locations(strategy_ids):
    """
    get all pnl locations from a list of strategy_ids
    :param strategy_ids: a list of strategy ids
    :return: backtest results in pd.dataframe
    """
    conn = get_connection()
    # cast int array to str array just in case
    strategy_ids = [str(i) for i in strategy_ids]
    ids = "( " + ",".join(strategy_ids) + " )"

    backtest_df = pd.read_sql(
        f" SELECT s.strategy_name, b.pnl_location"
        f" FROM backtest.strategies s"
        f" LEFT JOIN backtest.backtests b ON s.strategy_id = b.strategy_id"
        f" WHERE b.strategy_id in {ids} AND b.pnl_location is not null"
        f" ORDER BY b.last_modified_date; ",
        conn
    )

    return backtest_df
