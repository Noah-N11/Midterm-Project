import pandas as pd
import plotly.graph_objs as go
import requests
from dash import Dash, Input, Output, State, dcc, html, ctx, ALL
from datetime import datetime
import time

#This code imports the notification system and the data collection system so that the dashboard can use them.
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "monitor-features" / "notifications"))
sys.path.insert(0, str(PROJECT_DIR / "monitor-features" / "data_collection"))

from notification_system import check_notification
from data_collector import metric_collection

# Our Servers
SERVERS = {
    #"Server 1": "http://34.74.77.28:8000/metrics",

    #Temporary Test Server
    "Server 1": "http://127.0.0.1:8000/metrics",

    "Server 2": "http://35.255.80.106:8000/metrics",
    "Server 3": "http://34.44.252.24:8000/metrics",

    # add last server
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

def create_stat_card(title, value, unit, threshold, is_online, mode = "custom", minimum_severity = "HIGH"):
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

    result = check_notification(title, value, mode = mode, threshold = threshold, minimum_severity = minimum_severity)
    alert = result["alert"]
    status_msg = result["status"]

    bg_color = "#ffd2d2" if alert else "#ffffff"
    text_color = "#b30000" if alert else "#330033"
    border_style = "2px solid red" if alert else "1px solid #d8b4fe"

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
        html.Div(
            style = {
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "gap": "20px",
                "marginBottom": "15px",
            },

            children = [
                html.H1(
            "Linux Infrastructure Observability Dashboard",
            style={"color": "#2e1065"},
            ),
            
            html.Div(
                style = {
                    "display": "flex",
                    "alignItems": "end",
                    "gap": "15px",
                    "flexShrink": "0"
                },

                children = [
                    html.Button(
                        "Server Notifications",
                        id = "server-notifications-button",
                        n_clicks = 0,
                        style = {
                            "padding": "9px 14px",
                            "borderRadius": "8px",
                            "border": "1px solid",
                            "backgroundColor": "#ffffff",
                            "color": "#3b0764",
                            "fontFamily": FONT_FAMILY,
                            "cursor": "pointer"
                        }
                    ),

                    html.Div(
                        style = {"width": "240px", "flexShrink": "0"},
                        children = [
                            html.Label("Notification Mode:"),
                            dcc.Dropdown(
                                id = "notification-mode",
                                options = [
                                    {"label": "Custom Threshold", "value": "custom"},
                                    {"label": "Preset Severity", "value": "preset"},
                                ],

                                value = "custom",
                                clearable = False,
                            ),
                        ],
                    ),
                ],
            ),
            ],
        ),

        #Server Notification Window: Allows the user to choose whether they get notified about all servers or only the currently selected server. Also has a log
        #where the user can see when notifications were sent, what server caused the notification to be sent out, and the specifics on why the notification was sent
        #out.
        html.Div(
            id = "notification-window",
            style = {
                "display": "none",
                "position": "fixed",
                "top": "100px",
                "right": "30px",
                "width": "450px",
                "maxWidth": "90vw",
                "maxHeight": "75vh",
                "backgroundColor": "#ffffff",
                "border": "1px solid",
                "borderRadius": "12px",
                "padding": "20px",
                "boxShadow": "0 8px 25px rgba(0, 0, 0, 0.2)",
                "zIndex": "1000",
                "overflowY": "auto"
            },

            children = [
                html.Div(
                    style = {
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center"
                    },

                    children = [
                        html.H3(
                            "Server Notifications",
                            style = {"margin": "0", "color": "#3b0764"}
                        ),

                        html.Button(
                            "X",
                            id = "close-notifications-button",
                            n_clicks = 0,
                            style = {
                                "border": "none",
                                "backgroundColor": "transparent",
                                "fontSize": "20px",
                                "cursor": "pointer"
                            }
                        )
                    ]
                ),

                html.Label(
                    "Notify Me About:",
                    style = {"display": "block", "marginTop": "20px"}
                ),

                dcc.Dropdown(
                    id = "notification-scope",
                    options = [
                        {"label": "Selected Server Only", "value": "selected"},
                        {"label": "All Running Servers", "value": "all"}
                    ],

                    value = "selected",
                    clearable = False,
                    searchable = False
                ),

                html.H4(
                    "Notification Log",
                    style = {"marginTop": "20px", "color": "#3b0764"}
                ),

                html.Div(
                    id = "notification-log",
                    style = {
                        "height": "250px",
                        "overflowY": "auto",
                        "border": "1px solid",
                        "borderRadius": "8px",
                        "padding": "10px"
                    },

                    children = [
                        html.P(
                            "No Notifications Yet.",
                            style = {"color": "#777", "textAlign": "center"}
                        )
                    ]
                )
            ]
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
                    id = "custom-settings",
                    style = {
                        "display": "flex",
                        "flex": "3",
                        "gap": "15px",
                    },

                    children = [

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

        #Dropdown Menu For Preset Mode
        html.Div(
            id = "preset-settings",
            style = {
                "display": "none",
                "gap": "15px",
            },

            children = [
                html.Div(
                    style = {"flex": "1"},
                    children = [
                        html.Label("CPU Minimum Severity:"),
                        dcc.Dropdown(
                            id = "cpu-severity",
                            options = [
                                {"label": s, "value": s}
                                for s in ["NORMAL", "HIGH", "CRITICAL"]
                            ],

                            value = "HIGH",
                            clearable = False,
                            searchable = False,
                        ),
                    ],
                ),

                html.Div(
                    style = {"flex": "1"},
                    children = [
                        html.Label("Memory Minimum Severity:"),
                        dcc.Dropdown(
                            id = "mem-severity",
                            options = [
                                {"label": s, "value": s}
                                for s in ["NORMAL", "HIGH", "CRITICAL"]
                            ],

                            value = "HIGH",
                            clearable = False,
                            searchable = False,
                        ),
                    ],
                ),

                html.Div(
                    style = {"flex": "1"},
                    children = [
                        html.Label("Disk Minimum Severity:"),
                        dcc.Dropdown(
                            id = "disk-severity",
                            options = [
                                {"label": s, "value": s}
                                for s in ["NORMAL", "HIGH", "CRITICAL"]
                            ],

                            value = "HIGH",
                            clearable = False,
                            searchable = False,
                        ),
                    ],
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

        #This code is meant to store the notification history for your current browser session.
        dcc.Store(
            id = "notification-history",
            storage_type = "memory",
            data = []
        ),

        #This code tracks any duplicate notifications to ensure that the same notification isn't being sent out every 3 seconds.
        dcc.Store(
            id = "active-notifications",
            storage_type = "memory",
            data = {}
        ),

        #This code tracks the pop-up notifications that appear.
        dcc.Store(
            id = "notification-toast-state",
            storage_type = "memory",
            data = {"seen_count": 0, "popups": []}
        ),

    html.Div(
        id = "notification-toast-container",
        style = {
            "position": "fixed",
            "bottom": "20px",
            "left": "20px",
            "width": "350px",
            "maxWidth": "90vw",
            "zIndex": "1000",
            "display": "flex",
            "flexDirection": "column",
            "gap": "10px",
            "pointerEvents": "none"
        },

        children = []
    ),

    # Polling every 3 seconds
    dcc.Interval(id="interval-poller", interval=3000, n_intervals=0),
    ],
)

@app.callback(
    Output("notification-window", "style"),
    Input("server-notifications-button", "n_clicks"),
    Input("close-notifications-button", "n_clicks")
)

#This function is meant for the "Server Notifications" button on the dashboard. This function ensures that the ui opens as intended.
def toggle_notification_window(open_clicks, close_clicks):
    window_style = {
        "display": "none",
        "position": "fixed",
        "top": "100px",
        "right": "30px",
        "width": "450px",
        "maxWidth": "90vw",
        "maxHeight": "75vh",
        "backgroundColor": "#ffffff",
        "border": "1px solid",
        "borderRadius": "12px",
        "padding": "20px",
        "boxShadow": "0 8px 25px rgba(0, 0, 0, 0.2)",
        "zIndex": "1000",
        "overflowY": "auto"
    }

    if ctx.triggered_id == "server-notifications-button":
        window_style["display"] = "block"
    else:
        window_style["display"] = "none"

    return window_style

@app.callback(
    Output("custom-settings", "style"),
    Output("preset-settings", "style"),
    Input("notification-mode", "value")
)

#This function checks the current notification mode, and adjusts the dropdown menus for each metric as needed.
def toggle_notification_settings(notification_mode):
    if notification_mode == "preset":
        return (
            {"display": "none"},
            {"display": "flex",
                "flex": "3",
                "gap": "15px"}
        )

    return (
        {"display": "flex",
            "flex": "3",
            "gap": "15px"},
        {"display": "none"}
    )

@app.callback(
    [
        Output("status-cards-container", "children"),
        Output("cpu-mem-graph", "figure"),
        Output("network-graph", "figure"),
        Output("disk-gauge-graph", "figure"),
        Output("notification-history", "data"),
        Output("active-notifications", "data"),
    ],

    [Input("interval-poller", "n_intervals"), Input("server-selector", "value"), Input("notification-mode", "value"),
    Input("cpu-severity", "value"), Input("mem-severity", "value"), Input("disk-severity", "value"),
    ],

    [
        State("cpu-threshold", "value"),
        State("mem-threshold", "value"),
        State("disk-threshold", "value"),
        State("notification-history", "data"),
        State("active-notifications", "data"),
    ],
    )

def update_dashboard(n_interval, selected_server, notification_mode, cpu_severity, mem_severity, disk_severity, 
cpu_thresh, mem_thresh, disk_thresh, notification_history, active_notifications):
    if selected_server not in metrics_history:
        metrics_history[selected_server] = pd.DataFrame(
            columns=["time_label", "cpu_pct", "mem_pct", "disk_pct", "net_rx_kbps", "net_tx_kbps"]
        )
        elapsed_tracker[selected_server] = 0

    endpoint = SERVERS[selected_server]
    result = metric_collection(endpoint)
    is_online = result["online"]

    if is_online:
        data = result["metrics"]
        active_stress = data.get("active_stress", "IDLE")

    else:
        data = {
            "cpu_pct": None,
            "mem_pct": None,
            "disk_pct": None,
            "net_rx_kbps": None,
            "net_tx_kbps": None
        }

        active_stress = "UNKNOWN"

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

    notification_history = list(notification_history or [])
    active_notifications = dict(active_notifications or {})

    metrics_to_check = [
        ("CPU Usage", "cpu_pct", cpu_thresh, cpu_severity, 80),
        ("Memory Usage", "mem_pct", mem_thresh, mem_severity, 80),
        ("Disk Usage", "disk_pct", disk_thresh, cpu_severity, 85)
    ]

    for metric_name, metric_key, threshold, severity, default_threshold in metrics_to_check:
        alert_key = f"{selected_server}:{metric_name}"

        if is_online:
            metric_value = new_entry[metric_key]
            effective_threshold = (
                threshold if threshold is not None else default_threshold
            )

            #This part uses the "Notification System" to check the metric.
            result = check_notification(metric_name, metric_value, mode = notification_mode, 
            threshold = effective_threshold, minimum_severity = severity)

            #This part creates and inserts a notification if it does not already exist.
            if result["alert"]:
                if alert_key not in active_notifications:
                    notification_history.insert(0, {
                        "id": f"{time.time_ns()}-{selected_server}-{metric_name}",
                        "server": selected_server,
                        "metric": metric_name,
                        "value": metric_value,
                        "status": result["status"],
                        "threshold": effective_threshold,
                        "minimum_severity": severity,
                        "mode": notification_mode,
                        "timestamp": datetime.now().strftime("%I:%M:%S %p"),
                        "resolved": False,
                        "resolved_at": None
                    })

                    active_notifications[alert_key] = True
                
                #This part removes the alert without deleting its history.
            else:
                if alert_key in active_notifications:
                    for notification in notification_history:
                        if (
                            notification["server"] == selected_server
                            and notification["metric"] == metric_name
                            and not notification.get("resolved", False)
                        ):

                            notification["resolved"] = True
                            notification["resolved_at"] = datetime.now().strftime("%I:%M:%S %p")
                            break
                    
                    active_notifications.pop(alert_key, None)
            
        #This part resets the active marker in the case of the monitoring data becoming unavailable.
        else:
            active_notifications.pop(alert_key, None)
    
    cards = [
        create_stat_card("CPU Usage", new_entry["cpu_pct"], "%", cpu_thresh or 80, is_online, mode = notification_mode, minimum_severity = cpu_severity),
        create_stat_card("Memory Usage", new_entry["mem_pct"], "%", mem_thresh or 80, is_online, mode = notification_mode, minimum_severity = mem_severity),
        create_stat_card("Disk Usage", new_entry["disk_pct"], "%", disk_thresh or 85, is_online, mode = notification_mode, minimum_severity = disk_severity),
        html.Div(
            style={
                "flex": "1",
                "backgroundColor": "#fff",
                "padding": "12px",
                "borderRadius": "6px",
                "border": "1px solid #d8b4fe",
                "textAlign": "center"
            },
            children=[
                html.H4("Network I/O", style={"margin": "0 0 5px 0"}),
                html.H3(f"RX: {new_entry['net_rx_kbps']:.1f} KB/s" if is_online else "RX: N/A", style={"margin": "0", "color": "#0055cc"}),
                html.H3(f"TX: {new_entry['net_tx_kbps']:.1f} KB/s" if is_online else "TX: N/A", style={"margin": "0", "color": "#7a00cc"}),
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

# Plotting CPU and RAM
    cpu_mem_fig = go.Figure()
    cpu_mem_fig.add_trace(
        go.Scatter(
            x=df["time_label"], 
            y=df["cpu_pct"], 
            mode="lines+markers", 
            name="CPU %", 
            line=dict(color="#d32f2f"),
        )
    )
    cpu_mem_fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["mem_pct"],
            mode="lines+markers",
            name="RAM %",
            line=dict(color="#1976d2"),
        )
    )
    cpu_mem_fig.update_layout(
        title=f"CPU & Memory ({selected_server})",
        font=dict(family=FONT_FAMILY),
        xaxis=dict(title="Elapsed Time", type="category"),
        yaxis=dict(range=[0, 105], title="%"),
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
    )

# Plotting Network Traffic
    net_fig = go.Figure()
    net_fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["net_rx_kbps"], 
            mode="lines",
            name="RX KB/s",
            fill="tozeroy",
            line=dict(color="#388e3c"),
        )
    )
    net_fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["net_tx_kbps"],
            mode="lines", name="TX KB/s",
            fill="tozeroy",
            line=dict(color="#7b1fa2"),
        )
    )
    net_fig.update_layout(
        title=f"Network Throughput ({selected_server})",
        font=dict(family=FONT_FAMILY),
        xaxis=dict(title="Elapsed Time", type="category"),
        yaxis_title="KB/s",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
    )

#Plotting Storage Gauge: Shows a gauge detailing the current storage usage of the server. If the server is offline, the gauge is disabled.
    if is_online:
        disk_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=new_entry["disk_pct"],
                title={"text": "Disk Allocation (%)", "font": {"family": FONT_FAMILY, "size": 18}},
                number={"font": {"family": FONT_FAMILY, "size": 42}, "suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {
                        "color": "red"
                        if new_entry["disk_pct"] >= (disk_thresh or 85)
                        else "#6a1b9a"
                    },
                    "steps": [
                        {"range": [0, disk_thresh or 85], "color": "#f3e8ff"},
                        {"range": [disk_thresh or 85, 100], "color": "#ffcdd2"},
                    ],
                },
            )
        )
    
    else:
        disk_gauge = go.Figure()
        disk_gauge.add_annotation(
            text = "OFFLINE - Disk Usage Unavailable.",
            x = 0.5,
            y = 0.5,
            xref = "paper",
            yref = "paper",
            showarrow = False,
            font = {
                "size": 24,
                "color": "red",
                "family": FONT_FAMILY
            }
        )

        disk_gauge.update_xaxes(visible = False)
        disk_gauge.update_yaxes(visible = False)

    disk_gauge.update_layout(
        font=dict(family=FONT_FAMILY),
        height=360,
        margin=dict(l=30, r=30, t=40, b=20),
    )
    
    return cards, cpu_mem_fig, net_fig, disk_gauge, notification_history, active_notifications

