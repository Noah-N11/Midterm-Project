#!/bin/bash
ps -ef | grep "[m]onitoring_api.py" > /dev/null

if [ $? -ne 0 ]; then
    echo "The Monitoring API Is Not Running. Restarting..."
    systemctl restart unix-monitor-api.service
else
    echo "API is Currently Running"
fi