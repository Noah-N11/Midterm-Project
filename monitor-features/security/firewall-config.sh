#! /bin/bash

set -euo pipefail

#This first portion defines the SSH port, API port, and allowed IP for the firewall.
SSH_PORT=22
API_PORT=5000
ALLOWED_IP="${1:-}"

#The first check of the firewall is to check whether the program is being ran by an administrator (using sudo). If the user does not have administrator privledges, the
#check will fail.
if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run using administrator permissions."
    exit 1
fi

#Then, we check if the IP string has been provided, meaning that there are values in the string and it is not empty. In the case of the string being empty,
#this check will fail and give the user the specific reason so that the problem can be addressed.
if [[ -z "$ALLOWED_IP" ]]; then
    echo "Error: No IP address has been configured."
    exit 1
fi

#Then, we check if the provided IP is in the IPv4 format. If the IP is not in the IPv4 format, the check will fail.
if [[ ! "$ALLOWED_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    echo "Error: The provided IP is not in the IPv4 address format."
    exit 1
fi

#This code splits the IP address into four octets so that it can be checked by the next for-loop.
IFS='.' read -r -a OCTETS <<< "$ALLOWED_IP"

#Then, this for-loop verifies two different conditions that validate each octet of the IPv4 address. The first check verifies that the octets pulled from the last part
#are not larger than 255. The second check checks for any leading zeros in the IP.
for OCTET in "${OCTETS[@]}"; do
    if (( 10#$OCTET > 255)); then
        echo "Error: IPv4 octet exceeds 255."
        exit 1
    fi

    if [[ ${#OCTET} -gt 1 && $OCTET == 0* ]]; then
        echo "Error: IPv4 octets cannot contain any leading zeroes."
        exit 1
    fi
done

#The last check on run is to see whether UFW has been installed. If it has not been installed, the check will fail and provide the user with the instructions on how to
#download UFW.
if ! command -v ufw >/dev/null 2>&1; then
    echo "Error: UFW is not installed. UFW can be installed using the following code: sudo apt install ufw"
    exit 1
fi

#This portion gathers the listening TCP ports, existing UFW rules, and the UFW activation status which will be used for the next checks.
SSH_LISTENERS=$(ss -tln)
EXISTING_RULES=$(ufw show added)
UFW_STATUS=$(ufw status)

#This check sees if this UFW configuration is already active. If it is active, warns the user and stops the script.
if grep -q "^Status: active" <<< "$UFW_STATUS"; then
    echo "Error: UFW is already running. Please review the active firewall configuration before proceeding."
    exit 1
fi

#This check sees if there are already configured rules with the UFW. If there are already configured rules, warns the user and stops the script.
if [[ "$EXISTING_RULES" != *"(None)"* ]]; then
    echo "WARNING: There are already pre-existing UFW rules. Please review the current rules before proceeding:"
    echo "$EXISTING_RULES"
    exit 1
fi

#This check verifies that the SSH port is listening on the configured port. This check ensures that we do not lock ourselves out of the VM.
if ! grep -qE "[:.]${SSH_PORT}[[:space:]]" <<< "$SSH_LISTENERS"; then
    echo "Error: The SSH does not appear to be listening on the port $SSH_PORT."
    exit 1
fi

#This part of the code confirms that the SSH port is verified. 
echo "SSH port $SSH_PORT verified."
echo "Preparing Firewall Config..."
echo "Monitoring API Port: $API_PORT"
echo "Authorized IP: $ALLOWED_IP"

#Then, this will display the UFW configuration before making changes.
echo "Current UFW configuration:"
ufw status verbose

#Then, a prompt is sent to the user to see if they want the firewall commands to be executed. An if-statement is used to check the user's input.
read -r -p "Apply these firewall rules? (yes/no): " CONFIRM
CONFIRM=${CONFIRM,,}

if [[ "$CONFIRM" != "yes" ]]; then
    echo "Firewall configuration cancelled."
    exit 0
fi

#After the user accepts the firewall, we can configure the firewall to allow SSH connections and restrict the monitoring API access the the authorized IPv4 address. 
#By default, any other incoming connections are denied.
ufw allow "${SSH_PORT}/tcp"
ufw allow from "${ALLOWED_IP}" to any port "${API_PORT}" proto tcp
ufw default deny incoming

#Finally, after everything runs successfully, several print statements will be ran to tell the user that everything started as intended.
echo "Firewall rules have been added to the UFW configuration."
echo "WARNING: While the firewall has been successfully configured, UFW is not automatically enabled."
echo "Make sure to review the rules and verify SSH access before activating UFW."