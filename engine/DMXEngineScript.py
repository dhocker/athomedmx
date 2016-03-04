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
import Configuration
import pyuDMX.pyuDMX

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
        # Read config for script

        # Open uDMX
        # TODO We really want a driver adapter here with selectable driver behind it
        self._dev = pyuDMX.pyuDMX.uDMXDevice()
        if self._dev.open():
            logger.info("uDMX interface opened")
        else:
            logger.error("uDMX interface failed to open")
            return False
        return True

    def run_step_period(self):
        """
        Runs one step period
        :return:
        """
        return True