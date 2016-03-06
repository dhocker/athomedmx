#
# AtHomeDMX - DMX interface driver
# Copyright (C) 2016  Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

#
# DMX interface driver
#

import configuration
import pyudmx.pyudmx
import dummy_driver
import logging

logger = logging.getLogger("dmx")

def get_driver():
    """
    Returns a driver instance for the interface type specified
    in the configuration file.
    :return:
    """
    interface = configuration.Configuration.Interface().lower()
    d = None
    if interface == "udmx":
        d = pyudmx.pyudmx.uDMXDevice()
    elif interface == "dummy":
        d = dummy_driver.DummyDriver()

    if d:
        logger.info("%s driver created", interface)
    else:
        logger.error("%s is not a recognized DMX interface type", interface)

    return d