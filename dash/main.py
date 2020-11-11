# This is a sample Dash template.

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px

# Initialize the dash app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div()


@app.callback(
    Output('my_close_price_graph', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [State('my_pnl_symbol', 'value')])
def update_graph(n_clicks, title):
    graph_data = []

    # TODO: need to modify this.
    path = title+'.csv'
    df = pd.read_csv(path)
    graph_data.append({'x': df['date'], 'y': df['pnl']})
    fig = px.line(df, x='date', y='pnl', title='PNL with' + title)

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

if __name__ == '__main__':

    # Create a sidebar with stock to select

    # TODO: need to modify this.
    str_name_dic = {'STRG1': 'Strategy1', 'STRG2': 'Strategy2', 'STRG3': 'Strategy3'}
    options = []
    for ticker in str_name_dic:
        options.append({'label': '{}-{}'.format(str_name_dic[ticker], ticker), 'value': ticker})

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
            html.H2("PnL", className="display-4"),
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
                    dbc.Col(dcc.Graph(id="my_close_price_graph"),
                            width={"size": 8, "offset": 2}),
                ]
            )
        ],
        style=CONTENT_STYLE
    )

    app.layout = html.Div([sidebar, content])
    app.run_server(port='8083')


