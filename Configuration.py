#
# AtHomePowerlineServer - networked server for CM11/CM11A/XTB-232 X10 controllers
# Copyright (C) 2014  Dave Hocker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

#
# Server configuration
#
# The AtHomeDMX.conf file holds the configuration data in JSON format.
# Currently, it looks like this:
#
# {
#   "Configuration":
#   {
#     "X10ControllerDevice": "XTB232",
#     "ComPort": "COM1"
#   }
# }
#
# The JSON parser is quite finicky about strings being quoted as shown above.
#
# This class behaves like a singleton class. There is only one instance of the configuration.
# There is no need to create an instance of this class, as everything about it is static.
#

import os
import json
import logging

logger = logging.getLogger("dmx")

########################################################################
class Configuration():

  ActiveConfig = None
  
  ######################################################################
  def __init__(self):
    Configuration.LoadConfiguration()
    pass
    
  ######################################################################
  # Load the configuration file
  @classmethod
  def LoadConfiguration(cls):
    # Try to open the conf file. If there isn't one, we give up.
    try:
      cfg_path = Configuration.GetConfigurationFilePath()
      print "Opening configuration file {0}".format(cfg_path)
      cfg = open(cfg_path, 'r')
    except Exception as ex:
      print "Unable to open {0}".format(cfg_path)
      print str(ex)
      return
      
    # Read the entire contents of the conf file
    cfg_json = cfg.read()
    cfg.close()
    #print cfg_json
    
    # Try to parse the conf file into a Python structure
    try:
      config = json.loads(cfg_json)
      # The interesting part of the configuration is in the "Configuration" section.
      cls.ActiveConfig = config["Configuration"]
    except Exception as ex:
      print "Unable to parse configuration file as JSON"
      print str(ex)
      return
      
    #print str(Configuration.ActiveConfig)
    return

  ######################################################################
  @classmethod
  def IsLinux(cls):
    """
    Returns True if the OS is of Linux type (Debian, Ubuntu, etc.)
    """
    return os.name == "posix"

  ######################################################################
  @classmethod
  def IsWindows(cls):
    """
    Returns True if the OS is a Windows type (Windows 7, etc.)
    """
    return os.name == "nt"


  ######################################################################
  @classmethod
  def get_config_var(cls, var_name):
      try:
          return cls.ActiveConfig[var_name]
      except Exception as ex:
          logger.error("Unable to find configuration variable {0}".format(var_name))
          logger.error(str(ex))
          pass
      return None

  ######################################################################
  @classmethod
  def Scriptfile(cls):
    return cls.get_config_var("ScriptFile")

  ######################################################################
  @classmethod
  def Logconsole(cls):
    return cls.get_config_var("LogConsole").lower() == "true"

  ######################################################################
  @classmethod
  def Logfile(cls):
    return cls.get_config_var("LogFile")

  ######################################################################
  @classmethod
  def LogLevel(cls):
    return cls.get_config_var("LogLevel")

  ######################################################################
  @classmethod
  def GetConfigurationFilePath(cls):
    """
    Returns the full path to the configuration file
    """
    file_name = 'AtHomeDMX.conf'

    # A local configuration file (in the home directory) takes precedent
    if os.path.exists(file_name):
        return file_name

    if Configuration.IsLinux():
      return "/etc/{0}".format(file_name)

    return file_name
