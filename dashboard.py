import pandas as pd
import plotly.graph_objs as go
import requests
from dash import Dash, Input, Output, State, dcc, html

# Our Servers
SERVERS = {
    "Server 1 (My VM)": "http://34.74.77.28:8000/metrics",
    # add teammate servers
}

FONT_FAMILY = "Courier New, monospace"
HISTORY_WINDOW = 60

# Dataframe buffer per server
metrics_history = {
    srv: pd.DataFrame(
        columns=[
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

def create_stat_card(title, value, unit, threshold, is_online):
    """Build metric alert card with dynamic colors."""
    if not is_online:
        return html.Div(
            style={
                "flex": "1",
                "backgroundColor": "#f0f0f0",
                "padding": "12px",
                "borderRadius": "6px",
                "border": "1px solid #ccc",
                "textAlign": "center",
            },
            children=[
                html.H4(title, style={"margin": "0 0 5px 0"}),
                html.H2("N/A", style={"margin": "0"}),
                html.Span("OFFLINE", style={"color": "red", "fontSize": "12px", "fontWeight": "bold"}),
            ],
        )

    alert = value >= threshold
    bg_color = "#ffd2d2" if alert else "#ffffff"
    text_color = "#b30000" if alert else "#330033"
    border_style = "2px solid red" if alert else "1px solid #d8b4fe"
    status_msg = "CRITICAL" if alert else "NORMAL"

    return html.Div(
        style={
            "flex": "1",
            "backgroundColor": bg_color,
            "padding": "12px",
            "borderRadius": "6px",
            "border": border_style,
            "textAlign": "center",
        },
        children=[
            html.H4(title, style={"margin": "0 0 5px 0", "color": "#333"}),
            html.H2(f"{value:.1f} {unit}", style={"margin": "0", "color": text_color}),
            html.Span(status_msg, style={"fontSize": "11px", "fontWeight": "bold", "color": text_color}),
        ],
    )

app = Dash(__name__)
app.title = "Linux Infrastructure Observability Dashboard"

app.layout = html.Div(
    style={
        "fontFamily": FONT_FAMILY,
        "padding": "20px",
        "backgroundColor": "#f3e8ff",
        "minHeight": "100vh",
    },
    children=[
        html.H1(
            "Linux Infrastructure Observability Dashboard",
            style={"color": "#2e1065"},
        ),

        # Control Panel: Server Selection & Threshold Settings
        html.Div(
            style={
                "display": "flex",
                "gap": "15px",
                "padding": "15px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "border": "1px solid #d8b4fe",
                "marginBottom": "20px",
            },
            children=[
                html.Div(
                    style={"flex": "2"},
                    children=[
                        html.Label("Target Server:", style={"fontWeight": "bold", "color": "#3b0764"}),
                        dcc.Dropdown(
                            id="server-selector",
                            options=[{"label": k, "value": k} for k in SERVERS.keys()],
                            value=list(SERVERS.keys())[0],
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("CPU Alert Threshold (%):", style={"fontWeight": "bold", "color": "#3b0764"}),
                        dcc.Input(
                            id="cpu-threshold",
                            type="number",
                            value=80,
                            min=1,
                            max=100,
                            style={"width": "100%", "padding": "6px"},
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("Memory Alert Threshold (%):", style={"fontWeight": "bold", "color": "#3b0764"}),
                        dcc.Input(
                            id="mem-threshold",
                            type="number",
                            value=80,
                            min=1,
                            max=100,
                            style={"width": "100%", "padding": "6px"},
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1"},
                    children=[
                        html.Label("Disk Alert Threshold (%):", style={"fontWeight": "bold", "color": "#3b0764"}),
                        dcc.Input(
                            id="disk-threshold",
                            type="number",
                            value=85,
                            min=1,
                            max=100,
                            style={"width": "100%", "padding": "6px"},
                        ),
                    ],
                ),
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
                    },
                    children=[dcc.Graph(id="cpu-mem-graph")],
                ),
                html.Div(
                    style={
                        "backgroundColor": "#ffffff",
                        "borderRadius": "8px",
                        "padding": "12px",
                        "border": "1px solid #d8b4fe",
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
            },
            children=[
                dcc.Graph(id="disk-gauge-graph", style={"height": "450px"})
            ],
        ),

        # Polling every 3 seconds
        dcc.Interval(id="interval-poller", interval=3000, n_intervals=0),
    ],
)

@app.callback(
    [
        Output("status-cards-container", "children"),
        Output("cpu-mem-graph", "figure"),
        Output("network-graph", "figure"),
        Output("disk-gauge-graph", "figure"),

    ],
    [Input("interval-poller", "n_intervals"), Input("server-selector", "value")],
    [
        State("cpu-threshold", "value"),
        State("mem-threshold", "value"),
        State("disk-threshold", "value"),
    ],
)

def update_dashboard(n_interval, selected_server, cpu_thresh, mem_thresh, disk_thresh):
    if selected_server not in metrics_history:
        metrics_history[selected_server] = pd.DataFrame(
            columns=["time_label", "cpu_pct", "mem_pct", "disk_pct", "net_rx_kbps", "net_tx_kbps"]
        )
        elapsed_tracker[selected_server] = 0

    endpoint = SERVERS[selected_server]
    is_online = True
    active_stress = "IDLE"
    data = {"cpu_pct": 0, "mem_pct": 0, "disk_pct": 0, "net_rx_kbps": 0, "net_tx_kbps": 0}

    try:
        resp = requests.get(endpoint, timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            active_stress = data.get("active_stress", "IDLE")
        else:
            is_online = False
    except Exception:
        is_online = False

    # Time step tracking (increments by 3s)
    current_sec = elapsed_tracker[selected_server]
    time_label = f"{current_sec}s"
    elapsed_tracker[selected_server] += 3

    new_entry = {
        "time_label": time_label,
        "cpu_pct": data.get("cpu_pct", 0),
        "mem_pct": data.get("mem_pct", 0),
        "disk_pct": data.get("disk_pct", 0),
        "net_rx_kbps": data.get("net_rx_kbps", 0),
        "net_tx_kbps": data.get("net_tx_kbps", 0),
    }

    df = metrics_history[selected_server]
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True).tail(HISTORY_WINDOW)
    metrics_history[selected_server] = df

    cards = [
        create_stat_card("CPU Usage", new_entry["cpu_pct"], "%", cpu_thresh or 80, is_online),
        create_stat_card("Memory Usage", new_entry["mem_pct"], "%", mem_thresh or 80, is_online),
        create_stat_card("Disk Usage", new_entry["disk_pct"], "%", disk_thresh or 85, is_online),
        html.Div(
            style={"flex": "1", "backgroundColor": "#fff", "padding": "12px", "borderRadius": "6px", "border": "1px solid #d8b4fe", "textAlign": "center"},
            children=[
                html.H4("Network I/O", style={"margin": "0 0 5px 0"}),
                html.H3(f"RX: {new_entry['net_rx_kbps']:.1f} KB/s", style={"margin": "0", "color": "#0055cc"}),
                html.H3(f"TX: {new_entry['net_tx_kbps']:.1f} KB/s", style={"margin": "0", "color": "#7a00cc"}),
            ],
        ),
        html.Div(
            style={
                "flex": "1",
                "backgroundColor": "#ede9fe" if active_stress != "IDLE" else "#faf5ff",
                "padding": "12px",
                "borderRadius": "6px",
                "border": "1px solid #c4b5fd" if active_stress != "IDLE" else "1px solid #e9d5ff",
                "textAlign": "center",
            },
            children=[
                html.H4("Pipe Stress Event", style={"margin": "0 0 5px 0"}),
                html.H4(f"{active_stress}", style={"margin": "8px 0 0 0", "color": "#5b21b6" if active_stress != "IDLE" else "#777"}),
            ],
        ),
    ]


