import pandas as pd
import plotly.graph_objs as go
import requests
from dash import Dash, Input, Output, State, dcc, html

# Our Servers
SERVERS = {
    "Server 1 (My VM)": "http://34.74.77.28:8000/metrics",
    # add teammate servers
}

HISTORY_WINDOW = 60

# Dataframe buffer per server
metrics_history = {
    srv: pd.DataFrame(
        columns=[
            "elapsed_seconds",
            "time_label",
            "cpu_pct",
            "mem_pct",
            "disk_pct",
            "net_rx_kbps",
            "net_tx_kbps",
        ]
    )
    for srv in SERVERS
}

# 3-second increment tracker
elapsed_tracker = {srv: 0 for srv in SERVERS}


app = Dash(__name__)
app.title = "Linux Infrastructure Observability Dashboard"

app.layout = html.Div(
    style={
        "fontFamily": "'Courier New', Courier, monospace",
        "padding": "24px",
        "backgroundColor": "#f3e8ff",
        "minHeight": "100vh",
    },
    children=[
        html.H1(
            "Linux Infrastructure Observability Dashboard",
            style={
                "color": "#2e1065",
                "fontFamily": "'Courier New', Courier, monospace",
            },
        ),
        # Control Panel: Server Selection & Threshold Settings
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                "gap": "16px",
                "padding": "16px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "border": "1px solid #d8b4fe",
                "boxShadow": "0 2px 6px rgba(147, 51, 234, 0.08)",
                "marginBottom": "20px",
                "fontFamily": "'Courier New', Courier, monospace",
            },
            children=[
                html.Div([
                    html.Label(
                        "Target Server:",
                        style={"fontWeight": "bold", "color": "#3b0764"},
                    ),
                    dcc.Dropdown(
                        id="server-selector",
                        options=[
                            {"label": k, "value": k} for k in SERVERS.keys()
                        ],
                        value=list(SERVERS.keys())[0],
                        clearable=False,
                        style={
                            "fontFamily": "'Courier New', Courier, monospace"
                        },
                    ),
                ]),
                html.Div([
                    html.Label(
                        "CPU Alert Threshold (%):",
                        style={"fontWeight": "bold", "color": "#3b0764"},
                    ),
                    dcc.Input(
                        id="cpu-threshold",
                        type="number",
                        value=80,
                        min=1,
                        max=100,
                        style={
                            "width": "100%",
                            "padding": "6px",
                            "fontFamily": "'Courier New', Courier, monospace",
                            "border": "1px solid #d8b4fe",
                            "borderRadius": "4px",
                        },
                    ),
                ]),
                html.Div([
                    html.Label(
                        "Memory Alert Threshold (%):",
                        style={"fontWeight": "bold", "color": "#3b0764"},
                    ),
                    dcc.Input(
                        id="mem-threshold",
                        type="number",
                        value=80,
                        min=1,
                        max=100,
                        style={
                            "width": "100%",
                            "padding": "6px",
                            "fontFamily": "'Courier New', Courier, monospace",
                            "border": "1px solid #d8b4fe",
                            "borderRadius": "4px",
                        },
                    ),
                ]),
                html.Div([
                    html.Label(
                        "Disk Alert Threshold (%):",
                        style={"fontWeight": "bold", "color": "#3b0764"},
                    ),
                    dcc.Input(
                        id="disk-threshold",
                        type="number",
                        value=85,
                        min=1,
                        max=100,
                        style={
                            "width": "100%",
                            "padding": "6px",
                            "fontFamily": "'Courier New', Courier, monospace",
                            "border": "1px solid #d8b4fe",
                            "borderRadius": "4px",
                        },
                    ),
                ]),
            ],
        ),
        # Containers for Cards & Charts
        html.Div(
            id="status-cards-container",
            style={"display": "flex", "gap": "16px", "marginBottom": "20px"},
        ),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "16px",
            },
            children=[
                html.Div(
                    style={
                        "backgroundColor": "#ffffff",
                        "borderRadius": "8px",
                        "padding": "12px",
                        "border": "1px solid #d8b4fe",
                        "boxShadow": "0 2px 6px rgba(147, 51, 234, 0.08)",
                    },
                    children=[dcc.Graph(id="cpu-mem-graph")],
                ),
                html.Div(
                    style={
                        "backgroundColor": "#ffffff",
                        "borderRadius": "8px",
                        "padding": "12px",
                        "border": "1px solid #d8b4fe",
                        "boxShadow": "0 2px 6px rgba(147, 51, 234, 0.08)",
                    },
                    children=[dcc.Graph(id="network-graph")],
                ),
            ],
        ),
        html.Div(
            style={
                "marginTop": "20px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "padding": "24px",
                "border": "1px solid #d8b4fe",
                "boxShadow": "0 2px 6px rgba(147, 51, 234, 0.08)",
            },
            children=[
                dcc.Graph(id="disk-gauge-graph", style={"height": "450px"})
            ],
        ),
        # Polling every 3 seconds
        dcc.Interval(id="interval-poller", interval=3000, n_intervals=0),
    ],
)