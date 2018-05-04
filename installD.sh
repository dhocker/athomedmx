#!/bin/bash

### Install athomedmxD.sh as a daemon

# Installation steps
sudo cp athomedmxD.sh /etc/init.d/athomedmxD.sh
sudo chmod +x /etc/init.d/athomedmxD.sh
sudo update-rc.d athomedmxD.sh defaults

# Start the daemon: 
sudo service athomedmxD.sh start

exit 0

