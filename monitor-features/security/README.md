The "security" folder contains the firewall methods for the Linux Infrastructure Observability Dashboard Project.

Requirements: Debian/Ubuntu, Bash, UFW, and root privileges.

The protection method used for the security of this project is a firewall that restricts API traffic access to one authorized IPv4 address. Alongside this, a Google Cloud VPC firewall rule was included to restrict external API monitoring access, targetting VMs with the network tag "unix-monitor". It is important to note that this script does not automatically activate the firewall, but it does fully configure the firewall. The firewall can be activated with "sudo ufw enable". 

Testing: The methods I used to test the firewall was a test website created using python's built in HTTP server. The website would have the text "Monitoring API Firewall Test" if the user was successfully able to access it. On the computer used to develop this script, the website properly loaded, but on my phone that was attempted to access the website with cellular data, the website was unable to load.

Current Limitations (v1): The current script assumes the the SSH port is 22 and the API port is 5000, and will require manual review in order to be connected with other VMs.

Commands: 
To Configure The Firewall: sudo bash firewall-config.sh YOUR_AUTHORIZED_IP_HERE
To Activate The Firewall: sudo ufw enable