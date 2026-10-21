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
- To restart our stress test: sudo systemctl restart stress-loop.service
- To enable our stress test on VM startup (NOT RECOMMENDED): sudo systemctl enable stress-loop.service
- To disable our stress test on VM startup (NOT RECOMMENDED): sudo systemctl disable stress-loop.service

2. Monitoring API
- To start our API: sudo systemctl start unix-monitor-api.service
- To stop our API: sudo systemctl stop unix-monitor-api.service
- To restart our API: sudo systemctl restart unix-monitor-api.service
