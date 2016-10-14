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
        # Do-For control
        self._do_for_active = False
        self._do_for_elapsed_time = None
        self._do_for_start_time = None
        self._do_for_stmt = -1
        # Do-At control
        self._do_at_active = False
        self._do_at_stmt = -1
        # Do-Until control
        self._do_until_active = False
        self._run_until_time = None
        self._do_until_stmt = -1
        # Do-forever control
        self._do_forever_stmt = -1

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
            "do-for": self.do_for_stmt,
            "do-for-end": self.do_for_end_stmt,
            "do-at": self.do_at_stmt,
            "do-at-end": self.do_at_end_stmt,
            "do-until": self.do_until_stmt,
            "do-until-end": self.do_until_end_stmt,
            "do-forever": self.do_forever_stmt,
            "do-forever-end": self.do_forever_end_stmt,
            "pause": self.pause_stmt,
            "reset": self.reset_stmt
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
                logger.debug(stmt)
                next_index = self._valid_stmts[stmt[0]](stmt)
                # If the statement threw an exception end the script
                if next_index < 0:
                    logger.error("Virtual CPU stopped due to error")
                    break
            else:
                # Unrecognized statements are treated as no-ops.
                # Since the compile phase fails bad statements, the
                # only reason to be here is for a statement that
                # has not yet been implemented.
                next_index = self._stmt_index + 1

            # End of program check
            next_index = self.end_of_program_check(next_index)
            if next_index >= len(self._vm.stmts):
                # Time to terminate the script
                break

            # This sets the next statement
            self._stmt_index = next_index

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
        # Send the entire current message register
        self._send_message(1, self._vm.current)

        return self._stmt_index + 1

    def main_stmt(self, stmt):
        """
        Set the main loop point
        :param stmt:
        :return:
        """
        return self._stmt_index + 1

    def main_end_stmt(self, stmt):
        """
        Change the next statement index to the main loop point
        :param stmt:
        :return:
        """
        # This is the loop point for the main loop
        return self._vm.main_index

    def step_stmt(self, stmt):
        """
        Begin a program step
        :param stmt: step fade-time step-time
        :return:
        """
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

        # Exit the step
        return self._stmt_index + 1

    def step_period_stmt(self, stmt):
        """
        Sets the global step period time
        :param stmt:
        :return:
        """
        self._vm.step_period_time = float(stmt[1])
        return self._stmt_index + 1

    def do_for_stmt(self, stmt):
        """
        Execute a script block for a given duration of time.
        :param stmt: stmt[1] is the duration time struct.
        :return:
        """

        # If we are under Do-For control, ignore. Should be prevented at compile phase.
        if self._do_for_active:
            return self._stmt_index + 1

        self._do_for_active = True
        self._do_for_stmt = self._stmt_index

        # Determine the end time
        # Use the start time and a timedelta that allows second accuracy
        now = datetime.datetime.now()
        self._do_for_elapsed_time = datetime.timedelta(seconds=(stmt[1].tm_hour * 60 * 60) + (stmt[1].tm_min * 60) + stmt[1].tm_sec)
        self._do_for_start_time = now
        logger.info("Do-For %s", str(self._do_for_elapsed_time))

        return self._stmt_index + 1

    def do_for_end_stmt(self, stmt):
        """
        Foot of Do-For loop. Repeat script block until time expires.
        :return:
        """
        if self._do_for_active:
            # A Do-For statement is active.
            # When the duration expires...
            now = datetime.datetime.now()
            elapsed = now - self._do_for_start_time
            # TODO Include seconds in duration
            if elapsed >= self._do_for_elapsed_time:
                # Stop running the script block and set the stmt index to the next statement
                logger.info("Do-For loop ended at %s", str(now))
                self._do_for_active = False
                next_stmt = self._stmt_index + 1
            else:
                # Loop back to top of script block
                next_stmt = self._do_for_stmt + 1
        else:
            next_stmt = self._stmt_index + 1

        return next_stmt

    def do_at_stmt(self, stmt):
        """
        Executes a script block when a given time-of-day arrives.
        :param stmt: stmt[1] is a tm_struct defining the time of day. The hour and minute is
        all that is used.
        :return:
        """

        # If we are under Do-At control, ignore
        if self._do_at_active:
            return self._stmt_index + 1

        # Determine the start time
        now = datetime.datetime.now()
        run_start_time = datetime.datetime(now.year, now.month, now.day, stmt[1].tm_hour, stmt[1].tm_min, stmt[1].tm_sec)
        # If the start time is earlier than now, adjust to tomorrow
        if run_start_time < now:
            # Start is tomorrow
            run_start_time += datetime.timedelta(days=1)

        # We're now under Do-At control
        self._do_at_active = True
        self._do_at_stmt = self._stmt_index

        logger.info("Waiting until %s...", str(run_start_time))

        # Wait for start time to arrive. Break out on termination signal.
        while not self._terminate_event.isSet():
            time.sleep(1.0)
            now = datetime.datetime.now()
            # The deltatime will be negative until we cross the Do-At time
            dt = now - run_start_time
            if (dt.days == 0) and (dt.seconds >= 0):
                logger.info("Do-At begins at %s", str(now))

                # On to the next sequential statement
                break

        # Execution continues at the next statement after the Do-At
        return self._stmt_index + 1

    def do_at_end_stmt(self, stmt):
        """
        Serves as the foot of the Do-At loop.
        :param stmt:
        :return:
        """
        if not self._do_at_active:
            logger.info("No matching Do-At statement")
            return -1

        # Reset state. Turn off all DMX channels.
        self._do_at_active = False
        self._reset()

        # Execution returns to the matching Do-At statement
        return self._do_at_stmt

    def do_until_stmt(self, stmt):
        """
        Executes a script block until a given time-of-day arrives.
        :param stmt: stmt[1] is a tm_struct defining the time of day. The hour and minute is
        all that is used.
        :return:
        """

        # If we are under Do-Until control, ignore
        if self._do_until_active:
            return self._stmt_index + 1

        # Determine the until time
        now = datetime.datetime.now()
        self._run_until_time = datetime.datetime(now.year, now.month, now.day, stmt[1].tm_hour, stmt[1].tm_min, stmt[1].tm_sec)
        # If the start time is earlier than now, adjust to tomorrow
        if self._run_until_time < now:
            # Until time is tomorrow
            self._run_until_time += datetime.timedelta(days=1)

        # We're now under Do-Until control
        self._do_until_active = True
        self._do_until_stmt = self._stmt_index

        logger.info("Running until %s...", str(self._run_until_time))

        # Execution continues at the next statement after the Do-Until
        return self._stmt_index + 1

    def do_until_end_stmt(self, stmt):
        """
        Serves as the foot of the Do-Until loop.
        :param stmt:
        :return:
        """
        if not self._do_until_active:
            logger.info("No matching Do-Until statement")
            return -1

        # Terminate break out
        if self._terminate_event.isSet():
            return self._stmt_index + 1

        # Check for until time to arrive. Break out when it does.
        now = datetime.datetime.now()
        if now >= self._run_until_time:
            logger.info("Do-Until occurs at %s", str(now))
            # On to the next sequential statement
            return self._stmt_index + 1

        # Execution returns to the matching Do-Until statement
        return self._do_until_stmt

    def end_of_program_check(self, next_index):
        """
        End of program occurs when the next statement index is past
        the end of the statement list.
        :param next_index:
        :return: Returns the next statement index to be executed. If RunAt
        is effective, the next index will point to the RunAt statement.
        If RunAt is not in effect, the next index will be the first statement
        past the end of the statement list.
        """
        if next_index >= len(self._vm.stmts):
            logger.info("End of script")

        return next_index

    def do_forever_stmt(self, stmt):
        """
        Executes the following script block until the program is terminated.
        """
        # There is no error checking here because it is all done in the compile phase.
        self._do_forever_stmt = self._stmt_index

        # Execution continues at the next statement after the Do-Forever
        return self._stmt_index + 1

    def do_forever_end_stmt(self, stmt):
        """
        Foot of the the do-forever block
        """
        return self._do_forever_stmt

    def pause_stmt(self, stmt):
        """
        Pause the script for a given amount of time
        """
        # Determine the time when the pause will end
        now = datetime.datetime.now()
        pause_time = datetime.timedelta(
            seconds=(stmt[1].tm_hour * 60 * 60) + (stmt[1].tm_min * 60) + stmt[1].tm_sec)
        logger.info("Pausing for %s", str(pause_time))

        end_time = datetime.datetime.now() + pause_time
        logger.info("Pause ends at %s", str(end_time))

        # Wait for end of pause time to arrive. Break out on termination signal.
        now = datetime.datetime.now()
        while (not self._terminate_event.isSet()) and (now <= end_time):
            time.sleep(1.0)
            now = datetime.datetime.now()

        return self._stmt_index + 1

    def reset_stmt(self, stmt):
        """
        Reset all DMX channels by sending zeroes
        """
        self._reset()
        return self._stmt_index + 1