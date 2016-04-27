# GcodeMachine

Python3 module containing a class that emulates a simple CNC state machine
that can be used for simulation and processing of G-code.

After setting initial machine conditions (position, feed, etc.)
you can send Gcode lines to it. Sent Gcode lines change the state
of the machine, most importantly:

* machine position
* coordinate system position
* feed rate
* travel distances
* spindle speed
* motion mode
* distance mode
* plane mode
* etc.

In addition, by calling corresponding methods, the machine also can
transform the Gcode, e.g. for

* variable substitution
* feed override
* cleanup (comments, spaces, whitelisted commands)
* fractionizing of lines and arcs down into small linear fragments


Typical use:

    from gcode_machine import GcodeMachine
    
    # initial conditions
    initial_machine_position = impos = (0,0,0)
    initial_coordinate_system = ics = "G54"
    coordinate_system_offsets = cs_offsets = {"G54":(0,0,0)}
    
    # make a new machine
    gcm = GcodeMachine(impos, ics, cs_offsets)
    
    input = ["G0 Z-10", "G1 X10 Y10"]
    output = []
    
    for line in input:
        gcm.set_line(line)       # feed the line into the machine
        gcm.strip()              # clean up whitespace
        gcm.tidy()               # filter commands by a whitelist
        gcm.find_vars()          # parse variable usages
        gcm.substitute_vars()    # substitute variables
        gcm.parse_state()        # parse positions etc. and update the machine state
        gcm.override_feed()      # substitute F values
        gcm.transform_comments() # transform parentheses to semicolon comments
        output.append(gcm.line)  # read the processed line back from the machine
        gcm.done()               # update the machine position

For each interation of the loop, you should feed the command line
into the machine with the method `set_line`. Then, call processing
methods as needed for your application (see source code for all methods).

Also, you can inspect the machine state as needed.
When done with one line, call `done` -- this will update the virtual tool position.

Processing can happen as fast as possible, or asynchronously in a realtime manner.

This machine is experimental and subject to further extensions. It works well for simple cases though.

I believe the class is well documented. Also, code is documentation.


## Examples

Linear fractionization of arcs:

    gcm.position_m = (0,0,0)
    gcm.set_line("G2 X10 Y10 I5 J5")
    gcm.parse_state()
    print('\n'.join(gcm.fractionize()))
    
Result: 

    ;_gcm.arc_begin[G2 X10 Y10 I5 J5]
    ;_gcm.color_begin[0.35,0.50,0.40]
    G1X-0.33Y0.353Z0
    X-0.634Y0.727
    X-0.913Y1.122
    { snip }
    X8.037Y11.386
    X8.466Y11.164
    X8.878Y10.913
    X9.273Y10.634
    X9.647Y10.33
    X10Y10
    ;_gcm.color_end
    ;_gcm.arc_end

    
Comment transform:

    gcm.set_line("G0 X0 (bob) Y0 (alice)")
    gcm.transform_comments()
    print(gcm.line)
    
Result:

    G0 X0  Y0 ;alice

    
Strip unsupported commands (whitelist based):

    gcm.set_line("T2")
    gcm.tidy()
    print(gcm.line)
    
Result:

    ;T02 ;_gcm.unsupported
    
    
Split commands (some Gcode generators do this stupid thing):

    gcm.set_line("G55 M3 T2")
    gcm.split_lines()
    
Result:

    ['G55 ', 'M3 ', 'T2']


## License

gcode_machine - Copyright (c) 2016 Michael Franzl

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.