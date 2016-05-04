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
# Script compiler
#

import time
import datetime
import logging

logger = logging.getLogger("dmx")

class ScriptCompiler:
    """
    Builds an executable VM
    """
    def __init__(self, vm):
        self._last_error = None
        self._vm = vm
        self._stmt = None
        self._file_depth = 0
        self._line_number = [0]
        self._file_path = [""]
        self._do_for = False
        self._do_at = False
        self._do_forever = False

        # Valid statements and their handlers
        self._valid_stmts = {
            "set": self.set_stmt,
            "channel": self.channel_stmt,
            "value": self.value_stmt,
            "define": self.define_stmt,
            "import": self.import_stmt,
            "send": self.send_stmt,
            "step": self.step_stmt,
            "fade": self.fade_stmt,
            "step-end": self.step_end_stmt,
            "step-period": self.step_period_stmt,
            "do-for": self.do_for_stmt,
            "do-for-end": self.do_for_end_stmt,
            "do-at": self.do_at_stmt,
            "do-at-end": self.do_at_end_stmt,
            "do-forever": self.do_forever_stmt,
            "do-forever-end": self.do_forever_end_stmt,
            "pause": self.pause_stmt,
            "reset": self.reset_stmt
        }

    @property
    def last_error(self):
        """
        Returns the last logged error message
        :return:
        """
        return self._last_error

    def compile(self, script_file):
        """
        Compile the script defined by the given file handle
        :param script_file:
        :return:
        """
        self._last_error = None
        self._vm.script_file = script_file

        # Open the script file for compiling
        try:
            sf = open(script_file, "r")
            self._file_path[self._file_depth] = script_file
        except Exception as ex:
            self.script_error("Error opening script file {0}".format(script_file))
            logger.error("Error opening script file %s", script_file)
            logger.error(str(ex))
            return False

        valid = True
        stmt = sf.readline()
        while stmt and valid:
            self._stmt = stmt
            self._line_number[self._file_depth] += 1
            # case insensitive tokenization
            tokens = stmt.lower().split()
            valid = self.compile_statement(stmt, tokens)
            stmt = sf.readline()

        # TODO Validate that all script blocks are closed

        sf.close()

        # End of main file
        if self._file_depth == 0:
            logger.debug("%d statements compiled", len(self._vm.stmts))
        return valid

    def compile_statement(self, stmt, tokens):
        """
        Compile a single tokenized statement.
        :param stmt:
        :param tokens:
        :return: True if statement is valid.
        """
        # Comments and empty lines
        if len(tokens) == 0 or tokens[0].startswith("#"):
            return True

        # A statement is valid by default
        valid = True

        # Compile the statement. Here we build a list of valid script statements.
        if tokens[0] in self._valid_stmts:
            # Run the statement compiler if there is one
            if self._valid_stmts[tokens[0]]:
                # Here's where the statement is actually compiled
                compiled_tokens = self._valid_stmts[tokens[0]](tokens)
                # If the statement is valid and executable, add it to the statement list
                if compiled_tokens and len(compiled_tokens):
                    self._vm.stmts.append(compiled_tokens)
                elif compiled_tokens is None:
                    valid = False
        else:
            self.script_error("Unrecognized statement")
            valid = False

        return valid

    def add_channel(self, name, value):
        """
        Adds to the channel/value dictionary an alias channel name with channel number.
        """
        self._vm.channels[name] = int(value)

    def add_values(self, name, values):
        """
        Adds an alias with list of values to the channel/value dictionary.
        """
        int_values = map(int, values)
        self._vm.values[name] = int_values

    def add_values(self, name, values):
        """
        Adds an alias with list of values to the channel/value dictionary.
        """
        int_values = map(int, values)
        self._vm.values[name] = int_values

    def add_define(self, name, value):
        """
        Adds an alias with a float value defines dictionary.
        """
        self._vm.defines[name] = float(value)

    def is_valid_channel(self, channel):
        """
        Determines if a channel number is a valid DMX channel (1-512).
        """
        try:
            c = int(channel)
            return (c >= 1) and (c <= 512)
        except:
            return False

    def are_valid_values(self, values):
        """
        Determines if a list of values are valid DMX values (0-255).
        """
        try:
            int_values = map(int, values)
            for v in int_values:
                if (v >= 0) and (v <= 255):
                    continue
                else:
                    return False
        except Exception as ex:
            return False
        return True

    def is_valid_float(self, t):
        """
        Answers the question: Is t a valid floating point number?
        :param t:
        :return: True if t is a valid floating point number.
        """
        try:
            v = float(t)
        except:
            return False
        return True

    def resolve_tokens(self, message_tokens):
        """
        Translates statement alias references to their actual values.
        The first token is the statement verb.
        The second token is a channel number or alias.
        The remaining tokens are values or value aliases.
        """
        trans_tokens = [message_tokens[0]]
        if message_tokens[1] in self._vm.channels:
            trans_tokens.append(self._vm.channels[message_tokens[1]])
        else:
            trans_tokens.append(int(message_tokens[1]))

        for token in message_tokens[2:]:
            if token in self._vm.values:
                trans_tokens.extend(self._vm.values[token])
            else:
                trans_tokens.append(int(token))

        return trans_tokens

    def resolve_define(self, token):
        """
        Resolve a token that is subject to substitution by a define
        :param token:
        :return:
        """
        if token in self._vm.defines:
            return self._vm.defines[token]
        elif self.is_valid_float(token):
            return float(token)
        else:
            return None

    def script_error(self, message):
        """
        Single point error message logging
        :param message:
        :return:
        """
        self._last_error = []
        if self._stmt:
            error_at = "Script error in file {0} at line {1}".format(
                         self._file_path[self._file_depth],
                         self._line_number[self._file_depth])
            logger.error(error_at)
            logger.error(self._stmt)
            self._last_error.append(error_at)
        logger.error(message)
        self._last_error.append(message)

    def channel_stmt(self, tokens):
        """
        channel name 1-512
        :param tokens:
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Not enough tokens")
            return None
        if self.is_valid_channel(tokens[2]):
            self.add_channel(tokens[1], tokens[2])
        else:
            self.script_error("Channel numbers must be 1-512")
            return None
        return []

    def value_stmt(self, tokens):
        """
        value name v1...vn where vn 0-255
        :param tokens:
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Not enough tokens")
            return None
        if self.are_valid_values(tokens[2:]):
            self.add_values(tokens[1], tokens[2:])
        else:
            self.script_error("Value(s) must be 0-255")
            return None
        return []

    def define_stmt(self, tokens):
        """
        define name v where v can be any value, int or float
        :param tokens:
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Not enough tokens")
            return None
        if self.is_valid_float(tokens[2]):
            self.add_define(tokens[1], tokens[2])
        else:
            self.script_error("A defined value must be a valid float")
            return None
        return []

    def set_stmt(self, tokens):
        """
        set channel v1...vn where channel 1-512, vn 0-255
        :param tokens:
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Not enough tokens")
            return None
        trans_tokens = self.resolve_tokens(tokens)
        if self.is_valid_channel(trans_tokens[1]) and self.are_valid_values(trans_tokens[2:]):
            pass
        else:
            self.script_error("Invalid channel and/or value(s)")
            return None
        return trans_tokens

    def fade_stmt(self, tokens):
        """
        fade channel v1...vn where channel 1-512, vn 0-255
        :param tokens:
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Not enough tokens")
            return None
        trans_tokens = self.resolve_tokens(tokens)
        if self.is_valid_channel(trans_tokens[1]) and self.are_valid_values(trans_tokens[2:]):
            pass
        else:
            self.script_error("Invalid channel and/or value(s)")
            return None
        return trans_tokens

    def send_stmt(self, tokens):
        """
        send (no arguments)
        :param tokens: None required, all ignored
        :return:
        """
        return tokens

    def step_stmt(self, tokens):
        """
        Program step statement with fade-time and step-time arguments (floats)
        :param tokens: step fade-time step-time
        :return:
        """
        if len(tokens) < 3:
            self.script_error("Missing statement arguments")
            return None
        if tokens[1] in self._vm.defines:
            tokens[1] = self._vm.defines[tokens[1]]
        elif self.is_valid_float(tokens[1]):
            tokens[1] = float(tokens[1])
        else:
            self.script_error("Invalid fade time")
            return None
        if tokens[2] in self._vm.defines:
            tokens[2] = self._vm.defines[tokens[2]]
        elif self.is_valid_float(tokens[2]):
            tokens[2] = float(tokens[2])
        else:
            self.script_error("Invalid step time ")
            return None

        return tokens

    def step_end_stmt(self, tokens):
        """
        Program step end (no arguments)
        :param tokens:
        :return:
        """
        return tokens

    def step_period_stmt(self, tokens):
        """
        Sets the global step-period value. Default is 0.1 sec.
        :param tokens: step fade-time step-time
        :return:
        """
        if len(tokens) < 2:
            self.script_error("Missing statement arguments")
            return None
        pt = self.resolve_define(tokens[1])
        if pt is not None:
            tokens[1] = pt
        else:
            self.script_error("Invalid step period time")
            return None

        return tokens

    def import_stmt(self, tokens):
        """
        Import a source file directly in-line
        :param tokens: filepath
        :return:
        """
        if len(tokens) < 2:
            self.script_error("Missing file path")
            return None

        # Push the imported file onto the file stack
        self._file_depth += 1
        self._file_path.append(tokens[1])
        self._line_number.append(0)

        # This is a recursive call to compile the imported file
        # TODO Do we need a recursion limit here?
        self.compile(tokens[1])

        # Pop the file stack
        self._file_depth -= 1
        self._line_number.pop()
        self._file_path.pop()

        # The cpu will ignore this statement
        return tokens

    def do_for_stmt(self, tokens):
        """
        Execute a script block for a given period of time
        :param tokens: Duration (HH:MM)
        :return:
        """
        if len(tokens) < 2:
            self.script_error("Missing statement argument")
            return None
        if self._do_for:
            self.script_error("Only one Do-for statement can be active")
            return None

        # Translate/validate duration
        try:
            duration_struct = time.strptime(tokens[1], "%H:%M:%S")
        except Exception as ex:
            self.script_error("Invalid duration")
            return None

        tokens[1] = duration_struct
        self._do_for = True
        return tokens

    def do_for_end_stmt(self, tokens):
        """
        Marks the end/foot of a block of code headed by a Do-For statement.
        :param tokens:
        :return:
        """
        if not self._do_for:
            self.script_error("No matching Do-For is open")
            return None
        return tokens

    def do_at_stmt(self, tokens):
        """
        Executes a block of script when a given time-of-day arrives.
        :param tokens: tokens[1] is the time in HH:MM format (24 hour clock).
        :return:
        """
        if len(tokens) < 2:
            self.script_error("Missing statement arguments")
            return None
        if self._do_at:
            self.script_error("Only one Do-At statement is allowed")
            return None

        # Translate/validate start time
        try:
            start_time_struct = time.strptime(tokens[1], "%H:%M:%S")
        except Exception as ex:
            self.script_error("Invalid start time")
            return None

        tokens[1] = start_time_struct
        self._do_at = True
        return tokens

    def do_at_end_stmt(self, tokens):
        """
        Marks the end/foot of a block of code headed by a Do-At statement.
        :param tokens:
        :return:
        """
        if not self._do_at:
            self.script_error("No matching Do-At is open")
            return None
        return tokens

    def do_forever_stmt(self, tokens):
        """
        Marks the beginning of a do-forever block.
        """
        if self._do_forever:
            self.script_error("Only one Do-Forever statement is allowed")
            return None
        self._do_forever = True
        return tokens

    def do_forever_end_stmt(self, tokens):
        """
        Marks the end/foot of a block of code headed by a Do-Forever statement.
        :param tokens:
        :return:
        """
        if not self._do_forever:
            self.script_error("No matching Do-Forever is open")
            return None
        return tokens

    def pause_stmt(self, tokens):
        """
        pause hh:mm:ss
        Pauses script execution for a specified amount of time.
        """
        if len(tokens) < 2:
            self.script_error("Missing statement arguments")
            return None

        # Translate/validate pause time
        try:
            pause_struct = time.strptime(tokens[1], "%H:%M:%S")
        except Exception as ex:
            self.script_error("Invalid pause time")
            return None

        tokens[1] = pause_struct
        return tokens

    def reset_stmt(self, tokens):
        """
        Sends zeroes to all DMX channels.
        """
        return tokens
