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
import glob
import json
from collections import OrderedDict

logger = app_logger.getAppLogger()

class DMXClient:
    """
    Handles commands sent by a network client.
    The commands provide the means to control the DMX engine.

    The protocol is simple.
    The client sends a command line terminated by a newline (\n).
    The server executes the command a returns a JSON formatted response.
    The response is one line, terminated with a newline.
    The JSON payload is a dictionary. The following properties appear in all responses.
        command: the command for which the response was generated
        result: OK or ERROR
    The remainder of the response is command dependent. Here some additional properties
    that may appear
        state: RUNNING, STOPPED or CLOSED
        message: Message text usually explaining an error
        scriptfile: The name of the currently running script file

    Example
    Client sends:
        scriptfiles\n
    Server responds:
        {"command": "scriptfiles", "result": "OK", "scriptfiles": ["definitions.dmx", "test-end.dmx", "test.dmx"]}\n

    Client sends:
        bad-command\n
    Server responds:
        {"command": "bad-command", "result": "ERROR", "messages": ["Unrecognized command"]}\n

    The easiest way to experiment with the client is to use telnet. Simply open
    a connection a type commands.
        telnet server host

    Recognized commands
        status
        scriptfiles
        start <script-name>
        stop
        quit
        close
    """

    # Protocol constants
    OK_RESPONSE = "OK"
    ERROR_RESPONSE = "ERROR"
    END_RESPONSE_DELIMITER = "\n"
    STATUS_RUNNING = "RUNNING"
    STATUS_STOPPED = "STOPPED"
    STATUS_CLOSED = "CLOSED"

    # Singleton instance of DMX engine
    # TODO Access to this variable should be under lock control is multiple, concurrent sockets are supported
    dmx_engine = engine.dmx_engine.DMXEngine()
    dmx_script = None

    class Response:
        def __init__(self, command, result=None, state=None):
            self._response = OrderedDict()
            self._response["command"] = command
            if result:
                self._response["result"] = result
            if state:
                self._response["state"] = state

        def set_result(self, result):
            self._response["result"] = result

        def set_state(self, state):
            self._response["state"] = state

        def set_value(self, key, value):
            self._response[key] = value

        def is_closed(self):
            if "state" in self._response:
                return self._response["state"] == DMXClient.STATUS_CLOSED
            return False

        def __str__(self):
            return json.dumps(self._response) + DMXClient.END_RESPONSE_DELIMITER

    def __init__(self):
        """
        Constructor for an instance of DMXClient
        """
        # Valid commands and their handlers
        self._valid_commands = {
            "scriptfiles": self.get_script_files,
            "start": self.start_script,
            "stop": self.stop_script,
            "status": self.get_status,
            "quit": self.quit_session,
            "close": self.close_connection,
            "configuration": self.get_configuration,
        }

    def execute_command(self, raw_command):
        """
        Execute a client command/request.
        :param raw_command:
        :return:
        """
        tokens = raw_command.lower().split()
        if (len(tokens) >= 1) and (tokens[0] in self._valid_commands):
            if self._valid_commands[tokens[0]]:
                response = self._valid_commands[tokens[0]](tokens, raw_command)
            else:
                r = DMXClient.Response(tokens[0], result=DMXClient.ERROR_RESPONSE)
                r.set_value("messages", "Command not implemented")
                response = r
        else:
            r = DMXClient.Response(tokens[0], result=DMXClient.ERROR_RESPONSE)
            r.set_value("messages", "Unrecognized command")
            response = r

        # Return the command generated response with the end of response
        # delimiter tacked on.
        return response

    def get_configuration(self, tokens, command):
        """
        Return current server configuration.
        :param tokens:
        :param command:
        :return:
        """
        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE)

        r.set_value("port", configuration.Configuration.Port())
        r.set_value("interface", configuration.Configuration.Interface())
        r.set_value("scriptfiledirectory", configuration.Configuration.ScriptFileDirectory())
        r.set_value("logfile", configuration.Configuration.Logfile())
        r.set_value("logconsole", configuration.Configuration.Logconsole())
        r.set_value("loglevel", configuration.Configuration.LogLevel())

        return r

    def get_status(self, tokens, command):
        """
        Return current status of DMX script engine.
        :param tokens:
        :param command:
        :return:
        """
        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE)

        if DMXClient.dmx_engine.Running():
            r.set_state(DMXClient.STATUS_RUNNING)
            r.set_value("scriptfile", DMXClient.dmx_script)
        else:
            r.set_state(DMXClient.STATUS_STOPPED)

        return r

    def get_script_files(self, tokens, command):
        """
        Return a list of all of the *.dmx files in the script file directory.
        :param tokens:
        :param command:
        :return: List of file names without path.
        """
        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE)

        search_for = configuration.Configuration.ScriptFileDirectory() + "/*.dmx"
        files = glob.glob(search_for)
        names = []
        for f in files:
            names.append(os.path.split(f)[1])

        r.set_value("scriptfiles", names)
        return r

    def close_connection(self, tokens, command):
        """
        Close the current connection/session. Note that the DMX Engine
        state is not changed. If it is running, it stays running.
        :param tokens:
        :param command:
        :return:
        """
        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE, state=DMXClient.STATUS_CLOSED)
        return r

    def quit_session(self, tokens, command):
        """
        Close the current connection/session. Note that the DMX Engine
        is stopped if it is running.
        :param tokens:
        :param command:
        :return:
        """
        # If necessary, stop the DMX Engine
        DMXClient.stop_engine()

        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE, state=DMXClient.STATUS_CLOSED)
        return r

    def start_script(self, tokens, command):
        """
        Start the DMX engine running a script file
        :param tokens: tokens[1] is the script file name
        :param command:
        :return:
        """

        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE)

        # At least one command argument is required - the script name
        if len(tokens) < 2:
            r.set_result(DMXClient.ERROR_RESPONSE)
            r.set_value("messages", ["Missing script file name argument"])
            return r

        # Full path to script file
        # TODO Concurrency issue
        r.set_value("scriptfile", tokens[1])
        full_path = "{0}/{1}".format(configuration.Configuration.ScriptFileDirectory(), tokens[1])
        if not os.path.exists(full_path):
            r.set_result(DMXClient.ERROR_RESPONSE)
            r.set_value("messages", ["Script file does not exist"])
            return r

        # Stop a running script
        DMXClient.stop_engine()

        # Compile the script
        if DMXClient.dmx_engine.compile(full_path):
            DMXClient.dmx_script = tokens[1]
        else:
            r.set_result(DMXClient.ERROR_RESPONSE)
            r.set_state(DMXClient.STATUS_STOPPED)
            r.set_value("messages", DMXClient.dmx_engine.last_error)
            return r
        # Execute the compiled script
        # The engine will run until terminated by stop
        # Note than the DMX engine runs the script on its own thread
        if not DMXClient.dmx_engine.execute():
            r.set_result(DMXClient.ERROR_RESPONSE)
            r.set_state(DMXClient.STATUS_STOPPED)
            r.set_value("messages", ["Script failed to start"])
            return r

        r.set_state(DMXClient.STATUS_RUNNING)

        return r

    def stop_script(self, tokens, command):
        """
        Stop any running script. If no script is running,
        the command does nothing (this is not considered an error).
        :param tokens:
        :param command:
        :return:
        """
        r = DMXClient.Response(tokens[0], result=DMXClient.OK_RESPONSE)

        DMXClient.stop_engine()

        r.set_state(DMXClient.STATUS_STOPPED)
        return r

    @classmethod
    def stop_engine(cls):
        """
        If the script engine is running, stop it.
        :return: True if the engine was running and stopped.
        Otherwise, False.
        """
        if cls.dmx_engine.Running():
            cls.dmx_engine.Stop()
            cls.dmx_script = None
            return True
        return False
