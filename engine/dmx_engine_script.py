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
    def __init__(self, terminate_signal):
        """
        Construct instance
        :param terminate_signal: injects a threading event that can be tested for termination
        :return:
        """
        self._script = None
        self._dev = None
        self._vm = None
        self._terminate_signal = terminate_signal
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

        # Create a VM instance
        self._vm = script_vm.ScriptVM()

        # Compile the script (pass 1)
        compiler = script_compiler.ScriptCompiler(self._vm)
        rc = compiler.compile(self._script)
        if rc:
            logger.info("Successfully compiled script %s", self._script)

        return rc

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
