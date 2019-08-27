#!/bin/sh

### BEGIN INIT INFO
# Provides:          athomedmxD.sh
# Required-Start:    $all
# Required-Stop:     $remote_fs $syslog
# Should-Start:
# Should-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Manages AtHomeDMX as a daemon
# Description:       Adapted from the article: http://blog.scphillips.com/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
### END INIT INFO

# Installation
# Copy this script to /etc/init.d/: sudo cp athomedmxD.sh /etc/init.d/athomedmxD.sh
# Make sure to set its permissions for execution: chmod +x /etc/init.d/athomedmxD.sh
# Register the script: sudo update-rc.d athomedmxD.sh defaults
# Start the daemon: sudo service athomedmxD.sh start

# Setup the path to lead with the virtualenv. When it's python is executed it
# will activate the virtualenv.
VENV=/home/pi/Virtualenvs/athomedmx3
PATH=$VENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Change the next 4 lines to suit where you install your script and what you want to call it
DIR=/home/pi/rpi/athomedmx
DAEMON_SCRIPT=$DIR/at_home_dmx.py
DAEMON_NAME=athomedmxD.sh
PYTHON_INT=$VENV/bin/python

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
# In this case we are using a USB based DMX controller which does not require root access
# because we have set the permissions of the device.
# See https://github.com/dhocker/udmx-pyusb.
DAEMON_USER=pi

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER \
        --chuid $DAEMON_USER --startas $PYTHON_INT -- $DAEMON_SCRIPT
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --retry 30 --signal 15
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;
    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0

