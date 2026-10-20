import json
import psutil
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

STRESS_STATUS_PATH = Path("/run/unix-monitor/current-stress.txt")

def get_active_stress():
    try:
        return STRESS_STATUS_PATH.read_text().strip() or "UNKNOWN"
    except (OSError, UnicodeError):
        return "UNKNOWN"

class MonitoringHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404, "Endpoint not found")
            return
        
        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            mem_pct = psutil.virtual_memory().percent
            disk_pct = psutil.disk_usage("/").percent

            network = psutil.net_io_counters()
            rx_before = network.bytes_recv
            tx_before = network.bytes_sent

            time.sleep(1)

            network_after = psutil.net_io_counters()
            net_rx_kbps = max(0, (network_after.bytes_recv - rx_before) / 1024)
            net_tx_kbps = max(0, (network_after.bytes_sent - tx_before) / 1024)

            metrics = {
                "cpu_pct": cpu_pct,
                "mem_pct": mem_pct,
                "disk_pct": disk_pct,
                "net_rx_kbps": round(net_rx_kbps, 2),
                "net_tx_kbps": round(net_tx_kbps, 2),
                "active_stress": get_active_stress()
            }

            response = json.dumps(metrics).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        except Exception as error:
            print(f"Metric Collection Has Failed: {error}")
            self.send_error(500, "Unable to collect system metrics.")

if __name__ == "__main__":
    # Localhost-only for initial testing.
    server = HTTPServer(("0.0.0.0", 8000), MonitoringHandler)

    print("Monitoring API running on http://0.0.0.0:8000/metrics")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Monitoring API stopped.")
    finally:
        server.server_close()