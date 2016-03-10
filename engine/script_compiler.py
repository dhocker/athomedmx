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

import logging

logger = logging.getLogger("dmx")

class ScriptCompiler:
    """
    Builds an executable VM
    """
    def __init__(self, vm):
        self._vm = vm
        self._stmt = None
        self._line_number = 0

        # Valid statements and their handlers
        self._valid_stmts = {
            "set": self.set_stmt,
            "channel": self.channel_stmt,
            "value": self.value_stmt,
            "import": None,
            "send": self.send_stmt,
            "main": self.main_stmt,
            "step": None,
            "fade": None,
            "step-end": None,
            "main-end": self.main_end_stmt
        }

    def compile(self, script_file):
        """
        Compile the script defined by the given file handle
        :param script_file:
        :return:
        """

        # Open the script file for compiling
        try:
            sf = open(script_file, "r")
        except:
            logger.error("Error opening script file %s", script_file)
            return False

        valid = True
        stmt = sf.readline()
        while stmt and valid:
            self._stmt = stmt
            self._line_number += 1
            # case insensitive tokenization
            tokens = stmt.lower().split()
            valid = self.compile_statement(stmt, tokens)
            stmt = sf.readline()

        sf.close()
        logger.debug("%d statements compiled", len(self._vm.stmts))
        return valid

    def compile_statement(self, stmt, tokens):
        # Comments and empty lines
        if len(tokens) == 0 or tokens[0] == "#":
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

    def resolve_tokens(self, message_tokens):
        """
        Translates statement alias references to their defined values.
        The first token is the statement verb.
        The second token is a channel alias.
        The remaining tokens are value aliases.
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

    def script_error(self, message):
        """
        Single point error message logging
        :param message:
        :return:
        """
        logger.error("Script error at line %d", self._line_number)
        logger.error(self._stmt)
        logger.error(message)

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

    def send_stmt(self, tokens):
        """
        send (no arguments)
        :param tokens:
        :return:
        """
        return tokens

    def main_stmt(self, tokens):
        """
        main loop point (no arguments)
        :param tokens:
        :return:
        """
        # This should point to the main statement
        self._vm.main_index = len(self._vm.stmts)
        return tokens

    def main_end_stmt(self, tokens):
        """
        main loop end point (no arguments)
        :param tokens:
        :return:
        """
        return tokens