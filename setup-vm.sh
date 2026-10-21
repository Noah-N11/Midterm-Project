#!/bin/bash
set -euo pipefail

#This script is meant to setup any Debian/Ubuntu systems that use systemd and apt for the dashboard.
SERVICE_NAME="unix-monitor-api"
SERVICE_USER="monitor-api"
SERVICE_GROUP="monitor-api"

#This code is meant to find the repository directory.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_API="$PROJECT_DIR/monitor-features/data_collection/monitoring_api.py"

#This part of the code is meant to ensure that the API is installed into a consistent system location.
INSTALL_DIR="/opt/unix-monitor"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

#This code is meant to setup the stress-loop at the end of the setup script.
STRESS_SCRIPT="$PROJECT_DIR/stress-loop.sh"
STRESS_SOURCE_SERVICE="$PROJECT_DIR/stress-loop.service"
STRESS_INSTALL_DIR="/opt/server-monitor"
STRESS_SERVICE_FILE="/etc/systemd/system/stress-loop.service"

#This code sets up the reader for the stress test.
READER_SCRIPT="$PROJECT_DIR/monitor-features/data_collection/stress_event_reader.py"
READER_SOURCE_SERVICE="$PROJECT_DIR/stress-event-reader.service"
READER_SERVICE_FILE="/etc/systemd/system/stress-event-reader.service"

#This code is meant to setup the cron job, which will be used for monitoring API failure recovery.
CRON_SCRIPT="$PROJECT_DIR/cronstatus.sh"
CRON_INSTALL_PATH="$INSTALL_DIR/cronstatus.sh"
CRON_FILE="/etc/cron.d/unix-monitor-health"

echo "Starting The Linux Monitoring API Installation..."

#This part of the setup code is meant to verify that this code is being ran with "sudo".
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be ran using sudo."
    exit 1
fi

#This part of the setup code is meant to check that the monitoring API exists.
if [ ! -f "$SOURCE_API" ]; then
    echo "ERROR: monitoring_api.py was not found."
    exit 1
fi

#This part of the code installs all required packages automatically.
echo "Installing Dependencies..."
apt-get update
apt-get install -y python3 python3-psutil curl

#This part of the setup code is meant to create a dedicated system user and group.
if ! getent group "$SERVICE_GROUP" >/dev/null; then
    groupadd --system "$SERVICE_GROUP"
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    useradd \
    --system \
    --gid "$SERVICE_GROUP" \
    --home-dir "$INSTALL_DIR" \
    --shell /usr/sbin/nologin \
    "$SERVICE_USER"
fi

#This part of the setup code is meant to install the monitoring_api.py file from the github repository.
echo "Installing The Monitoring API..."
install -d -o root -g root -m 755 "$INSTALL_DIR"
install -o root -g root -m 644 "$SOURCE_API" "$INSTALL_DIR/monitoring_api.py"

#This part of the setup code is the setup and creation portion for the systemd service.
echo "Creating The Systemd Service..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Linux Infrastructure Monitoring API
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/monitoring_api.py
Restart=always
RestartSec=5
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

#This part of the setup code is meant to enable and start up the newly installed monitoring service.
echo "Starting Monitoring Service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

#Wait a brief moment for the API to start.
sleep 3

#This part of the setup code is meant to verify that the API is active, stopping the script if for whatever reason the service is unable to start.
echo "Checking Service Status..."
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "ERROR: The monitoring service was unable to start."
    systemctl status "$SERVICE_NAME" --no-pager || true
    exit 1
fi

#This part of the setup code is meant to verify that the API is actually returning valid metrics.
echo "Testing Local Monitoring Endpoint..."
if ! curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/metrics; then
    echo "ERROR: Monitoring endpoint is not responding."
    exit 1
fi
#Finally, once the setup is successful, several echoes are returned, providing the service, service user, and endpoint.
echo "Monitoring API Installation Successful!"
echo "Service: $SERVICE_NAME"
echo "Service User: $SERVICE_USER"
echo "Local Endpoint: http://127.0.0.1:8000/metrics"


#Before starting the stress-loop installation, the setup code verifies that the source files exist.
if [ ! -f "$STRESS_SCRIPT" ] || [ ! -f "$STRESS_SOURCE_SERVICE" ]; then
    echo "ERROR: Stress-loop files were not found."
    exit 1
fi

#The second portion of the setup file is meant to setup the stress test.
apt-get install -y stress-ng systemd

#First, we must set up the installation directory.
install -d -o root -g root -m 755 "$STRESS_INSTALL_DIR"

#Then, we must copy the stress script and ensure that it can be executed.
install -o root -g root -m 755 \
    "$STRESS_SCRIPT" \
    "$STRESS_INSTALL_DIR/stress-loop.sh"

#Then, we must copy the systemd service definition.
install -o root -g root -m 644 \
    "$STRESS_SOURCE_SERVICE" \
    "$STRESS_SERVICE_FILE"

systemctl daemon-reload

#Finally, the stress-loop installation ends, providing the user with the method to use the stress loop.
echo "The Stress-Loop Files Have Been Successfully Installed."
echo "However, The Stress-Loop Must Be Manually Enabled Using: systemctl enable --now stress-loop.service"

#The third portion of the setup script installs the named-pipe reader.
echo "Installing Stress Event Reader..."
if [ ! -f "$READER_SCRIPT" ] || [ ! -f "$READER_SOURCE_SERVICE" ]; then
    echo "ERROR: Stress event reader files were not found."
    exit 1
fi

#This part of the setup copies the reader into the monitoring application's installation directory.
install -o root -g root -m 644 \
    "$READER_SCRIPT" \
    "$INSTALL_DIR/stress_event_reader.py"

#This part of the setup installs the service's systemd definition.
install -o root -g root -m 644 \
    "$READER_SOURCE_SERVICE" \
    "$READER_SERVICE_FILE"

#This part of the setup reloads the system, then starts up the reader.
systemctl daemon-reload
systemctl enable stress-event-reader.service
systemctl restart stress-event-reader.service
echo "Stress Event Reader Has Been Installed And Started."
sleep 1

#The fourth part of the setup file is meant to install the cron job health check, which occurs once every 5 minutes.
echo "Installing API Health Check..."

#To start, we must verify that our cronstatus script exists.
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "ERROR: cronstatus.sh was not found."
    exit 1
fi

#This part of the setup installs cron and copies the health check script.
apt-get install -y cron
install -o root -g root -m 755 \
    "$CRON_SCRIPT" \
    "$CRON_INSTALL_PATH"

#Then, we must schedule the script to run every 5 minutes as root.
printf '*/5 * * * * root %s >> /var/log/unix-monitor-health.log 2>&1\n' \
    "$CRON_INSTALL_PATH" > "$CRON_FILE"

chmod 644 "$CRON_FILE"

#Lastly, we will start the cron automatically.
systemctl enable --now cron.service

#When all steps of this part complete, the script will echo the frequency of the cron job, as well as a confirmation that everything set up as intended.
echo "API Health Check Installed Successfully!"
echo "Current Schedule: Run Every 5 Minutes"

#At the end of the setup, the user is told that the VM setup script completed successfully, and their VM should be ready to work with the dashboard.
echo "VM Setup Has Been Completed!"