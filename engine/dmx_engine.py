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


# This class should be used as a singleton
class DMXEngine:
    def __init__(self):
        self.engine_thread = None

    def Start(self):
        """
        Starts the script engine thread
        :return:
        """
        self.engine_thread = dmx_engine_thread.DMXEngineThread(1, "TimerServiceThread")
        self.engine_thread.start()

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
        return not self.engine_thread.isTerminated()
