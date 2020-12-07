"""
example 0: random strategy
description: trade randomly
character: any better way to lose money?
"""

import datetime
import numpy as np
from utils import mock_historical_data


class Strategy:
    """
    a strategy is a class always named as Strategy and it meets two requirements:
        (1) it has defined trading universe
        (2) it has a run function that returns the portfolio distribution
            of trading universe for a given day
    """

    # trading universe should not be changed after initialization
    trading_universe = [
        'BTC',
        'ETH',
        'BNB',
        'EOS',
        'ATOM',
        'USDT'
    ]

    INIT_CAPITAL = 10 ** 6

    @staticmethod
    def get_position():
        """
        returns the portfolio distribution of trading universe in a given day
        """
        num_strategy = len(Strategy.trading_universe)
        allocation_ls = list(
            np.random.dirichlet(
                np.ones(num_strategy)
            )
        )
        allocation_map = {}
        for i in range(num_strategy):
            allocation_map[
                Strategy.trading_universe[i]
            ] = allocation_ls[i]
        return allocation_map

    @staticmethod
    def get_price():
        """
        get price of symbols in the universe
        :return:
        """
        mk_data = mock_historical_data.MockData
        prices = {}
        for ticker in Strategy.trading_universe:
            prices[ticker] = mk_data.get_price(datetime.datetime.now(), ticker)
        return prices
