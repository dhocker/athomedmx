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
# Script virtual machine
#

class ScriptVM():
    def __init__(self):
        # Script statements are a list of token lists
        self.stmts = []

        # Current DMX channel values
        self.current = [0 for v in range(0, 512)]
        self.current_len = 0

        # Target DMX channel values for fade statements
        self.target = [0 for v in range(0, 512)]
        self.target_len = 0

        # Channel definitions
        self.channels = {}

        # Value definitions
        self.values = {}

        # Main statement index
        self.main_index = -1

    def set_current_value(self, index, v):
        self.current[index] = v
        # Adjust the effective length of the DMX current message
        if index > (self.current_len - 1):
            self.current_len = index + 1