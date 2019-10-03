#
# AtHomeDMX - DMX emulator interface driver
# Copyright © 2019  Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#
# This is an adapter to the DMX Emulator client
#

from driver.dmx_emulator_client import DMXEmulatorClient


class DMXEmulatorDriver:
    """
    A device driver must implement each of the methods in this class.
    The driver class name is arbitrary and generally is not exposed.
    Add the driver to the app by modifying the driver.get_driver()
    method.

    This template is implemented as a dummy device driver for testing.
    """
    def __init__(self):
        self._dev = DMXEmulatorClient(512)
        self._frame = bytearray(0 for n in range(512))
        # High water mark is in range 1-512
        self._frame_hi_mark = 0

    @property
    def Device(self):
        """
        Returns the wrapped usb.core.Device instance.
        Refer to the usb.core.Device class for details of the Device class.
        """
        return self._dev

    def open(self, vendor_id=0x16c0, product_id=0x5dc, bus=None, address=None):
        """
        Open the DMX emulator client
        :param vendor_id: ignored
        :param product_id: ignored
        :param bus: ignored
        :param address: ignored
        :return: Returns true if a device was opened. Otherwise, returns false.
        """
        return self._dev.open()

    def close(self):
        """
        Close the current DMX emulator instance.
        :return: None
        """
        self._dev.close()

    def send_single_value(self, channel, value):
        """
        Send a single value to the uDMX
        :param channel: DMX channel number, 1-512
        :param value: Value to be sent to channel, 0-255
        :return: number of bytes actually sent
        """
        if channel > self._frame_hi_mark:
            self._frame_hi_mark = channel
        self._frame[channel - 1] = value
        # Only send the used bytes
        new_frame = bytes(self._frame[n] for n in range(self._frame_hi_mark))
        self._dev.send(new_frame)
        return 1

    def send_multi_value(self, channel, values):
        """
        Send multiple consecutive bytes to the uDMX
        :param channel: The starting DMX channel number, 1-512
        :param values: any sequence of integer values that can be converted
        to a bytearray (e.g a list). Each value 0-255.
        :return: number of bytes actually sent
        """
        len_values = len(values)
        hi_water_mark = channel + len_values - 1
        if hi_water_mark > self._frame_hi_mark:
            self._frame_hi_mark = hi_water_mark
        vx = 0
        # Update last sent frame with new values
        for c in range(channel - 1, channel + len_values - 1):
            self._frame[c] = values[vx]
            vx += 1
        new_frame = bytes(self._frame[n] for n in range(self._frame_hi_mark))
        self._dev.send(new_frame)
        return len_values
