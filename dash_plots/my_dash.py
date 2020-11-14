# This is a sample Dash template.

import dash_plots
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_plots.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from flask import Flask

# Initialize the dash_plots app
dashapp = dash_plots.Dash(__name__, requests_pathname_prefix='/dash_plots/', external_stylesheets=[dbc.themes.BOOTSTRAP])
dashapp.layout = html.Div('dash_plots test')

@dashapp.callback(
    Output('my_pnl_graph', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [State('my_pnl_symbol', 'value')])
def update_graph(n_clicks, strategy_name):
    """
    Update graph based on the clicked graph.
    :param strategy_name: Strategy name.
    :param file_path: Strategy file path.
    :return:
    """

    graph_data = []
    file_path = strategy_name + '.csv'
    df = pd.read_csv(file_path)
    graph_data.append({'x': df['date'], 'y': df['pnl']})
    fig = px.line(df, x='date', y='pnl', title='PNL with' + strategy_name)

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
    return fig

def plotting():
    """
    Plotting the PnL results, including graph, table and should be able to compare different results.
    :return:
    """
    # Create a sidebar with stock to select
    strategy_paths = {'STRG1': 'Strategy1', 'STRG2': 'Strategy2', 'STRG3': 'Strategy3'}
    user_id = 0
    # strategy_ids = get_user_strategies(user_id)
    # strategy_paths = { get_strategy_location(str_id) : str_id for str_id in strategy_ids}
    options = []
    for str_path in strategy_paths:
        options.append({'label': '{}-{}'.format(strategy_paths[str_path], str_path), 'value': str_path})

    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "30rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    controls = dbc.Card(
        [
            dbc.FormGroup(
                [
                    dcc.Dropdown(
                        id='my_pnl_symbol',
                        options=options,
                        value='PnL'
                    ),
                    dbc.Button(
                        id='submit-button',
                        n_clicks=0,
                        children='Submit',
                        color="primary",
                        block=True
                    ),
                ]
            )
        ],
    )

    sidebar = html.Div(
        [
            html.H2("PnL Dashboard", className="display-4"),
            html.Hr(),
            controls
        ],
        style=SIDEBAR_STYLE,
    )

    CONTENT_STYLE = {
        "margin-left": "32rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }
    content = html.Div(
        [
            html.H1('Personal PnL Dashboard',
                    style={'textAlign': 'center'}),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="my_pnl_graph"),
                            width={"size": 8, "offset": 2}),
                ]
            )
        ],
        style=CONTENT_STYLE
    )

    dashapp.layout = html.Div([sidebar, content])



if __name__ == "__main__":

    plotting()
    dashapp.run_server(port=8083)
