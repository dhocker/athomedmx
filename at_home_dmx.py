#!/usr/bin/python

#
# AtHomeDMX - DMX script engine
# Copyright (C) 2016  Dave Hocker (email: AtHomeX10@gmail.com)
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

import configuration
import app_logger
import engine.dmx_engine
import disclaimer.disclaimer
import logging
import signal
import os
import time
import sys


#
# main
#
def main():
    logger = logging.getLogger("dmx")

    # Clean up when killed
    def term_handler(signum, frame):
        logger.info("AtHomeDMX received kill signal...shutting down")
        # This will break the forever loop at the foot of main()
        terminate_service = True
        sys.exit(0)

    # Orderly clean up of the DMX engine
    def CleanUp():
        dmx_engine.Stop()
        logger.info("AtHomeDMX shutdown complete")
        logger.info("################################################################################")
        app_logger.Shutdown()

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
    # TODO If we decide to support drivers, we probably need the configuration to
    # specify the type of interface (e.g. uDMX) and its unique identification)
    # For now, this app supports the first uDMX it finds.
    #logger.info("X10 controller: %s", Configuration.Configuration.X10ControllerDevice())
    #logger.info("ComPort: %s", Configuration.Configuration.ComPort())

    # Inject the controller driver
    # TODO If we decide to support drivers for DMX interfaces
    #driver = Configuration.Configuration.GetX10ControllerDriver()
    #drivers.X10ControllerAdapter.X10ControllerAdapter.Open(driver)

    # TODO turn this into the script engine thread
    # Fire up the DMX script engine
    dmx_engine = engine.dmx_engine.DMXEngine()

    # Set up handler for the kill signal
    signal.signal(signal.SIGTERM, term_handler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C or kill the daemon.

    # Launch the engive server
    try:
        # This runs "forever", until ctrl-c or killed
        dmx_engine.Start()
        logger.info("Engine thread started")
        terminate_service = False
        while (not terminate_service) and dmx_engine.Running():
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
        CleanUp()


#
# Run as an application or daemon
#
if __name__ == "__main__":
    main()
