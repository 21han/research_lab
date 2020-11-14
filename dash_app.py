from dash import Dash
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import flask
from werkzeug.serving import run_simple
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import dash_table as dt

app = flask.Flask(__name__)
dash_app = Dash(__name__, server=app, url_base_pathname='/plots/')
dash_app.layout = html.Div()


@app.route('/')
@app.route('/hello')
def hello():
    return 'hello world!'


@app.route('/plots/')
def render_reports():
    return flask.redirect('/dash_plot')


app_embeds = DispatcherMiddleware(app, {
    '/dash_plot': dash_app.server
})


@dash_app.callback(
    Output('my_pnl_graph', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [State('my_pnl_symbol', 'value')])
def update_graph(n_clicks, strategy_path):
    """
    Update graph based on the clicked graph.
    :param strategy_name: Strategy name.
    :param file_path: Strategy file path.
    :return:
    """

    graph_data = []
    file_path = strategy_path
    df = pd.read_csv(file_path)
    graph_data.append({'x': df['date'], 'y': df['pnl']})
    fig = px.line(df, x='date', y='pnl', title='PNL plot')

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


def fig_update(file_path):
    graph_data = []
    file_path = file_path
    df = pd.read_csv(file_path)
    graph_data.append({'x': df['date'], 'y': df['pnl']})
    fig = px.line(df, x='date', y='pnl', title='PNL plot')

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


def make_table(table_path):

    data = pd.read_csv(table_path)
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
    ], className="seven columns", style = {'margin-top': '35',
                                           'margin-left': '15',
                                           'border': '1px solid #C6CCD5'}
    )

def construct_plot():
    # Create a sidebar with stock to select
    strategy_names = {'STRG1': 'Strategy1',
                      'STRG2': 'Strategy2',
                      'STRG3': 'Strategy3'}

    paths = {'STRG1': './pnl_holder/STRG1.csv',
             'STRG2': './pnl_holder/STRG2.csv',
             'STRG3': './pnl_holder/STRG3.csv'}

    # TODO: Get data from RDB instead of local
    ''' 
    user_id = 0
    strategy_ids = get_user_strategies(user_id)
    strategy_paths = { get_strategy_location(str_id) : str_id for str_id in strategy_ids}
    '''

    options = []
    for name in strategy_names.keys():
        options.append({'label': '{}-{}'.format(strategy_names[name], name), 'value': paths[name]})

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
    '''
    content = html.Div(children=[
        # All elements from the top of the page
        html.Div([
            html.Div(
                [
                    html.H1('PnL Plot',
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
            ),

            html.Div(
                [
                    html.H1('Table',
                            style={'textAlign': 'center'}),
                    html.Hr(),
                    dbc.Table.from_dataframe(df='my_table', striped=True, bordered=True, hover=True)
                ],
                style=CONTENT_STYLE
            ),
        ]),
    ])

    dash_app.layout = html.Div([content])
    '''

    strategy_names = {'STRG1': 'Strategy1',
                      'STRG2': 'Strategy2',
                      'STRG3': 'Strategy3'}

    paths = {'STRG1': './pnl_holder/STRG1.csv',
             'STRG2': './pnl_holder/STRG2.csv',
             'STRG3': './pnl_holder/STRG3.csv'}

    table_paths= {'STRG1': './pnl_holder/table1.csv',
                  'STRG2': './pnl_holder/table2.csv',
                  'STRG3': './pnl_holder/table3.csv'}


    contents = []
    for str_key, str_name in strategy_names.items():
        contents.append(
            dcc.Tab(label=str_name, children=[
                html.Div(
                    [
                        html.H1('PnL Plot',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(figure=fig_update(paths[str_key])) ) # ,
                                        #width={"size": 8, "offset": 2}),
                            ]
                        )
                    ],
                    style=CONTENT_STYLE
                ),
                html.Div(
                    [
                        html.H1('Pyfolio Table',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Table.from_dataframe(pd.read_csv(table_paths[str_key]),
                                                 striped=True, bordered=False, hover=False)
                    ],
                    style=CONTENT_STYLE
                )

            ])
        )

    dash_app.layout = html.Div([
        dcc.Tabs(contents)
    ])


def main():
    # app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')
    construct_plot()
    run_simple('0.0.0.0', 5000, app_embeds, use_reloader=True, use_debugger=True)


if __name__ == "__main__":
    main()
