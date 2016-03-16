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
import datetime
import logging

logger = logging.getLogger("dmx")

class ScriptCPU:
    def __init__(self, dmxdev, vm, terminate_event):
        """
        Constructor
        :param dmxdev: A DMX device instance
        :param vm: A script VM instance
        :param terminate_event: A threading event to be tested for termination
        :return: None
        """
        self._dmxdev = dmxdev
        self._vm = vm
        self._terminate_event = terminate_event
        # This is the equivalent of the next instruction address
        self._stmt_index = 0
        self._send_count = 0
        self._fade_time = 0.0
        self._step_time = 0.0
        # Runat control
        self._runat_active = False
        self._run_end_time = None
        self._runat_stmt = -1

        # Valid statements and their handlers
        self._valid_stmts = {
            "set": self.set_stmt,
            "channel": None,
            "value": None,
            "import": None,
            "send": self.send_stmt,
            "main": self.main_stmt,
            "step": self.step_stmt,
            "fade": self.fade_stmt,
            "step-end": self.step_end_stmt,
            "main-end": self.main_end_stmt,
            "step-period": self.step_period_stmt,
            "runat": self.runat_stmt
        }

    def run(self):
        """
        Run the statements in the VM
        :return:
        """
        logger.info("Virtual CPU running...")
        # The statement index is like an instruction address
        next_index = self._stmt_index

        # Run CPU until termination is signaled by main thread
        while not self._terminate_event.isSet():
            stmt = self._vm.stmts[self._stmt_index]
            # Ignore statements with no handler
            if self._valid_stmts[stmt[0]] is not None:
                # The statement execution sets the next statement index
                next_index = self._valid_stmts[stmt[0]](stmt)
                # If the statement threw an exception end the script
                if next_index < 0:
                    logger.error("Virtual CPU stopped due to error")
                    break

                # End of program check
                if next_index >= len(self._vm.stmts):
                    logger.info("End of script")
                    break
            else:
                # Unrecognized statements are treated as no-ops.
                # Since the compile phase fails bad statements, the
                # only reason to be here is for a statement that
                # has not yet been implemented.
                next_index = self._stmt_index + 1

            # This sets the next statement
            self._stmt_index = next_index

            # End of RunAt program check
            # This will set the next statement index at end of program time
            self.runat_time_check()

        logger.info("Virtual CPU stopped")
        self._reset()
        return next_index > 0

    def _reset(self):
        """
        Reset all DMX channels to value zero.
        This should turn everything off.
        :return:
        """
        # TODO Determine if this is the right thing to do
        reset_msg = [0 for v in range(0, 512)]
        self._send_message(1, reset_msg)
        logger.info("All DMX channels reset")

    def _send_message(self, channel, msg):
        """
        Send a DMX message
        :param channel: DMX channel 1-512
        :param msg: list of channel values to be sent (all 512)
        :return:
        """
        logger.debug(msg)
        # Originally, the intent was to send the minimum number of bytes.
        # However, it appears that either the pyUSB package or libusb package
        # occasionally throws an overflow error if something other than a full size message
        # of 512 bytes is sent.
        # This try/catch is here to handle that error.
        success = False
        retry_count = 0
        while not success:
            try:
                self._send_count += 1
                self._dmxdev.send_multi_value(channel, msg)
                success = True
            except Exception as ex:
                logger.error("Unhandled exception sending DMX message")
                logger.error(str(ex))
                logger.error("Send count %d", self._send_count)
                logger.error(msg)
                retry_count += 1
                if retry_count > 5:
                    raise ex

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
            # We set both the current and target so the delta is zero
            self._vm.set_current_value(cur_index, stmt[i + 2])
            self._vm.set_target_value(cur_index, stmt[i + 2])
        return self._stmt_index + 1

    def fade_stmt(self, stmt):
        """
        Fade one or more channel values. Fading goes from the current value
        to the target value.
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        # stmt[1] is the channel (1-512)
        # stmt[2:] is/are the value(s)
        # copy the statement values to the target message register
        for i in range(0, len(stmt) - 2):
            # the -1 accounts for the fact that channels are 1-512, not 0-511
            cur_index = stmt[1] + i - 1
            # We set both the current and target so the delta is zero
            self._vm.set_target_value(cur_index, stmt[i + 2])
        return self._stmt_index + 1

    def send_stmt(self, stmt):
        """
        Send the net contents of the current DMX message
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        # Send the entire current message register
        self._send_message(1, self._vm.current)

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

    def step_stmt(self, stmt):
        """
        Begin a program step
        :param stmt: step fade-time step-time
        :return:
        """
        logger.debug(stmt)
        # Capture times for step-end
        self._fade_time = float(stmt[1])
        self._step_time = float(stmt[2])
        return self._stmt_index + 1

    def step_end_stmt(self, stmt):
        """
        Step end - execute the step statements.
        Mostly, this is about fading values from some starting
        value to a target value.
        :param stmt:
        :return:
        """

        # TODO This is messy and needs to be refactored/cleaned up

        logger.debug(stmt)

        # Send the entire current message register
        # This amounts to the starting point for the step
        logger.debug("Sending current DMX message")
        self._send_message(1, self._vm.current)

        # How many increments to complete fade
        incrs = self._fade_time / self._vm.step_period_time
        logger.debug("%f fade increments", incrs)

        # Build a copy of the starting channel values
        base_values = list(self._vm.current)

        # Compute fade value increment for each channel value
        delta_values = []
        for i in range(0, len(self._vm.target)):
            # Value change per period
            v = float(self._vm.target[i] - self._vm.current[i]) / incrs
            # Note that delta values are floats
            delta_values.append(v)
            if v != 0.0:
                logger.debug("Channel %d delta fade %f", i, v)

        # During fade/step time, check termination event to avoid hangs
        # Note that if fade time > step time, the target value will not be reached.
        fade_time = self._fade_time
        step_time = self._step_time
        fade_count = 1.0 # Intentionally a float
        while (not self._terminate_event.isSet()) and (step_time > 0.0):
            # Wait for step period time
            time.sleep(self._vm.step_period_time)

            # Until fade time has passed...
            if fade_time > 0.0:
                # Adjust the current message register with the fade increments
                # Send the altered message register
                changed = False
                for i in range(0, len(self._vm.current)):
                    # Value change per period
                    if delta_values[i] != 0.0:
                        # Apply fade increment to current value.
                        # This is done in a way that avoids truncation/rounding issues
                        self._vm.current[i] = base_values[i] + int(delta_values[i] * fade_count)
                        # Make sure adjusted value stays in range 0-255
                        if self._vm.current[i] < 0:
                            self._vm.current[i] = 0
                        elif self._vm.current[i] > 255:
                            self._vm.current[i] = 255
                        changed = True

                # If fading changed any values, send them
                if changed:
                    self._send_message(1, self._vm.current)

                # Last fade increment
                if fade_time <= self._vm.step_period_time:
                    logger.debug("Fade ended")
                fade_count += 1.0

            fade_time -= self._vm.step_period_time
            step_time -= self._vm.step_period_time

            # If the RunAt duration has expired, return to the RunAt statement
            if not self.runat_time_check():
                return self._stmt_index

        # Exit the step
        return self._stmt_index + 1

    def step_period_stmt(self, stmt):
        """
        Sets the global step period time
        :param stmt:
        :return:
        """
        logger.debug(stmt)
        self._vm.step_period_time = float(stmt[1])
        return self._stmt_index + 1

    def runat_stmt(self, stmt):
        """
        Run the program beginning at a given time and ending at duration time later.
        :param stmt: stmt[1] is the start time struct and stmt[2] is the duration
        time struct.
        :return: The runat statement does not complete until the specified
        time arrives.
        """

        # If we are under RunAt control, ignore
        if self._runat_active:
            return self._stmt_index + 1

        now = datetime.datetime.now()
        run_start_time = datetime.datetime(now.year, now.month, now.day, stmt[1].tm_hour, stmt[1].tm_min)
        logger.info("Waiting from %s until %s", str(now), str(run_start_time))
        while not self._terminate_event.isSet():
            time.sleep(1.0)
            now = datetime.datetime.now()
            # As soon as we get the start HH:MM we are ready to run
            if (now.hour == run_start_time.hour) and (now.minute == run_start_time.minute):
                # We're now under RunAt control
                self._runat_active = True
                self._runat_stmt = self._stmt_index
                # Set end time
                self._run_end_time = now + \
                    datetime.timedelta(seconds=(stmt[2].tm_hour * 60 * 60) + (stmt[2].tm_min * 60) + stmt[2].tm_sec)
                logger.info("Run program beginning at %s", str(now))

                # Within one minute after run time
                break

        return self._stmt_index + 1


    def runat_time_check(self):
        """
        Answers the question: Are we in the RunAt duration?
        :return: Returns True if we are in the RunAt duration
        """
        if self._runat_active:
            # A RunAt statement is active.
            # When the duration expires...
            now = datetime.datetime.now()
            if (now.hour == self._run_end_time.hour) and (now.minute == self._run_end_time.minute):
                # Stop running the program and set the stmt index back to the RunAt statement
                logger.info("Run program ended at %s", str(now))
                # We reset all DMX channels under the assumption the program will start over
                self._reset()
                self._runat_active = False
                # We want to put the next statement back to the RunAt
                self._stmt_index = self._runat_stmt
                return False

        # If no RunAt statement is active, we are always running
        return True