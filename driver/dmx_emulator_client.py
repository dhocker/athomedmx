#
# DMXEmulatorClient - for connecting to DMX Emulator
# Copyright © 2019  Dave Hocker (email: AtHomeX10@gmail.com)
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
#

import socket
from struct import pack


class DMXEmulatorClient:
    """
    Sends data to a DMX Emulator app
    """
    def __init__(self, num_channels, host="localhost", port=5555):
        """
        Create an instance of a DMX Emulator client
        :param num_channels:
        :param host:
        :param port:
        """
        self._num_channels = num_channels
        self._host = host
        self._port = port
        self._sock = None

    def open(self):
        """
        Open the connection to the emulator app
        :return:
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._sock.connect((self._host, self._port))
        except Exception as ex:
            print(str(ex))
            return False
        return True

    def close(self):
        """
        Close the connection to the emulator app
        :return:
        """
        try:
            self._sock.close()
            self._sock = None
        except Exception as ex:
            print(str(ex))

    def send(self, frame):
        """
        Send a frame to the emulator app
        :param frame: A list of 1-512 bytes
        :return: Count of bytes sent
        """
        try:
            sent = self._frame_send(frame)
        except Exception as ex:
            print(str(ex))
            return 0
        return sent

    def _frame_send(self, frame):
        """
        Send an entire frame
        :param frame:
        :return:
        """
        frame_size = pack('!i', len(frame))
        sent = self._block_send(frame_size)
        sent += self._block_send(frame)
        return sent

    def _block_send(self, block):
        """
        Send a block of bytes
        :param block:
        :return:
        """
        total_sent = 0
        while total_sent < len(block):
            sent = self._sock.send(block[total_sent:])
            if sent == 0:
                raise RuntimeError("DMXEmulatorClient: connection to emulator broken")
            total_sent += sent
        return total_sent
