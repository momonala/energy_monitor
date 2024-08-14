import sqlite3
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import logging
from utils import print_value

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.YETI, dbc.icons.FONT_AWESOME],
)
app.title = "Energy Monitor"
server = app.server
app.config["suppress_callback_exceptions"] = False

dash.clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark");
       return window.dash_clientside.no_update
    }
    """,
    Output("switch", "id"),
    Input("switch", "value"),
)


def _fetch_data(query: str) -> pd.DataFrame:
    with sqlite3.connect("data/energy_data.db") as conn:
        df = pd.read_sql(query, conn, parse_dates=["timestamp"])
    return df


def fetch_data(dt: datetime) -> pd.DataFrame:
    dt = dt.strftime('%Y-%m-%d %H:%M:%S')
    query = f"""
    SELECT * FROM energy_measurements
    WHERE timestamp >= '{dt}'
    """
    return _fetch_data(query)


def fetch_latest_data() -> pd.DataFrame:
    query = """
        SELECT * 
        FROM energy_measurements
        ORDER BY timestamp DESC
        LIMIT 1
    """
    return _fetch_data(query)


# fmt: off
last_value_style = {"width": "100px", "textAlign": "center", "fontSize": "24px"}
app.layout = dash.html.Div(
    [
        dash.html.Div(
            [
                dash.html.H2("Energy Monitor", style={"padding-left": "10px", "padding-bottom": "2px"}),
                dash.html.H5(children="", id="timestamp", style={"padding-left": "10px", "padding-top": "2px"}),

                dash.html.Div(
                    [
                        dash.html.Label("Lookback minutes:", style={"marginRight": "10px"}),
                        dash.dcc.Input(id="minutes-input", type="text", value="5", style={"width": "100px"}),
                        dash.html.Span(
                            [
                                dbc.Label(className="fa fa-moon", html_for="switch"),
                                dbc.Switch(id="switch", value=True, className="d-inline-block ms-1", persistence=True),
                                dbc.Label(className="fa fa-sun", html_for="switch"),
                            ], style={"marginLeft": "20px"},
                        ),
                    ],
                    style={"marginBottom": "5px", "padding": "10px", "display": "inline-block", "float": "left"},
                ),
            ], style={"display": "inline-block"},
        ),
        dash.html.Div(
            [
                dash.html.Div(
                    [dash.html.Label("Voltage (V)"), dash.html.Div(id='voltage-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Current (A)"), dash.html.Div(id='current-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Power (W)"), dash.html.Div(id='power-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Energy (kWh)"), dash.html.Div(id='energy-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Freq (Hz)"), dash.html.Div(id='freq-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Power Factor"), dash.html.Div(id='pf-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
                dash.html.Div(
                    [dash.html.Label("Cost (€)"), dash.html.Div(id='cost-value', style=last_value_style)],
                    style={"display": "inline-block", "width": "120px"},
                ),
            ],
            style={"marginLeft": "80px", "textAlign": "center", "fontFamily": "Arial", "display": "inline-block"},
        ),
        dash.dcc.Graph(id="combined-graph", style={"marginTop": "0px"}),
        dash.dcc.Interval(id="interval-live", interval=int(0.5 * 1000), n_intervals=0),
        dash.dcc.Interval(id="interval-graph", interval=int(1 * 1000), n_intervals=0),
    ]
)
# fmt: on


@app.callback(
    [
        Output("timestamp", "children"),
        Output("voltage-value", "children"),
        Output("current-value", "children"),
        Output("power-value", "children"),
        Output("energy-value", "children"),
        Output("freq-value", "children"),
        Output("pf-value", "children"),
        Output("cost-value", "children"),
    ],
    [Input("interval-live", "n_intervals")],
)
def update_latest_values(n_intervals):
    df = fetch_latest_data()
    last_row = df.iloc[-1] if not df.empty else pd.Series()
    latest_time = last_row.get('timestamp', None)
    if latest_time:
        latest_time = latest_time.strftime('%Y-%m-%d %H:%M:%S')

    return (
        latest_time,
        print_value(last_row.get('voltage', 0)),
        print_value(last_row.get('current', 0), 3),
        print_value(last_row.get('power', 0)),
        print_value(last_row.get('energy', 0), 3),
        print_value(last_row.get('frequency', 0)),
        print_value(last_row.get('pf', 0)),
        print_value(last_row.get('cost', 0), 4),
    )


@app.callback(
    [
        Output("interval-graph", "disabled"),
        Output("combined-graph", "figure"),
    ],
    [Input("interval-graph", "n_intervals"), Input("minutes-input", "value")],
)
def update_graphs(n_intervals, minutes):
    max_points_to_show = 9000
    rolling_window_size = 10

    # Ensure minutes is a positive integer
    try:
        minutes = int(eval(minutes))
        if minutes <= 0:
            minutes = 15
    except (ValueError, SyntaxError):
        minutes = 15

    # Disable interval if minutes > 60
    interval_disabled = minutes > 60

    # Filter data for the last N minutes
    start_time = datetime.now() - pd.Timedelta(minutes=minutes)
    df = fetch_data(start_time)
    logger.debug(f"Fetched data for {start_time=} {df.shape=}")
    filtered_df = df[df["timestamp"] >= start_time]
    sampling_freq = int(len(filtered_df) / max_points_to_show)
    if sampling_freq > 1:
        filtered_df = filtered_df[::sampling_freq]
        # Apply rolling average
        for column in filtered_df.columns:
            if column != "timestamp":
                filtered_df[column] = filtered_df[column].rolling(window=rolling_window_size, min_periods=1, center=True).mean()

    # Create subplots with a shared x-axis
    columns_to_plot = (
        ("current", "Current (A)"),
        ("power", "Power (W)"),
        ("energy", "Energy (kWh)"),
        ("pf", "Power Factor"),
        ("cost", "Cost (€)"),
    )
    fig = make_subplots(
        rows=len(columns_to_plot),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.01,
    )
    axes_titles = {}
    for i, (pd_col, plot_title) in enumerate(columns_to_plot):
        fig.add_trace(
            go.Scatter(x=filtered_df["timestamp"], y=filtered_df[pd_col], mode="lines", name=plot_title),
            row=i + 1,
            col=1,
        )
        axes_titles[f"yaxis{i+1}"] = dict(title=plot_title, title_standoff=15, side="left")

    fig.update_layout(
        height=650,
        showlegend=True,
        margin=dict(l=40, r=40, t=10, b=10),
        xaxis5=dict(title="Time", title_standoff=15, side="bottom"),
        **axes_titles,
    )
    return interval_disabled, fig


if __name__ == "__main__":
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_serve_dev_bundles=True)
    app.run_server(debug=True, port=8050)
