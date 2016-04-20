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

class DMXClient:
    """
    Handles commands sent by a network client.
    The commands provide the means to control the DMX engine.
    """

    def execute_command(self, raw_command):
        return "Handler not implemented\n"
