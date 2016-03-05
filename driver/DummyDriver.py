#
# AtHomeDMX - DMX interface driver template
# Copyright (C) 2016  Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

#
# DMX interface driver template
#

class DummyDriver:
    """
    A device driver must implement each of the methods in this class.
    The driver class name is arbitrary and generally is not exposed.
    Add the driver to the app by modifying the driver.get_driver()
    method.

    This template is implemented as a dummy device driver for testing.
    """
    def __init__(self):
        self._dev = None

    @property
    def Device(self):
        """
        Returns the wrapped usb.core.Device instance.
        Refer to the usb.core.Device class for details of the Device class.
        """
        return self._dev

    def open(self, vendor_id=0x16c0, product_id=0x5dc, bus=None, address=None):
        """
        Open the first device that matches the search criteria. Th default parameters
        are set up for the likely most common case of a single uDMX interface.
        However, for the case of multiple uDMX interfaces, you can use the
        bus and address paramters to further specifiy the uDMX interface
        to be opened.
        :param vendor_id:
        :param product_id:
        :param bus: USB bus number 1-n
        :param address: USB device address 1-n
        :return: Returns true if a device was opened. Otherwise, returns false.
        """
        return True

    def close(self):
        """
        Close and release the current usb device.
        :return: None
        """
        pass

    def send_single_value(self, channel, value):
        """
        Send a single value to the uDMX
        :param channel: DMX channel number, 1-512
        :param value: Value to be sent to channel, 0-255
        :return: number of bytes actually sent
        """
        return 1

    def send_multi_value(self, channel, values):
        """
        Send multiple consecutive bytes to the uDMX
        :param channel: The starting DMX channel number, 1-512
        :param values: any sequence of integer values that can be converted
        to a bytearray (e.g a list). Each value 0-255.
        :return: number of bytes actually sent
        """
        return len(values)
