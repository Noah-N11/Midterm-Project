#!/bin/bash
ps -ef | grep "python3 maintain.py" | grep -v grep
if [ $? -ne 0 ]; then
    python3 maintain.py
else
    echo "API is Currently Running"
fi