#This function will display the current recorded notifications inside of the Server Notifications window.
@app.callback(
    Output("notification-log", "children"),
    Input("notification-history", "data")
)

def display_notification_log(notification_history):
    if not notification_history:
        return html.P(
            "No Notifications Yet.",
            style = {"color": "#777", "textAlign": "center"}
        )
    
    entries = []
    for notification in notification_history:
        is_resolved = notification.get("resolved", False)
        entries.append(
            html.Div(
                style = {
                    "backgroundColor": "#f3f3ff",
                    "border": "1px solid",
                    "borderRadius": "8px",
                    "padding": "12px",
                    "marginBottom": "10px"
                },

                children = [
                    html.Div(
                        style = {
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                        },

                        children = [
                            html.Strong(f'{notification["status"]} - {notification["metric"]}'),
                            html.Small(notification["timestamp"])
                        ]
                    ),

                    html.P(
                        f'{notification["server"]} - '
                        f'{notification["metric"]}: {notification["value"]:.1f}%',
                        style = {"marginBottom": "5px"}
                    ),

                    html.Small(
                        f'Exceeded The Configured Threshold Of {notification["threshold"]}%' if notification["mode"] == "custom"
                        else f'Triggered Configured Severity Alert'
                    ),

                    html.P(
                        f'RESOLVED AT: {notification.get('resolved_at', 'Unknown')}'
                        if is_resolved else "ACTIVE",
                        style = {
                            "color": "green" if is_resolved else "red",
                            "fontWeight": "bold",
                            "fontSize": "12px",
                            "marginBottom": "0"
                        }
                    ),

                ]
            )
        )
    
    return entries

