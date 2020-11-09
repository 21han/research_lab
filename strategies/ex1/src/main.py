"""
an example strategy file

takes in a sample of random data between -1 and 1 for each timestamp (at daily interval)

for each day, if random data > 0.5, we will convert to all BTC; else, we will convert to all USDT

compute PnL each day
"""

import random
import datetime
import pandas as pd

# TODO: convert this into a user upload field
SAMPLE_DATA = pd.DataFrame({
    'date': [datetime.datetime.today() - datetime.timedelta(days=i) for i in range(100)],
    'data': [random.randrange(-1, 1) for _ in range(100)]
})


def strategy(data):
    # take in data and return this datetime's realied PnL
    return random.randrange(-10000, 10000)


# TODO: user shouldn't be uploading this part of this code. We shoud handle this in application logic
date, pnl = [], []
for i, r in SAMPLE_DATA.iterrows():
    date.append(r['date'])
    pnl.append(strategy(r))

print(pd.DataFrame({
    'date': date,
    'pnl': pnl
}))
