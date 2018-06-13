#!/usr/bin/python
# coding: utf-8

#
# AtHomeDMX - DMX script engine
# Copyright © 2016, 2018  Dave Hocker (email: AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the LICENSE file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE file).  If not, see <http://www.gnu.org/licenses/>.
#

import athomesocketserver.SocketServerThread as SocketServerThread
import configuration
import app_logger
import engine.dmx_engine
import engine.dmx_client
import disclaimer.disclaimer
import logging
import signal
import os
import time
import sys
import json


#
# main
#
def main():
    global terminate_service

    logger = logging.getLogger("dmx")

    terminate_service = False

    # Clean up when killed
    def term_handler(signum, frame):
        global terminate_service
        logger.info("AtHomeDMX received kill signal...shutting down")
        # This will break the forever loop at the foot of main()
        terminate_service = True
        sys.exit(0)

    # Orderly clean up of the DMX engine
    def CleanUp():
        engine.dmx_client.DMXClient.stop_engine()
        logger.info("AtHomeDMX shutdown complete")
        logger.info("################################################################################")
        app_logger.Shutdown()

    def autorun_script():
        """
        Conditionally run a DMX script at start up.
        :return:
        """
        script = configuration.Configuration.AutoRun()
        if script:
            dc = engine.dmx_client.DMXClient()
            response = dc.execute_command("", "start {0}".format(script))
            r = json.loads(str(response))
            success = r["result"] == "OK"
            if success:
                logger.info("AutoRun script {0} started".format(script))
            else:
                logger.error("AutoRun script failed to start script: {0}".format(script))
                logger.error(r["messages"][0])
            return success
        return True

    # Change the current directory so we can find the configuration file.
    # For Linux we should probably put the configuration file in the /etc directory.
    just_the_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(just_the_path)

    # Load the configuration file
    configuration.Configuration.LoadConfiguration()

    # Per GPL, show the disclaimer
    disclaimer.disclaimer.DisplayDisclaimer()
    print("Use ctrl-c to shutdown engine\n")

    # Activate logging to console or file
    # Logging.EnableLogging()
    app_logger.EnableEngineLogging()

    logger.info("################################################################################")

    # For additional coverage, log the disclaimer
    disclaimer.disclaimer.LogDisclaimer()

    logger.info("Starting up...")

    logger.info("Using configuration file: %s", configuration.Configuration.GetConfigurationFilePath())

    # Set up handler for the kill signal
    signal.signal(signal.SIGTERM, term_handler)  # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C or kill the daemon.

    # This accepts connections from any network interface. It was the only
    # way to get it to work in the RPi from remote machines.
    HOST, PORT = "0.0.0.0", configuration.Configuration.Port()

    # Create the TCP socket server on its own thread.
    # This is done so that we can handle the kill signal which
    # arrives on the main thread. If we didn't put the TCP server
    # on its own thread we would not be able to shut it down in
    # an orderly fashion.
    server = SocketServerThread.SocketServerThread(HOST, PORT, engine.dmx_client.DMXClient,
                                                   connection_time_out=configuration.Configuration.Timeout())

    # Launch the socket server
    try:
        # This runs "forever", until ctrl-c or killed
        server.Start()

        # Run AutoRun script
        autorun_script()

        terminate_service = False
        while not terminate_service:
            # We do a lot of sleeping to avoid using too much CPU :-)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("AtHomeDMX shutting down...")
    except Exception as e:
        logger.error("Unhandled exception occurred")
        logger.error(e.strerror)
        logger.error(sys.exc_info()[0])
    finally:
        # We actually get here through ctrl-c or process kill (SIGTERM)
        # TODO This needs to move to the clean up function
        server.Stop()
        CleanUp()


#
# Run as an application or daemon
#
if __name__ == "__main__":
    version = sys.version_info
    print("Running Python {0}.{1}.{2}".format(version[0], version[1], version[2]))
    main()
