import requests
import math

#These are the metrics that the dashboard expects to receive from each Linux monitoring agent.
REQUIRED_METRICS = (
    "cpu_pct",
    "mem_pct",
    "disk_pct",
    "net_rx_kbps",
    "net_tx_kbps"
)

#This function retrieves the metrics from a given monitoring agent. The function either returns the metrics if the data is valid, or provides a specific error if the
#data does not pass a check.
def metric_collection(endpoint):
    try:
        response = requests.get(endpoint, timeout = 2)
        response.raise_for_status()
        metrics = response.json()

        #This check verifies that the metric lits is a dictionary. If the response isn't a dictionary, provides an error.
        if not isinstance(metrics, dict):
            raise ValueError("Invalid metrics responce, expected a dictionary.")
        
        #If a metric is missing, return an error, stating the missing metric.
        for metric in REQUIRED_METRICS:
            if metric not in metrics:
                raise ValueError(f"Missing a required metric: {metric}")

            value = metrics[metric]

            #This check verifies that the fields being retrieved by the VMs is an actual number. If the returned value is not a number, return an error.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Invalid value for: {metric}, must be a number.")

            #This check verifies that the received value is a finite number. If it is not a finite number, return an error.
            if not math.isfinite(value):
                raise ValueError(f"Invalid value for: {metric}, value must be finite.")
            
            #This check verifies that the CPU percent, Memory percent, and Disk percent values are all between (or equal to) 0 to 100. If the value is below 0 or greater than 100, return an error.
            if metric in ("cpu_pct", "mem_pct", "disk_pct"):
                if not 0 <= value <= 100:
                    raise ValueError(f"Invalid percentage for {metric}: percent value must be between 0 and 100.")
            
            #This check verifies that the network I/O values are above 0. If they are below 0, return an error.
            if metric in ("net_rx_kbps", "net_tx_kbps"):
                if value < 0:
                    raise ValueError(f"Invalid network value for {metric}: value cannot be negative.")
            
        #If all checks pass, returns the metrics.
        return {
            "online": True,
            "metrics": metrics
        }

    #Otherwise, return the table as offline, specifying the error.
    except (requests.exceptions.RequestException, ValueError) as error:
        return {
            "online": False,
            "metrics": None,
            "error": str(error)
        }