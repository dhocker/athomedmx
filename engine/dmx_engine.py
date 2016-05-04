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
# Engine class encapsulating script engine thread
#

import dmx_engine_thread
import script_vm
import script_compiler
import logging

logger = logging.getLogger("dmx")


# This class should be used as a singleton
class DMXEngine:
    def __init__(self):
        self.engine_thread = None
        self._vm = None
        self._compiler = None
        self._last_error = None

    @property
    def last_error(self):
        """
        Returns the last logged error message
        :return:
        """
        return self._last_error

    def compile(self, script_file):
        # Create a VM instance
        self._vm = script_vm.ScriptVM(script_file)

        # Compile the script (pass 1) of the current (main) thread
        self._compiler = script_compiler.ScriptCompiler(self._vm)
        rc = self._compiler.compile(script_file)
        if not rc:
            self._last_error = self._compiler.last_error
            return rc

        logger.info("Successfully compiled script %s", script_file)
        return rc

    def execute(self):
        # Execute the compiled script on a separate thread
        self.engine_thread = dmx_engine_thread.DMXEngineThread(1, "DMXEngineThread", self._vm)
        self.engine_thread.start()

    def __Start(self, script_file):
        """
        Starts the script engine thread
        :return:
        """
        # Create a VM instance
        self._vm = script_vm.ScriptVM()

        # Compile the script (pass 1) of the current (main) thread
        self._compiler = script_compiler.ScriptCompiler(self._vm)
        rc = self._compiler.compile(script_file)
        if not rc:
            self._last_error = self._compiler.last_error
            return rc

        logger.info("Successfully compiled script %s", script_file)

        # Execute the compiled script on a separate thread
        self.engine_thread = dmx_engine_thread.DMXEngineThread(1, "DMXEngineThread", self._vm)
        self.engine_thread.start()

        return rc

    def Stop(self):
        """
        Stops the script engine thread
        :return:
        """
        if self.engine_thread is not None:
            self.engine_thread.Terminate()

    def Running(self):
        """
        Returns the running status of the thread
        :return: Returns True if the thread is running
        """
        return self.engine_thread and (not self.engine_thread.is_terminated)
