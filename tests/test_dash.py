"""
This file contains all the tests for the dash_single.py
"""

import dash_app
import pandas as pd
import numpy as np


def test_annual_return():
    """
    Test for the annual return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-03 12:09:07', '2020-10-04 16:10:05', '2020-10-05 12:03:00'],
                         'pnl': [1000, 1050, -787]})

    result = dash_app.pnl_summary(data)
    ann_return = str(round(((1000+1050-787) - 1000) / 1000 / (3 / 365) * 100, 2)) + '%'
    assert ann_return == result['Value'].iloc[0]


def test_cumulative_return():
    """
    Test for the cumulative return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = dash_app.pnl_summary(data)
    ann_return = str(round((((1000+900+750-1500) - 1000)/1000) * 100, 2)) + '%'
    assert ann_return == result['Value'].iloc[1]


def test_annual_volatility():
    """
    Test for the annual return calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})
    std = np.std([1000, 900, 750, -1500], ddof=1)
    result = dash_app.pnl_summary(data)
    volatility = str(round(std*np.sqrt(252), 2)) + '%'
    assert volatility == result['Value'].iloc[2]


def test_sharpe_ratio():
    """
    Test for the Sharpe Ratio calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, -800, 950, 600]})

    cum_shift = data['pnl'].cumsum().diff()
    std = np.std(cum_shift, ddof=1)
    mean = cum_shift.mean()
    result = dash_app.pnl_summary(data)
    sr = str(round(mean / std * np.sqrt(252), 2) )
    assert sr == result['Value'].iloc[3]


def test_max_dropdown():
    """
    Test for the Max Dropdown calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = dash_app.pnl_summary(data)
    md = str((1000 - (-1500)) / np.max(data['pnl']))
    assert md == result['Value'].iloc[4]


def test_skew():
    """
    Test for the Skew calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = dash_app.pnl_summary(data)
    sk = str(round(data['pnl'].skew(), 2))
    assert sk == result['Value'].iloc[5]


def test_kurtosis():
    """
    Test for the kurtosis calculation.
    :return:
    """
    data = pd.DataFrame({'date': ['2020-10-04 12:09:07', '2020-10-05 16:10:05',
                                  '2020-10-06 12:01:00', '2020-10-07 17:00:00'],
                         'pnl': [1000, 900, 750, -1500]})

    result = dash_app.pnl_summary(data)
    kui = str(round(data['pnl'].kurtosis(), 2))
    assert kui == result['Value'].iloc[6]

