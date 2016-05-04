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
import script_vm
import script_compiler
import script_cpu
import driver.manager

logger = logging.getLogger("dmx")

class DMXEngineScript():
    def __init__(self, terminate_signal, vm):
        """
        Construct instance
        :param terminate_signal: injects a threading event that can be tested for termination
        :param vm: injects a script VM into the engine
        :return:
        """
        self._dev = None
        self._vm = vm
        self._terminate_signal = terminate_signal
        pass

    def initialize(self):
        """
        Initialize the script engine to begin execution
        :return: Returns True if engine is initialized.
        Returns False if something fails.
        """

        # Open DMX interface driver
        self._dev = driver.manager.get_driver()
        if self._dev.open():
            logger.info("DMX interface driver opened")
        else:
            logger.error("DMX interface driver failed to open")
            return False

        return True

    def execute(self):
        """
        Runs one step period
        :return:
        """

        cpu = script_cpu.ScriptCPU(self._dev, self._vm, self._terminate_signal)
        rc = cpu.run()

        self.shutdown()
        return rc

    def shutdown(self):
        """
        Shutdown the script engine
        :return:
        """
        if self._dev:
            self._dev.close()
