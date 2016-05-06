# AtHomeDMX - DMX Server
Copyright © 2016 by Dave Hocker

## Overview
The AtHomeDMX server is designed to run simple DMX controlled light shows on
light weight hardware using an inexpensive DMX controller.
The original motive for the AtHomeDMX server was for
something to run a holiday lighting program using a Raspberry Pi.

The server can be controlled locally or remotely via a TCP based communication interface
([the remote control interface](#remote-control)).
The interface is suited to command-line control via telnet or a front-end client application
that uses the interface as an API.

A show is constructed as a script using a relatively simple
scripting language ([Script Engine](#script-engine)). Scripts are stored in script
files in the [ScriptFileDirectory](#configuration) on the AtHomeDMX host.

Using the remote control interface you can:

* view a list of available script files
* start a script file
* stop the currently running script file
* view the status of the AtHomeDMX server

To work with DMX lights, you will need a DMX controller interface. AtHomeDMX comes with a driver for the
USB-based [Anyma uDMX](https://wiki.openlighting.org/index.php/Anyma_uDMX) interface. 
Inexpensive, compatible uDMX interfaces can be found on various
popular web retail sites (e.g. eBay, Amazon and Alibaba Express). If you want to
use another DMX controller you will need to write your own driver. The athomedmx/driver/dummy_driver.py
file provides a template for implementing a driver. The DUMMY driver can be used as a mock device.
This is a good solution for testing.

If you are interested in learning more about DMX see [DMX](https://en.wikipedia.org/wiki/DMX512).

## License

The AtHomeDMX server is licensed under the GNU General Public License v3 as published 
by the Free Software Foundation, Inc..
See the LICENSE file for the full text of the license.

## Source Code

The full source is maintained on [GitHub](https://www.github.com/dhocker/athomedmx).

AtHomeDMX was developed using PyCharm CE. PyCharm CE is highly recommended. However, if you
want to make changes, a good text editor of your choice is all that is really required.

## Execution Environment

AtHomeDMX is written in Python 2.7. A suitable execution environment would use 
virtualenv and virtualenvwrapper to create a working virtual environment. 
The requirements.txt file can be used with pip to create the required virtual environment with all dependencies.
if you are using a uDMX controller, AtHomeDMX requires the [pyudmx](https://www.github.com/dhocker/pyudmx) package.

AtHomeDMX has been tested on Raspbian Jessie and OS X 10.11.4. It has not been tried or
tested on any version of Windows.

## Configuration <a id="configuration"></a>

AtHomeDMX is setup using the JSON formatted **at_home_dmx.conf** file. The easiest way to create a configuration
file is to copy at_home_dmx.example.conf to at_home_dmx.conf and edit as required.

|Key           | Use         |
|------------- |-------------|
| Interface | uDMX or DUMMY. Case insensitive. |
| ScriptFileDirectory | Full path to location where script files are stored. Script files should be named with a .dmx extension. |
| LogFile | Full path and name of log file. |
| LogConsole | True or False. If True logging output will be routed to the log file and the console. |
| LogLevel | Debug, Info, Warn, or Error. Case insensitive. |
| Port | The TCP port to be used for remote control. The default is 5000. |

## Script Engine <a id="script-engine"></a>
The script engine executes the contents of a script file. It is a two phase interpreter. The first phase is a
compile phase where statements are validated and value definitions are captured. The second phase is an 
execution phase. Because of the two phase design, definitional statements (channel, value, define) are
compiled so that the last definition wins. That is, if a name is defined multiple times, the last
definition wins.

## Script File
A script file contains any number of statements. 

* Each line is a statement.
* Leading and trailing blanks are ignored.
* Blank lines are ignored.
* Lines that begin with a # are ignored.
* Everything is case insensitive.

## Statements

### Syntax
A statement consists of a number of white space delimited tokens. Except for the # character, there
are no special rules for characters. The single quote, double quote and all other special characters are treated
just like alpha-numeric characters.

The first token of a statement is the statement identifier (a.k.a. an opcode or command).

    statement [argument [argument...argument]]

### Names
Several statements involve the definition of a name (a constant). The only rule for a name is that it
cannot contain blanks. A name can contain any alpha-numeric or special character.
Single or double quotes have no special significance. 

### Comment
Any line whose first non-blank character is a # is a comment. Comments are ignored.

    # This is a comment

Comments are not recognized as such when placed at the end of an otherwise valid statement.

### Channel
A channel statement defines a named DMX channel. Valid DMX channels are n=1-512.

    channel name n
    
### Value
A value statement defines a named channel value or set of values (e.g. rgb). Valid channel values are v=0-255.

    value name v1 v2...vn

### Define
A define statement defines a general use numeric value. Typically, a defined value is a time value used on a step
statement. A valid define value is an integer or floating point number. For example, 10.0 or 10.

    define name value

### Global Step Period Time
This statement sets the global step period time (in seconds). Each step moves
forward at this rate. It’s the clock tick interval. The default step period is 0.1 seconds. 

    step-period 0.1

### Import
The import statement includes another file into the script file. This works like a C/C++ include or a Python import
statement. The content of the imported file is inserted into the script in line. There is no duplicate import
checking. If you import the same file multiple times, its contents will be inserted multiple times.

    import filename

### Set
This statement sets one or more channel value(s) for transmission.
The channel values are essentially queued. This allows the values from multiple set statements to
be aggregated. Use the send statement to actually send
the queued values. This process is a bit like making changes and then actually committing them.

    set channel v1...vn

### Send
The send statement sends all accumulated channel values (from set statements) to the DMX controller.
Essentially, the send statement acts like a commit action.

    send

### Do-At
The Do-At statement is designed for running a lighting program on a daily basis. This is the kind of thing that
you would do for a holiday lighting program. The Do-At statement allows you to specify a time of day when the
program is to run. The lighting program is the script block between the Do-At statement
and its corresponding Do-At-End statement. There can only be one Do-At statement in a script.
This is a simple limitation to avoid overly complicating the script language.

    do-at hh:mm:ss
        # script block statements
    do-at-end
    
The argument is the time of day (24 hour clock) when the program is to run. When the Do-At statement executes, 
it puts the script into a wait state where it waits for the time of day to arrive.

Example

    do-at 18:00:00
        # script block statements
    do-at-end

This example waits until 18:00:00 (6:00pm) at which time it runs the script block.

Note: If you need to break a waiting Do-At statement, use the stop command on the remote control interface.

### Do-At-End
The Do-At-End statement serves as the foot of the Do-At loop or the end of the Do-At block.
When script execution reaches the Do-At-End statement, all DMX channels are reset and 
execution returns to the corresponding Do-At statement.

    do-at-end

### Do-For
The Do-For statement executes a script block for a given period of time. The script block is the
set of statements between the Do-For statement and its corresponding Do-For-End statement.
    
    do-for hh:mm:ss
        # script block statements
    do-for-end
    
The argument is a duration in hours, minutes and seconds.

Currently, Do-For statements cannot be nested.

### Do-For-End
The Do-For-End statement is the foot of the Do-For loop. When execution reaches the Do-For-End statement,
the elapsed time since the entry into the Do-For loop is evaluated. If the elapsed time is less than
the Do-For duration, execution returns to the next statement after the Do-For. If the elapsed time
is greater than or equal to the Do-For duration, execution continues with the statement after
the Do-For-End. Note that with this behavior, the time spent in the loop may actually be longer than
the Do-For duration. This is completely dependent on how long it takes to execute the script block.

    do-for-end

### Step
Step starts the definition of what is to be done in a step. A step consists of a fade-time and a step-time.
DMX channel value fading occurs during fade-time. The step ends after step-time has elapsed. Fade-time/step-time
are advanced according to the step-period time.
While not a requirement, generally step-time >= fade-time. If fade-time is greater than step-time,
the fade will not complete.

    step fade-time step-time

Use fade statements to specify which DMX channel values are to be faded.

### Step-end
Step-end executes the set and fade statements included within the step. If the step includes any
set statements, they are immediately sent. After sending queued channel values, any pending
fade statements are executed until fade-time elapses.
After fade-time elapses, it waits for the step-time to elapse.

    step-end

### Fade 
Fade causes channel values to move from their current values to 
target values over fade-time. How a value fades is 
determined by the step-period and fade-time. A DMX channel value is changed incrementally by a
delta value (dv) which is determined by:

    dv = (target - current) / (fade-time / step-period)

Example: Assume the current value for channel 1 is 100 and the target value is 200. The fade-time is 1.0 second and
the step-time is 0.2 second. Substituting, we have:

    dv = (200 - 100) / (1.0 / 0.2) = 20

For each step-period during fade-time, the channel 1 value will be
incremented by one dv value = 20.

Note that dv can be positive or negative. In the above example, if the current channel 1 value was 200 and 
the target value was 100, the dv value would be -20. In this case, the channel 1 value would be decreased by 20
for each step-period.

The fade statement syntax is

	fade channel v1 v2...vn

### Do-forever
The do-forever statement is the script equivalent of the C/C++ "while true" statement. The block of script
following the do-forever statement is executed until script engine execution is terminated.
There can only be one Do-Forever statement in a script.

    do-forever
        # Block of statements
    do-forever-end

Note: Script engine execution can be terminiated in two ways:
* the remote control interface stop command
* killing the AtHomeDMX server process (e.g. ctrl-C or kill command or service stop command)

### Do-forever-end
The do-forever-end statement is the foot of the do-forever loop. When the statement executes, it sets the next
statement to the statement following the corresponding do-forever statement.

    do-forever-end

### Pause
Pause suspends the execution of the script for the specified amount of time.

    pause hh:mm:ss
    
### Reset
Reset sends zero values to all 512 DMX channels.

    reset

### Script File EOF
When end-of-file is reached, the script terminates. As part of script termination, all DMX channels
are reset.

### Script Example
The following script runs one hour every day at 6:30pm local time.

    #
    # DMX test script
    #
    
    # Device channel definitions (channel name number 1-512)
    channel tp64rgb  1
    channel tp64mode 6
    channel tp64dimmer 7
    
    # Value definitions (value name integer 0-255...)
    value rgb-off 0 0 0
    value rgb-on 255 255 255
    value off 0
    value on 255
    value rgb-mode 0
    
    # Time definitions
    define default-fade-time 3.0
    define default-step-time 5.0
    define periodtime 0.2
    
    # Set the global step time
    step-period periodtime
    
    # Initial state (set channel value(s))
    set tp64rgb rgb-off
    set tp64mode rgb-mode
    set tp64dimmer off
    send
    
    do-at 18:30:00   
        # This one hour loop contains three steps with a step-time of 5.0 seconds.
        # That means one pass through the main loop will take 3 * 5.0 = 15.0 seconds.
        # Note that indention is not required, but it does improve readability.
        do-for 01:00:00
            # Each step runs for the step-time
            # Step 1
            step default-fade-time default-step-time
                # Immediate changes
                set tp64rgb rgb-off
                set tp64dimmer on
                # Values fade from their initial to target values over fade-time
                # This will fade the r and b channels from 0 to 255 over 3 seconds
                fade tp64rgb on 0 on
            step-end
    
            # Intervening statements
            set tp64rgb rgb-off
            set tp64dimmer on
            send
        
            # Step 2
            step default-fade-time default-step-time
                fade tp64rgb 0 on on
            step-end
        
            set tp64rgb rgb-off
            set tp64dimmer on
            send
        
            # Step 3
            step default-fade-time default-step-time
                fade tp64rgb on on 0
            step-end
        
            set tp64dimmer off
            send
        do-for-end
    do-at-end

## Remote Control Interface <a id="remote-control"></a>
The remote control interface uses a simple TCP socket connection to implement a client-server
arrangement. The client sends simple commands and the server responds with JSON formatted responses.
A basic telnet app can be used as the client or a UI application can be written.

A connection to the AtHomeDMX server can usually be opened like this.

    telnet hostname 5000

## Control Commands
Each command produces a JSON formatted response. There are several response
properties that are common to most command responses.

|Property      | Description |
|------------- |-------------|
| command | The command that produced this response. |
| result | OK or ERROR. |
| messages | If the result == ERROR this property (a list) will describe the error. |

Commands that produce an error will include an error message list in the response.


### DMX Engine Status
The status command returns the current status of the DMX Engine.

**Command:** status

**Response:** {"command": "status", "result": "OK", "state": "STOPPED"}

**Response:** {"command": "status", "result": "OK", "state": "RUNNING", "scriptfile": "test.dmx"}

### List Script Files
The scriptfiles command returns a list of all of the available script files.

**Command:** scriptfiles

**Response:** {"command": "scriptfiles", "result": "OK", "scriptfiles": ["definitions.dmx", "test-end.dmx", "test.dmx"]}

### Start Script Execution
The start command is used to start execution of a specified script. Any running script is stopped before the
new script is started.

**Command:** start script-file-name

**Response:** {"command": "start", "result": "OK", "scriptfile": "test.dmx", "state": "RUNNING"}

**Error Response:** {"command": "start", "result": "ERROR", "messages": ["Script file does not exist"], "scriptfile": "x.dmx"}

Note that the messages property is a list. Script compilation errors will typically produce a multi-line message.

### Stop Script Execution
The stop command terminates execution of the current script. If no script is running,
the command is ignored.

**Command:** stop

**Response:** {"command": "stop", "result": "OK", "state": "STOPPED"}

### Close Socket Connection
The close command closes the TCP socket while leaving the DMX Engine in its current
state. If the DMX Engine is running it will continue running. Use the close command
when you want to start a script and leave it running.

**Command:** close

**Response:** {"command": "close", "result": "OK", "state": "CLOSED"}

### Quit
The quit command stops the DMX Engine and closes the TCP socket. Essentially, it is a stop command
followed by a close command.

**Command:** quit

**Response:** {"command": "quit", "result": "OK", "state": "CLOSED"}

### Telnet Session Example
The following console output shows an example of how the remote control interface works.

    telnet localhost 5000
    Trying ::1...
    telnet: connect to address ::1: Connection refused
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    scriptfiles
    {"command": "scriptfiles", "result": "OK", "scriptfiles": ["definitions.dmx", "test-end.dmx", "test.dmx"]}
    status
    {"command": "status", "result": "OK", "state": "STOPPED"}
    start test.dmx
    {"command": "start", "result": "OK", "scriptfile": "test.dmx", "state": "RUNNING"}
    stop
    {"command": "stop", "result": "OK", "state": "STOPPED"}
    close
    {"command": "close", "result": "OK", "state": "CLOSED"}
    Connection closed by foreign host.

## Running AtHomeDMX Server as a Daemon
On a Linux based system (e.g. Raspbian Jessie on a Raspberry Pi), you can easily run the AtHomeDMX
server as a daemon. The athomedmxD.sh shell script will help you do just that.

Assuming Raspbian:

    sudo cp athomedmxD.sh /etc/init.d
    sudo update-rc.d athomedmxD.sh defaults
    sudo service athomedmxD.sh start
