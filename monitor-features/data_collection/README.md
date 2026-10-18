The "data_collection" folder contains the data collector for the dashboard, alongside a test script called "tester_agent.py" that allows the user to test the data downloading with a mock monitoring agent.

Requirements: Python 3, Requests library, Math module

The methods used to pull the data from each monitoring agent is a Python script that requests performance metrics from a Linux monitoring agent. The main script, "data_collector.py", pulls five metrics: CPU usage, Memory usage, Disk usage, incoming network traffic, and outgoing network traffic. After receiving the data from the monitoring data, the data is vetted through several checks to ensure that the data provided is valid and can be displayed.

Testing: "data_collector.py" was tested using a script "tester_agent.py", which creates a mock monitoring agent with several parameters meant to simulate a monitoring agent's metrics using a local /metrics endpoint. The data collector successfully pulled the data when all fields came as intended, and rejected any fields that violated any of the checks.

Current Limitations (v1): The current data collector uses a two-second request timeout and needs a monitoring agent that returns the expected metric names.

Commands:
To Install Requests: -m pip install requests
To Start The Test Agent (Optional, meant for testing): monitor-features/data-collection/tester_agent.py
To Run The Data Collector: python monitor-features/data-collection/data-collector.py