#
# AtHomeDMX - DMX script engine
# Copyright (C) 2016  Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

#
#
# DMX script engine execution
#

import logging
import configuration
import driver.manager

logger = logging.getLogger("dmx")

class DMXEngineScript():
    def __init__(self):
        self._script = None
        self._dev = None
        pass

    def initialize(self):
        """
        Initialize the script engine to begin execution
        :return: Returns True if engine is initialized.
        Returns False if something fails.
        """
        # Read config for script to execute
        self._script = configuration.Configuration.Scriptfile()

        # Open DMX interface driver
        self._dev = driver.manager.get_driver()
        if self._dev.open():
            logger.info("DMX interface driver opened")
        else:
            logger.error("DMX interface driver failed to open")
            return False
        return True

    def run_step_period(self):
        """
        Runs one step period
        :return:
        """
        return True

    def shutdown(self):
        """
        Shutdown the script engine
        :return:
        """
        if self._dev:
            self._dev.close()
