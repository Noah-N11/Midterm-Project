# Midterm-Project
Repository for Systems in Unix Midterm Project

How to set up your VM to work with the dashboard:
1. Launch your Google Cloud VM using SSH. Run the following commands in order:
- git clone -b monitor-features https://github.com/Noah-N11/Midterm-Project.git
- cd Midterm-Project
- sudo bash setup-vm.sh

That's it! Make sure that when connecting a new VM to your dashboard, the VM's IP is static, and is included in dashboard.py's "SERVERS" dictionary.

Important Bash commands to remember:
1. Stress Test
- To start our stress test: sudo systemctl start stress-loop.service
- To stop our stress test: sudo systemctl stop stress-loop.service
- To see the status of our stress test: sudo systemctl status stress-loop.service
- To restart our stress test: sudo systemctl restart stress-loop.service
- To enable our stress test on VM startup (NOT RECOMMENDED): sudo systemctl enable stress-loop.service
- To disable our stress test on VM startup: sudo systemctl disable stress-loop.service

2. Monitoring API
- To start our API: sudo systemctl start unix-monitor-api.service
- To stop our API: sudo systemctl stop unix-monitor-api.service
- To restart our API: sudo systemctl restart unix-monitor-api.service

# Presentation Portion
1. Show a stress event and provide the code (the three stress files)
2. Show how systemd auto restarts via config ()
3. Dedicated user and group (id monitor-api, systemctl cat unix-monitor-api.service)
4. Named pipes (ls -l /run/unix-monitor/stress-events.fifo, cat /run/unix-monitor/current-stress.txt; pipes send event names though pipe, reader receives, and API reports the current event to our dashboard)
5. Cron job used for failiure recovery (cat /etc/cron.d/unix-monitor-health; every 5 minutes, checks if API is missing, then restarts it)
--
1. Commented code
2. Metrics per server (on dashboard)
3. Graphs (real-time and historical)
4. Adjustable thresholds and alerts
5. Multiple servers
6. Github repo
7. firewall