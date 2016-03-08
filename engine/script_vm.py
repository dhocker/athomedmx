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
        # Target DMX channel values for fade statements
        self.target = [0 for v in range(0, 512)]
        # Channel definitions
        self.channels = {}
        # Value definitions
        self.values = {}