@app.callback(
    Output("notification-toast-state", "data"),
    Output("notification-toast-container", "children"),
    Input("notification-history", "data"),
    Input("interval-poller", "n_intervals"),
    Input({"type": "dismiss-notification-toast", "index": ALL}, "n_clicks"),
    State("notification-toast-state", "data")
)

def update_notification_toasts(notification_history, n_intervals, dismiss_clicks, toast_state):
    notification_history = notification_history or []
    toast_state = toast_state or {"seen_count": 0, "popups": []}

    seen_count = toast_state.get("seen_count", 0)
    popups = list(toast_state.get("popups", []))
    triggered = ctx.triggered_id
    if(isinstance(triggered, dict) and triggered.get("type") == "dismiss-notification-toast"):
        dismissed_id = triggered["index"]

        popups = [popup for popup in popups if popup["notification"]["id"] != dismissed_id]

    current_time = time.time()
    popups = [popup for popup in popups if popup["expires_at"] > current_time]

    new_count = max(0, len(notification_history) - seen_count)
    if new_count > 0:
        new_notifications = notification_history[:new_count]

        for notification in reversed(new_notifications):
            popups.insert(0, {"notification": notification.copy(), "expires_at": current_time + 6})

    seen_count = len(notification_history)
    popup_cards = []

    for popup in popups:
        notification = popup["notification"]

        popup_cards.append(
            html.Div(
                style = {
                    "backgroundColor": "#ffffff",
                    "border": "2px solid",
                    "borderRadius": "10px",
                    "padding": "14px",
                    "boxShadow": "0 5px 18 px rgba(0, 0, 0, 0,2)",
                    "pointerEvents": "auto"
                },

                children = [
                    html.Div(
                        style = {
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "gap": "8px"
                        },

                        children = [
                            html.Strong(
                                f"⚠ {notification["status"]} - {notification["metric"]}",
                                style = {"color": "red"}
                            ),

                            html.Button(
                                "x",
                                id = {
                                    "type": "dismiss-notification-toast",
                                    "index": notification["id"]
                                },
                                n_clicks = 0,
                                style = {
                                    "border": "none",
                                    "backgroundColor": "transparent",
                                    "fontSize": "20px",
                                    "cursor": "pointer",
                                    "color": "#555"
                                }
                            )
                        ]
                    ),              

                    html.P(
                        f"{notification["server"]} - "
                        f"{notification["metric"]}: {notification["value"]:.1f}%",
                        style = {"margin": "8px"}
                    ),

                    html.Div(
                        f"Triggered At: {notification["timestamp"]}",
                        style = {
                            "fontSize": "11px",
                            "color": "#777",
                            "marginTop": "8px"
                        }
                    )
                ]
            )
        )
    
    return ({"seen_count": seen_count, "popups": popups}, popup_cards)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)