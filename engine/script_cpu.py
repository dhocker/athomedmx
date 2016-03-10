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
# Script cpu (executes compiled scripts
#

import time
import logging

logger = logging.getLogger("dmx")

class ScriptCPU:
    def __init__(self, dmxdev, vm, terminate_event):
        self._dmxdev = dmxdev
        self._vm = vm
        self._terminate_event = terminate_event
        self._stmt_index = 0

        # Valid statements and their handlers
        self._valid_stmts = {
            "set": self.set_stmt,
            "channel": None,
            "value": None,
            "import": None,
            "send": self.send_stmt,
            "main": self.main_stmt,
            "step": None,
            "fade": None,
            "step-end": None,
            "main-end": self.main_end_stmt
        }

    def run(self):
        """
        Run the statements in the VM
        :return:
        """
        logger.info("Virtual CPU running...")
        next_index = self._stmt_index
        # Run CPU until termination is signaled by main thread
        while not self._terminate_event.isSet():
            stmt = self._vm.stmts[self._stmt_index]
            # Ignore statements with no handler
            if self._valid_stmts[stmt[0]] is not None:
                # The statement execution sets the next statement index
                next_index = self._valid_stmts[stmt[0]](stmt)
                if next_index < 0:
                    logger.error("Virtual CPU stopped due to error")
                    break
                # End of program check
                if next_index >= len(self._vm.stmts):
                    logger.info("End of script")
                    break
            else:
                next_index = self._stmt_index + 1

            self._stmt_index = next_index

            # TODO Determine wait time based on step time and fade time
            time.sleep(0.1)

        logger.info("Virtual CPU stopped")
        return next_index > 0

    def set_stmt(self, stmt):
        """
        Set one or more channel values
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        # stmt[1] is the channel (1-512)
        # stmt[2:] is/are the value(s)
        # copy the statement values to the current message register
        for i in range(0, len(stmt) - 2):
            # the -1 accounts for the fact that channels are 1-512, not 0-511
            cur_index = stmt[1] + i - 1
            self._vm.set_current_value(cur_index, stmt[i + 2])
        return self._stmt_index + 1

    def send_stmt(self, stmt):
        """
        Send the net contents of the current DMX message
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        msg = self._vm.current[:self._vm.current_len]
        logger.debug(msg)
        self._dmxdev.send_multi_value(1, msg )
        return self._stmt_index + 1

    def main_stmt(self, stmt):
        """
        Set the main loop point
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        return self._stmt_index + 1

    def main_end_stmt(self, stmt):
        """
        Change the next statement index to the main loop point
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        # This is the loop point for the main loop
        return self._vm.main_index
