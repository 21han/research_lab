"""
This file contains all the tests for the dash part in application.py
"""

import numpy as np
import pandas as pd
import application as app
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import boto3
from utils import s3_util, rds
from user import OAuthUser
import datetime
from config import S3_BUCKET


TOTAL_CAPITAL = 10 ** 6


def test_annual_return():
    """
    Test for the annual return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-03 12:09:07', '2020-10-04 16:10:05', '2020-10-05 12:03:00'],
                         'pnl': [1000, 1050, -787]})

    result = app.pnl_summary(data)
    ann_return = str(round ( (1000+1050-787) / TOTAL_CAPITAL / (3 / 365) * 100, 2)) + '%'
    assert ann_return == result['Value'].iloc[0]


def test_cumulative_return():
    """
    Test for the cumulative return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [100000, 90000, 75000, -150000]})

    result = app.pnl_summary(data)
    ann_return = str(round(((100000+90000+75000-150000) / TOTAL_CAPITAL) * 100, 2)) + '%'
    assert ann_return == result['Value'].iloc[1]


def test_annual_volatility():
    """
    Test for the annual return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [0, 1000, 900, 750, -1500]})

    std = np.std([1000/TOTAL_CAPITAL, 900/TOTAL_CAPITAL, 750/TOTAL_CAPITAL, -1500/TOTAL_CAPITAL], ddof=1)
    result = app.pnl_summary(data)
    volatility = str(round(std*np.sqrt(365), 2))
    assert volatility == result['Value'].iloc[2]


def test_sharpe_ratio():
    """
    Test for the Sharpe Ratio calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, -800, 950, 600]})

    cum_shift = data['pnl']
    std = np.std(cum_shift, ddof=1)
    mean = cum_shift.mean()
    result = app.pnl_summary(data)
    # round to 2 decimals to be consistent
    sr = str(round(mean / std * np.sqrt(365), 2))
    assert sr == result['Value'].iloc[3]


def test_max_dropdown():
    """
    Test for the Max Dropdown calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = app.pnl_summary(data)
    md = str((1000 - (-1500)) / np.max(data['pnl']))
    # 4th value is dropdown
    assert md == result['Value'].iloc[4]


def test_skew():
    """
    Test for the Skew calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = app.pnl_summary(data)
    sk = str(round(data['pnl'].skew(), 2))
    # 5th value is skew
    assert sk == result['Value'].iloc[5]


def test_kurtosis():
    """
    Test for the kurtosis calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = app.pnl_summary(data)
    kui = str(round(data['pnl'].kurtosis(), 2))
    # 6th value is kurtosis
    assert kui == result['Value'].iloc[6]


def test_layout():
    """
    Test if new_plot() gives a valid layout for dash code.
    :return:
    """
    layout = app.new_plot()
    assert type(layout) == type(html.Div())


def before_test():
    """
    Before testing, add test user and dummy result file.
    :return: user_id, strategy_id
    """
    conn = rds.get_connection()
    cursor = conn.cursor()

    userid = 12345

    # add user
    query = "INSERT IGNORE INTO backtest.user (id, username, email, image_file, password, is_approved, user_type) " \
            f"VALUES ({userid}, 'test', 'test@123.com', 'default.jpg', 'xxx', 'Yes', 'user');"
    cursor.execute(
        query
    )
    conn.commit()

    # upload dummy strategy file
    timestamp = datetime.datetime.now()
    max_id = pd.read_sql(
         "SELECT MAX(strategy_id) FROM backtest.strategies",
        conn
    )

    valid_id = int(max_id.values[0, 0]) + 1
    location = f"s3://coms4156-strategies/{userid}/strategy{valid_id}/dummy.py"
    query = "INSERT INTO backtest.strategies (user_id, strategy_location, strategy_id, " \
        f" last_modified_date, last_modified_user, strategy_name)" \
        f" VALUES ({userid}, '{location}', {valid_id}, '{timestamp}' , 'test_user', 'dummy');"
    cursor.execute(
        query
    )
    conn.commit()

    # upload dummy backtest file
    file_name = "./tests/test_data/dummy_result.csv"
    key = f"tests/{userid}/backtest_{valid_id}.csv"

    _s3_client = s3_util.init_s3_client()
    _s3_client.upload_file(file_name, S3_BUCKET, key)

    query = "REPLACE INTO backtest.backtests (strategy_id, backtest_id," \
            "pnl_location, last_modified_date) \
                    VALUES (%s,%s,%s,%s)"
    cursor.execute(
        query, (valid_id, valid_id,
                f"s3://{S3_BUCKET}/{key}", timestamp)
    )
    conn.commit()

    return userid, str(valid_id)


def test_update_fig():
    """
    Test if fig_update() will return four valid graphs by giving a valid backtest path in s3.
    The return variables are px, go.Figure(), go.Figure() and Dataframe
    :return:
    """
    _, strategy_id = before_test()
    location_df = rds.get_all_locations([strategy_id])
    location = location_df['pnl_location'].iloc[0]
    fig1, fig2, fig3, fig4 = app.fig_update(location)
    assert type(fig1) == type(go.Figure()) and type(fig2) == type(go.Figure()) \
           and type(fig3) == type(go.Figure()) and isinstance(fig4, pd.DataFrame)


def test_update_fig_invalid():
    """
    Test if fig_update() will return four None graphs by giving None for the path.
    :return:
    """
    fig1, fig2, fig3, fig4 = app.fig_update(None)
    assert not fig1 and not fig2 and not fig3 and not fig4


def test_get_plot():
    """
    Test get_plot with valid strategy id list, should return true
    to demonstrate we update global variables in application.
    :return:
    """
    _, strategy_id = before_test()

    # test with this strategy id
    result = app.get_plot([str(strategy_id)])
    assert result


def test_get_plot_invalid():
    """
    Test get_plot with empty list, should return false to demonstrate nothing changed.
    :return:
    """

    result = app.get_plot([])
    assert not result


def test_update_layout():
    """
    Test update_layout with valid user id 0.
    :return:
    """
    user_id, _ = before_test()
    result = app.update_layout(user_id)
    assert result


def test_update_layout_invalid():
    """
    Test update_layout with invalid user id -1. We will never has negative user id.
    :return:
    """

    result = app.update_layout(-1)
    assert not result
