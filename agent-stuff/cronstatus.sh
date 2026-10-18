#!/bin/bash
ps -ef | grep "python3 agent.py" | grep -v grep
if [ $? -ne 0 ]; then
    echo "Restarted Agent"
    python3 agent.py
else
    echo "Agent is Currently Running"
fi