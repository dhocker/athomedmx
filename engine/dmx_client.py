#
# AtHomeDMX - DMX engine client
# Copyright (C) 2016  Dave Hocker (email: AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE file).  If not, see <http://www.gnu.org/licenses/>.
#

import app_logger
import configuration
import engine.dmx_engine
import os
import sys
import glob
import app_logger

logger = app_logger.getAppLogger()

class DMXClient:
    """
    Handles commands sent by a network client.
    The commands provide the means to control the DMX engine.

    The protocol is simple.
    The client sends a command line terminated by a newline (\n).
    The server executes the command a returns a response in the form of one or more lines.
    Each response line is terminated with a newline.
    The first line of the response indicates the result: OK or ERROR.
    The end of the response is marked by an empty line (or two consecutive newlines).

    Example
    Client sends:
        scriptfiles\n
    Server responds:
        OK\n
        file1\n
        file2\n
        filen\n
        \n

    Client sends:
        bad-command\n
    Server responds:
        ERROR\n
        Unrecognized command\n
        \n
    """

    # Protocol constants
    OK_RESPONSE = "OK\n"
    ERROR_RESPONSE = "ERROR\n"
    END_RESPONSE_DELIMITER = "\n"
    LINE_END = "\n"

    # Singleton instance of DMX engine
    # TODO Access to this variable should be under lock control is multiple, concurrent sockets are supported
    dmx_engine = None
    dmx_script = None

    def __init__(self):
        self._script = None
        # Valid commands and their handlers
        self._valid_commands = {
            "scriptfiles": self.get_script_files,
            "start": self.start_script,
            "stop": self.stop_script,
            "status": self.get_status,
            "exit": self.close_connection,
            "close": self.close_connection
        }

    def execute_command(self, raw_command):
        """
        Execute a client command/request.
        :param raw_command:
        :return:
        """
        response = self._format_response(DMXClient.ERROR_RESPONSE, "Command not implemented", None)

        tokens = raw_command.lower().split()
        if (len(tokens) >= 1) and (tokens[0] in self._valid_commands):
            if self._valid_commands[tokens[0]]:
                response = self._valid_commands[tokens[0]](tokens, raw_command)
            else:
                response = self._format_response(DMXClient.ERROR_RESPONSE, "Command not implemented: {0}", tokens[0])
        else:
            response = self._format_response(DMXClient.ERROR_RESPONSE, "Unrecognized command: {0}", tokens[0])

        # Return the command generated response with the end of response
        # delimiter tacked on.
        return response + DMXClient.END_RESPONSE_DELIMITER

    def _format_response(self, result, response_text, *args):
        """
        Format a single line response
        :param result: OK or ERROR
        :param response_text: Response text string suitable for use with .format method
        :param args: Variable list of arguments for substitution in response_text
        :return:
        """
        return result + response_text.format(*args) + DMXClient.LINE_END

    def get_status(self, tokens, command):
        """
        Return current status of DMX script engine.
        :param tokens:
        :param command:
        :return:
        """
        if DMXClient.dmx_script:
            return self._format_response(DMXClient.OK_RESPONSE, "DMX Engine running script: {0}", DMXClient.dmx_script)
        return self._format_response(DMXClient.OK_RESPONSE, "DMX Engine stopped", None)

    def get_script_files(self, tokens, command):
        """
        Return a list of all of the *.dmx files in the script file directory.
        :param tokens:
        :param command:
        :return: List of file names without path.
        """
        search_for = configuration.Configuration.ScriptFileDirectory() + "/*.dmx"
        files = glob.glob(search_for)
        names = []
        for f in files:
            names.append(os.path.split(f)[1])
        response = DMXClient.OK_RESPONSE + DMXClient.LINE_END.join(names) + DMXClient.LINE_END
        return response

    def close_connection(self, tokens, command):
        """
        Close the current connection/session. Note that the DMX Engine
        state is not changed. If it is running, it stays running.
        :param tokens:
        :param command:
        :return:
        """
        return self._format_response(DMXClient.OK_RESPONSE, "Closed")

    def start_script(self, tokens, command):
        """
        Start the DMX engine running a script file
        :param tokens: tokens[1] is the script file name
        :param command:
        :return:
        """
        DMXClient.dmx_engine = engine.dmx_engine.DMXEngine()

        # Full path to script file
        # TODO Concurrency issue
        DMXClient.dmx_script = tokens[1]
        full_path = "{0}/{1}".format(configuration.Configuration.ScriptFileDirectory(), DMXClient.dmx_script)

        # Launch the DMX engine VM
        try:
            # The engine will run until terminated by stop
            # Note than the DMX enginer runs on its own thread
            DMXClient.dmx_engine.Start(full_path)
            logger.info("Engine thread started")
        except Exception as e:
            logger.error("Unhandled exception starting DMX engine")
            logger.error(e)
            logger.error(sys.exc_info()[0])
            return self._format_response(DMXClient.ERROR_RESPONSE, "Script failed to start")

        return self._format_response(DMXClient.OK_RESPONSE, "Script started")

    def stop_script(self, tokens, command):
        if DMXClient.dmx_engine:
            DMXClient.dmx_engine.Stop()
            DMXClient.dmx_script = None
            return self._format_response(DMXClient.OK_RESPONSE, "Script stopped")

        return self._format_response(DMXClient.OK_RESPONSE, "No script running")
