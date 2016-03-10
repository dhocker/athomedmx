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
# DMX script engine thread
#

import threading
import logging
import configuration
import dmx_engine_script

logger = logging.getLogger("dmx")


########################################################################
class DMXEngineThread(threading.Thread):
    ########################################################################
    # Constructor
    def __init__(self, thread_id, name):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.terminate_signal = threading.Event()
        self._script = dmx_engine_script.DMXEngineScript(self.terminate_signal)

    ########################################################################
    # Called by threading on the new thread
    def run(self):
        script_file = configuration.Configuration.Scriptfile()
        logger.info("Engine running script file %s", script_file)

        # TODO Initialize DMX script. Establish initial state.
        if not self._script.initialize():
            logger.error("Script initialize failed. Thread terminated.")
            self.terminate_signal.set()

        # run the script until termination is signaled
        self._script.execute()
        self.terminate_signal.set()

    ########################################################################
    # Terminate the engine thread. Called on the main thread.
    def Terminate(self):
        self.terminate_signal.set()
        # wait for engine thread to exit - could be a while
        logger.info("Waiting for engine thread to stop...this could take a few seconds")
        # This waits until the engine thread has stopped
        self.join()
        logger.info("Engine thread stopped")

    @property
    def is_terminated(self):
        return self.terminate_signal.isSet()