The "notifications" folder contains the notification system and the performance threshold methods for this project.

Requirements: Python 3

The notification system method for this project is a Python script that checks a monitoring agent's performance and compares it to user-given thresholds or default thresholds, with both modes being toggleable by the user. If these thresholds are reached or exceeded, the script determines that the user should be sent a notification, alarming them that the usage of a certain metric is in critical territory. The notification features several checks that ensure that the processed numbers are valid.

The main mode, known as the "Custom" mode, takes a user given percent for a metric and returns a "CRITICAL" status when that metric reaches or exceeds the percentage.

An extra mode I opted to add, known as the "Preset" mode, has four different thresholds: "LOW" (0-20%), "NORMAL" (20.1-60%), "HIGH" (60.1-80%), and "CRITICAL"(80.1% +). The user can pick what threshold they want to be notified about ("LOW" was excluded as that is the minimum status), and if that threshold is reached or exceeded, the script will tell the dashboard to notify them that the threshold is exceeded. For example, if the user switches to the "Preset" mode and they want to be notified when the CPU usage exceeds the "HIGH" threshold, if the CPU usage reaches 90%, it will alert the user, stating that the CPU usage has passed the "HIGH" threshold and reached "CRITICAL" status.

Testing: The methods used to test the notification system were several Python-executed test cases. These test cases verified that the "Custom" mode correctly read the user inputted threshold, and returned a "CRITICAL" status when the threshold was exceeded. Other test cases for the "Preset" mode made sure that all values were correctly assigned their threshold depending on their usage. Several other test cases that violated the checks in the notification system were tested, and they were all rejected as intended.

Current Limitations (v1): The developed script is meant to determine when an alert should appear, but it does not make a notification appear on its own.

Commands:
To Test The Notification System: python monitor-features/notifications/alert_system.py