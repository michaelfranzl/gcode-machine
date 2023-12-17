# GcodeMachine

![Unit tests on master branch](https://github.com/michaelfranzl/gcode_machine/actions/workflows/test.yml/badge.svg?branch=master)

Python3 module containing a class that emulates a simple CNC state machine
that can be used for pre-processing and for realtime streaming of G-code to CNC controllers.

I split it off my project [gerbil](https://github.com/michaelfranzl/gerbil) to make it generally usable.

This machine is completely unit tested
and was also successfully tested by realtime processing G-code for my wood-milling CNC machine.


## Features

After passing initial conditions (machine position, coordinate system offsets, current coordinate
system) to the constructor, you can send G-code lines to the machine. Sent G-code lines change the state
of the machine:

* machine position, absolute to the machine (`position_m`)
* working position, relative to current coordinate system (`position_w`)
* coordinate system (`current_cs`)
* feed rate (`current_feed`)
* travel distances (the list `dist_xyz`, the scalar `dist`)
* spindle speed (`current_spindle_speed`)
* motion mode (`current_motion_mode`)
* distance mode (`current_distance_mode`)
* plane mode (`current_plane_mode`)
* comment (`comment`)

To change the current coordinate system, use the accessor `current_cs=`
(as this also recalculates the working position `pos_w`).

Optionally, the physical machine position can at any time be updated from the state of a real CNC controller;
for this, the accessor `position_m=` should be used (as this recalculates the working position `pos_w`).

In addition, by calling corresponding methods, the machine also can *pre-process* the set G-code line:

* variable substitution (`#1`, `#2`, etc. using the `vars` dict attribute)
* spindle scaling (`scale_spindle()` using the `spindle_factor` attribute)
* feed override (`override_feed()` using the `request_feed` attribute)
* tidying (`tidy()`) (comments, change comment format from parentheses to semicolon, spaces, command allow-list)

The methods `split_lines` and `fractionize` are pure pre-processing methods that do not modify the
state of the machine, but return a list of G-code. In a future release, these methods may be moved
to class methods, or into a separate class:

* `fractionize()` splits linear (G1) and arc (G2, G3) motions into tiny linear G1 motions
* `split_lines()` splits several space-separated commands into a list of separate commands

Callers can assign a custom callback function to the attribute `callback`, which will be called when
certain processing events happen. Currently, the only evens are:

* `on_feed_change`: When the G-Code line changes the feed speed. The first argument is the feed speed as a floating point number.
* `on_var_undefined`: When the processor encounters a variable that was not defined before. The
    first argument is the name of the undefined variable.

Last but not least, the attribute `logger` has a logger created by `logging.getLogger('gcode_machine')`
that can be used by the application.



## Installation

```sh
python -m pip install gcode-machine
```

## Usage

```python
from gcode_machine import GcodeMachine

# initial conditions
impos = (0, 0, 0) # initial machine position, default zero
ics = "G54" # initial coordinate system , default G54
cs_offsets = {"G54": (0, 0, 0), "G55": (10, 20, 30)} # coordinate system offsets

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
    gcm.parse_state()        # parse the line and update the machine state
    gcm.override_feed()      # substitute F values in the current line

    # When done processing:
    output.append(gcm.line)  # read the processed line back from the machine
    gcm.done()               # update the machine position
```

Explanation of this example:

For each iteration of the loop, feed the command line
into the machine with the method `set_line()`. Then, call individual processing
methods as needed for your application; this gives a lot of flexibility to the application.

When done with one line, call `done()` -- this will update the virtual tool position.


## Processing examples

Please also see the unit tests for the full feature set.


### Linear fractionization of arcs

```python
gcm.position_m = (0,0,0)
gcm.set_line("G2 X10 Y10 I5 J5")
gcm.parse_state()
print('\n'.join(gcm.fractionize()))
```

Result:

```gcode
;_gcm.arc_begin[G2 X10 Y10 I5 J5]
;_gcm.color_begin[0.35,0.50,0.40]
G1X-0.33Y0.353Z0
X-0.634Y0.727
X-0.913Y1.122
...
X8.037Y11.386
X8.466Y11.164
X8.878Y10.913
X9.273Y10.634
X9.647Y10.33
X10Y10
;_gcm.color_end
;_gcm.arc_end
```

### Comment transform

```python
gcm.set_line("G0 X0 (bob) Y0 (alice)")
gcm.transform_comments()
print(gcm.line)
```

Result:

```gcode
G0 X0  Y0 ;alice
```


### Tidying and allow-listing

```python
gcm.set_line("T2")
gcm.tidy()
print(gcm.line)
```

Result:

```gcode
;T02 ;_gcm.unsupported
```


### Splitting commands

```python
gcm.set_line("G55 M3 T2")
gcm.split_lines()
```

Result:

```gcode
['G55 ', 'M3 ', 'T2']
```
