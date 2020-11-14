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
    """
    Redirect to dosh route for visualization.
    :return:
    """
    return flask.redirect('/dash_plot')


app_embeds = DispatcherMiddleware(app, {
    '/dash_plot': dash_app.server
})


def fig_update(file_path):
    """
    Given the file path, return an updated fig graph to display.
    :param file_path: string, to get csv file.
    :return: fig, the styled graph.
    """
    graph_data = []
    file_path = file_path
    df = pd.read_csv(file_path)
    graph_data.append({'x': df['date'], 'y': df['pnl']})
    fig = px.line(df, x='date', y='pnl')

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
    """
    Given the file path, return an updated table to display.
    :param table_path: string, to get csv file.
    :return: html.Div, the component in Dash containing table.
    """
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
        ], className="seven columns", style={'margin-top': '35',
                                             'margin-left': '15',
                                             'border': '1px solid #C6CCD5'}
    )


def construct_plot(strategy_names, pnl_paths, table_paths) -> None:
    """
    Construct whole structure of plots by given strategy_names, pnl_paths and table_paths.
    :param strategy_names: A dictionary to map strategy id to strategy name. 
                           Key is strategy id, value is strategy name
    :param pnl_paths: A dictionary to map strategy id to corresponding pnl path of csv file. 
                        Key is strategy id, value is a path string. 
    :param table_paths: A dictionary to map strategy id to corresponding table path of csv file. 
                        Key is strategy id, value is a path string. 
    :return: None
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
        pnl_fig = fig_update(pnl_paths[str_key])
        table_df = pd.read_csv(table_paths[str_key])
        contents.append(
            dcc.Tab(label=str_name, children=[
                html.Div(
                    [
                        html.H1('PnL Plot',
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
                        html.H1('Pyfolio Table',
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

    dash_app.layout = html.Div([
        dcc.Tabs(contents)
    ])


def get_plot():
    strategy_names = {'STRG1': 'Strategy1',
                      'STRG2': 'Strategy2',
                      'STRG3': 'Strategy3'}

    pnl_paths = {'STRG1': './pnl_holder/STRG1.csv',
                 'STRG2': './pnl_holder/STRG2.csv',
                 'STRG3': './pnl_holder/STRG3.csv'}

    table_paths = {'STRG1': './pnl_holder/table1.csv',
                   'STRG2': './pnl_holder/table2.csv',
                   'STRG3': './pnl_holder/table3.csv'}

    construct_plot(strategy_names, pnl_paths, table_paths)


def main():
    # app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')
    get_plot()
    run_simple('0.0.0.0', 5000, app_embeds, use_reloader=True, use_debugger=True)


if __name__ == "__main__":
    main()
