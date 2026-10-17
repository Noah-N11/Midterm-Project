#The function is a check that verifies that a valid percentage between 0 and 100 is being entered.
def validate_percent(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Percent must be a number.")

    if not 0 <= value <= 100:
        raise ValueError("Percent must be between 0 and 100.")

    return value

#This function checks the user set threshold for a given metric. If the current value reaches or exceeds the threshold, the user will be alerted. (Main Project Part)
def check_threshold(metric_name, current_value, threshold):
    current_value = validate_percent(current_value)
    threshold = validate_percent(threshold)

    if current_value >= threshold:
        return {
            "metric": metric_name,
            "value": current_value,
            "threshold": threshold,
            "status": "CRITICAL",
            "alert": True
        }

    return {
        "metric": metric_name,
        "value": current_value,
        "threshold": threshold,
        "status": "NORMAL",
        "alert": False
    }

#This next function is a feature I thought would add an extra layer of depth to the notification system, that being a toggleable mode to change from a user inputted
#threshold to some default thresholds. 0-20% = LOW, 20.1-60% = NORMAL, 60.1-80% = HIGH, 80.1% + = CRITICAL.
def check_usage_level(current_value):
    current_value = validate_percent(current_value)

    if current_value <= 20:
        return "LOW"
    elif current_value <= 60:
        return "NORMAL"
    elif current_value <= 80:
        return "HIGH"
    else:
        return "CRITICAL"

#This function allows the user to toggle the threshold that needs to be reached for the system to notify them. For example, if the user picks the "HIGH" threshold, it
#will notify the user when the component reaches "HIGH" usage, or any usage point above "HIGH" (just "CRITICAL" in this case).
def check_severity_alert(current_value, minimum_severity="HIGH"):
    severity = check_usage_level(current_value)
    severity_order = ["LOW", "NORMAL", "HIGH", "CRITICAL"]

    if minimum_severity not in ("NORMAL", "HIGH", "CRITICAL"):
        raise ValueError("Invalid minimum notification severity.")

    alert = severity_order.index(severity) >= severity_order.index(minimum_severity)
    return {
        "value": current_value,
        "status": severity,
        "minimum_severity": minimum_severity,
        "alert": alert
    }

#This function checks for the current mode (custom or preset), then checks if a given metric is exceeding the user provided threshold for custom, or the base thresholds
#for preset.
def check_notification(metric_name, current_value, mode = "custom", threshold = 80, minimum_severity = "HIGH"):
    if current_value is None:
        return {
            "metric": metric_name,
            "value": None,
            "status": "OFFLINE",
            "alert": False
        }

    if mode == "custom":
        return check_threshold(metric_name, current_value, threshold)

    elif mode == "preset":
        result = check_severity_alert(current_value, minimum_severity)
        result["metric"] = metric_name
        return result
        
    else:
        raise ValueError("Current notification mode is invalid.")

#Test Code
if __name__ == "__main__":
    print(check_threshold("CPU", 85, 80))
    print(check_threshold("Memory", 75, 70))

    print(check_usage_level(15))
    print(check_usage_level(50))
    print(check_usage_level(75))
    print(check_usage_level(95))

    print(check_severity_alert(75, "HIGH"))
    print(check_severity_alert(95, "HIGH"))
    print(check_severity_alert(50, "HIGH"))
    print(check_severity_alert(95, "CRITICAL"))
    print(check_severity_alert(75, "CRITICAL"))

    print(check_notification("CPU", 85, mode="custom", threshold=80))
    print(check_notification("CPU", 75, mode="preset", minimum_severity="HIGH"))
    print(check_notification("CPU", 90, mode="custom", threshold=80))
    print(check_notification("CPU", None, mode="custom"))
    print(check_notification("Memory", None, mode="preset"))
