"""

"""
from flask import Flask
from flask import render_template
import sqlite3
from flask import request
import logging
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


def get_user_strategies(user_id):
    conn = sqlite3.connect("alchemist.db")
    strategies = pd.read_sql(f"select * from strategies where user_id = {user_id};", conn)
    return strategies


@app.route('/strategies')
def all_strategy():
    # TODO remove hard code of user after integration with Michael
    current_user_id = 0
    all_user_strategies = get_user_strategies(current_user_id)

    # display all user strategy as a table on the U.I.
    return render_template('strategies.html', df=all_user_strategies)


def get_strategy_location(strategy_id):
    conn = sqlite3.connect("alchemist.db")
    strategies = pd.read_sql(
        f"select * from strategies where strategy_id = {strategy_id};",
        conn
    )
    s_loc = strategies['strategy_location'].iloc[0]
    logger.info(f"[db] - {s_loc}")
    return s_loc


@app.route('/strategy')
def display_strategy():
    strategy_id = request.args.get('id')
    strategy_location = get_strategy_location(strategy_id)
    with open(f"strategies/{strategy_location}/src/main.py") as f:
        code_snippet = f.read()
    return render_template('strategy.html', code=code_snippet)





def main():
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')


if __name__ == "__main__":
    main()
