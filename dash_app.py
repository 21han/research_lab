import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import numpy as np
import pandas as pd
import plotly.express as px
import sys
from dash import Dash
from utils import s3_util, rds
from config import S3_BUCKET

# create an s3 client
s3_client = s3_util.init_s3_client()
bucket_name = S3_BUCKET

dash_app = Dash(__name__)
dash_app.layout = html.Div()

TOTAL_CAPITAL = 10 ** 6


def fig_update(file_path):
    """
    Given the file path, return an updated fig graph to display.
    :param file_path: string, to get csv file.
    :return: fig, the styled graph.
    """
    graph_data = []

    split_path = file_path.split('/')
    prefix = "/".join(split_path[3:])

    csv_obj = s3_client.get_object(Bucket=bucket_name, Key=prefix)
    pnl_df = pd.read_csv(csv_obj['Body'])

    #pnl_df.rename(columns={'Unnamed: 0': 'date', 'value': 'pnl'}, inplace=True)

    # pnl_df = pd.read_csv(file_path)
    pnl_df['cusum'] = pnl_df['pnl'].cumsum()
    graph_data.append({'x': pnl_df['date'], 'y': pnl_df['cusum']})
    fig = px.line(pnl_df, x='date', y='cusum')

    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    return fig, pnl_df


def make_table(data):
    """
    Given the file path, return an updated table to display.
    :param table_path: string, to get csv file.
    :return: html.Div, the component in Dash containing table.
    """
    return html.Div(
        [
            dt.DataTable(
                data=data.to_dict('rows'),
                columns=[{'id': c, 'name': c} for c in data.columns],
                style_as_list_view=True,
                selected_rows=[],
                style_cell={'padding': '5px',
                            'whiteSpace': 'no-wrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'maxWidth': 0,
                            'height': 30,
                            'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'color': 'black'
                },
                style_cell_conditional=[],
                virtualization=True,
                n_fixed_rows=1
            ),
        ], className="seven columns", style={'margin-top': '35',
                                             'margin-left': '15',
                                             'border': '1px solid #C6CCD5'}
    )


def construct_plot(strategy_names, pnl_paths):
    """
    Construct whole structure of plots by given strategy_names, pnl_paths and table_paths.
    :param strategy_names: A dictionary to map strategy id to strategy name. 
                           Key is strategy id, value is strategy name
    :param pnl_paths: A dictionary to map strategy id to corresponding pnl path of csv file. 
                        Key is strategy id, value is a path string.
    :return: Lively dash layout.
    """

    options = []
    for name in strategy_names.keys():
        options.append({'label': '{}-{}'.format(strategy_names[name], name), 'value': strategy_names[name]})

    TABLE_STYLE = {
        "position": "fixed",
        "top": 70,
        "left": 0,
        "bottom": 5,
        "width": "30rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    CONTENT_STYLE = {
        "margin-left": "32rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    contents = []
    for str_key, str_name in strategy_names.items():
        pnl_fig, pnl_df = fig_update(pnl_paths[str_key])
        table_df = pnl_summary(pnl_df)

        contents.append(
            dcc.Tab(label=str_name, children=[
                html.Div(
                    [
                        html.H1('Cumulative Plot',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(figure=pnl_fig),
                                        width={"size": 8, "offset": 2}),
                            ]
                        )
                    ],
                    style=CONTENT_STYLE
                ),
                html.Div(
                    [
                        html.H1('Statistic Table',
                                style={'font_size': '80',
                                       'text_align': 'center'}),
                        html.Hr(),
                        dt.DataTable(
                            data=table_df.to_dict('records'),
                            columns=[{'id': c, 'name': c} for c in table_df.columns],

                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'Backtest'},
                                    'textAlign': 'left'
                                },

                                {
                                    'if': {'column_id': 'Category'},
                                    'textAlign': 'left'
                                }

                            ],
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'column_id': 'Category'},
                                    'fontWeight': 'bold'
                                }
                            ],
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            }
                        )
                    ],
                    style=TABLE_STYLE
                )

            ])
        )

    return html.Div([dcc.Tabs(contents)])


def get_plot(strategy_ids):
    """
    Get two dictionaries, one mapping from strategy id to strategy name,
    another is mapping from strategy id to strategy location. And then construct dash plot.
    :return:
    """

    backtests = rds.get_all_locations(strategy_ids)
    strategy_names = {}
    pnl_paths = {}
    for idx, id in enumerate(strategy_ids):
        strategy_names[id] = backtests['strategy_name'].iloc[idx]
        pnl_paths[id] = backtests['pnl_location'].iloc[idx]

    dash_app.layout = construct_plot(strategy_names, pnl_paths)


def pnl_summary(data):
    """
    Statistic analysis of backtest result.
    :param data: A dataframe including the backtest results, contains date and pnl two columns.
    :return: A dataframe for making the table, it contains two columns, category name and corresponding values.
    """
    print(data)

    data['cumulative'] = data['pnl'].cumsum()
    result = {'Category': [], 'Value': []}
    total_date = data.shape[0]
    print(total_date)
    # (ending value - initial value) / initial value
    print(data['cumulative'].iloc[-1])
    return_value = (data['cumulative'].iloc[-1]) / TOTAL_CAPITAL

    # Annual return
    annual_return = round(return_value / (total_date / 365) * 100, 2)
    result['Category'].append('Annual Return')
    result['Value'].append(str(annual_return) + '%')

    # Cumulative return
    cumulative_return = round(return_value * 100, 2)
    result['Category'].append('Cumulative Return')
    result['Value'].append(str(cumulative_return) + '%')

    # Annual volatility  -->  every value / 10**6
    daily_change = data['pnl'].iloc[1:].div(TOTAL_CAPITAL)
    #daily_change = daily_change.pct_change()
    annual_volatility = round(daily_change.std() * np.sqrt(365), 2)
    result['Category'].append('Annual Volatility')
    result['Value'].append(str(annual_volatility))

    # Sharpe ratio
    r = data['pnl'].div(TOTAL_CAPITAL)
    sr = round(r.mean() / r.std() * np.sqrt(365), 2)
    result['Category'].append('Sharpe Ratio')
    result['Value'].append(str(sr))

    # Max Dropdown
    md = round((np.max(data['pnl']) - np.min(data['pnl'])) / np.max(data['pnl']), 2)
    result['Category'].append('Max Dropdown')
    result['Value'].append(str(md))

    # Skew
    skew = round(data['pnl'].skew(), 2)
    result['Category'].append('Skew')
    result['Value'].append(str(skew))

    # Kurtosis
    kurtosis = round(data['pnl'].kurtosis(), 2)
    result['Category'].append('Kurtosis')
    result['Value'].append(str(kurtosis))

    return pd.DataFrame(result)


def call_dash(*args):
    """
    Call dash process and construct plot.
    :param args: args should be ids, like 15, 20, 24
    :return:
    """
    ids = [str(item) for item in args[0][1:]]
    get_plot(ids)

    dash_app.run_server(host='127.0.0.1', port=8050, debug=False, threaded=True)


def main(*args):
    """

    :param args:
    :return:
    """
    ids = args[0][1:]
    get_plot(ids)
    app.run_server(debug=False)


if __name__ == "__main__":
    call_dash(sys.argv)

