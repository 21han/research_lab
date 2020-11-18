"""
we will not use real data for this project
we will use mock data instead
"""

import random


class MockData:
    """
    mock data source
    """

    universe = {
        'BTC',
        'ETH',
        'BNB',
        'EOS',
        'USDT',
        'ATOM'
    }  # example trade universe

    balance = 10**6  ## sample balance to mock account info

    def __init__(self):
        pass

    def get_balance(self):
        """
        return current balance
        :return:
        """
        return self.balance

    @staticmethod
    def get_price(date, ticker):
        """
        get ticker price for a particular day
        :param date:
        :param ticker:
        :return:
        """
        if not date:
            raise ValueError("invalid date. you must pass in a date first.")
        ticker = ticker.upper()
        if ticker not in MockData.universe:
            raise ValueError(f"{ticker} is not valid. Valid Tickers are {MockData.universe}")

        random_factor = random.random()
        if ticker == "BTC":
            return random_factor * 20000
        if ticker == "ETH":
            return random_factor * 2500
        if ticker == 'BNB':
            return random_factor * 35
        if ticker == 'EOS':
            return random_factor * 4.5
        if ticker == 'ATOM':
            return random_factor * 5.5
        assert ticker == 'USDT'
        return 1
