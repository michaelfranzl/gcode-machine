import unittest

from gcode_machine import GcodeMachine


class Test(unittest.TestCase):
    g55_offset = (10, 20, 30)

    def setUp(self):
        # initial conditions
        impos = (0, 0, 0)
        ics = 'G54'
        cs_offsets = {'G54': (0, 0, 0), 'G55': Test.g55_offset}

        # make a new machine
        self.gcm = GcodeMachine(impos, ics, cs_offsets)
        self.gcm.cs_offsets['G55'] = (10, 20, 30)

    def test_default_current_distance_mode(self):
        self.assertEqual(self.gcm.current_distance_mode, 'G90')

    def test_default_current_motion_mode(self):
        self.assertEqual(self.gcm.current_motion_mode, 0)

    def test_default_plane_mode(self):
        self.assertEqual(self.gcm.current_plane_mode, 'G17')

    def test_reset(self):
        callback_received = False

        def callback(event, args):
            nonlocal callback_received
            self.assertEqual(event, 'on_feed_change')
            self.assertEqual(args, None)
            callback_received = True

        self.gcm.callback = callback
        self.gcm.reset()
        self.assertEqual(self.gcm.vars, {})
        self.assertEqual(self.gcm.current_feed, None)
        self.assertEqual(self.gcm.current_motion_mode, 0)
        self.assertEqual(self.gcm.current_distance_mode, 'G90')
        self.assertTrue(callback_received)


    def test_position_m_setter(self):
        self.gcm.current_cs = 'G55'
        self.gcm.position_m = [101, 102, 103]
        self.assertEqual(self.gcm.pos_m, [101, 102, 103])
        self.assertEqual(self.gcm.pos_w[0], 91)
        self.assertEqual(self.gcm.pos_w[1], 82)
        self.assertEqual(self.gcm.pos_w[2], 73)

    def test_position_m_getter(self):
        self.gcm.pos_m = [101, 102, 103]
        self.assertEqual(self.gcm.position_m, [101, 102, 103])

    def test_current_cs_getter(self):
        self.assertEqual(self.gcm.current_cs, "G54")
        self.assertEqual(self.gcm.pos_w, [0, 0, 0])

    def test_current_cs_setter(self):
        self.gcm.current_cs = 'G55'
        self.assertEqual(self.gcm.pos_w, [-10, -20, -30])
        self.assertEqual(self.gcm.cs, 'G55')

    def test_set_line(self):
        self.gcm.set_line('G0 X0 (comment)')
        self.assertEqual(self.gcm.line, 'G0 X0 ')

    def test_set_line_transforms_comments(self):
        self.gcm.set_line('G0 (inner comment) X0 (trailing comment)')
        self.assertEqual(self.gcm.comment, ';trailing comment')
        self.assertEqual(self.gcm.line, 'G0  X0 ')

    def test_split_lines(self):
        self.gcm.set_line('G54 M3 T2; do too much')
        result = self.gcm.split_lines()
        self.assertEqual(result[0], 'G54 ; do too much')
        self.assertEqual(result[1], 'M3 ')
        self.assertEqual(result[2], 'T2')

    def test_strip(self):
        self.gcm.set_line(" G0  X0 \n")
        self.gcm.strip()
        self.assertEqual(self.gcm.line, 'G0X0')

    def test_tidy_padding_G(self):
        self.gcm.set_line("G1")
        self.gcm.tidy()
        self.assertEqual(self.gcm.line, 'G01')

    def test_tidy_padding_M(self):
        self.gcm.set_line("M1")
        self.gcm.tidy()
        self.assertEqual(self.gcm.line, 'M01')

    def test_tidy_whitelist(self):
        self.gcm.set_line("T1")
        self.gcm.tidy()
        self.assertEqual(self.gcm.line, ';T01 ;_gcm.unsupported')

    def test_parse_state_motion_mode(self):
        self.gcm.set_line("G3 X42")
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_motion_mode, 3)

    def test_parse_state_distance_mode(self):
        self.gcm.set_line('G91')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_distance_mode, 'G91')

    def test_parse_state_plane_mode_G18(self):
        self.gcm.set_line('G18')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_plane_mode, 'G18')

    def test_parse_state_plane_mode_G19(self):
        self.gcm.set_line('G19')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_plane_mode, 'G19')

    def test_parse_state_current_cs(self):
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_cs, 'G55')

    def test_parse_state_contains_feed(self):
        self.gcm.set_line('G0 X0 F42')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.contains_feed, True)

    def test_override_feed_callback(self):
        self.gcm.do_feed_override = False
        self.gcm.set_line('G0 X0 F42')
        self.gcm.parse_state()
        callback_received = False

        def callback(event, args):
            nonlocal callback_received
            self.assertEqual(event, 'on_feed_change')
            self.assertEqual(args, 42)
            callback_received = True

        self.gcm.callback = callback
        self.gcm.override_feed()
        self.assertEqual(callback_received, True)

    def test_override_feed_1(self):
        self.gcm.do_feed_override = True
        self.gcm.request_feed = 100
        self.gcm.set_line('G0 X0 F42')
        self.gcm.parse_state()
        callback_received = False

        def callback(event, args):
            nonlocal callback_received
            self.assertEqual(event, 'on_feed_change')
            self.assertEqual(args, 100)
            callback_received = True

        self.gcm.callback = callback
        self.gcm.override_feed()
        self.assertEqual(self.gcm.line, 'G0 X0F100.0')

    def test_override_feed_2(self):
        self.gcm.do_feed_override = True
        self.gcm.request_feed = 100
        self.gcm.set_line('G0 X0')
        self.gcm.parse_state()
        callback_received = False

        def callback(event, args):
            nonlocal callback_received
            self.assertEqual(event, 'on_feed_change')
            self.assertEqual(args, 100)
            callback_received = True

        self.gcm.callback = callback
        self.gcm.override_feed()
        self.assertEqual(self.gcm.line, 'G0 X0F100.0')

    def test_parse_state_feed_in_current_line(self):
        self.gcm.set_line('G0 X0 F42.3')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.feed_in_current_line, 42.3)

    def test_parse_state_contains_spindle(self):
        self.gcm.set_line('S1')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.contains_spindle, True)

    def test_scale_spindle(self):
        self.gcm.spindle_factor = 2
        self.gcm.set_line('G0 X10 S200')
        self.gcm.parse_state()
        self.gcm.scale_spindle()
        self.assertEqual(self.gcm.line, 'G0 X10S400')

    def test_parse_state_current_spindle_speed(self):
        self.gcm.set_line('S100')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.current_spindle_speed, 100)

    def test_parse_state_current_motion_mode_offset(self):
        self.gcm.set_line('G2 X10 Y11 I6 J7 K8')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.offset[0], 6.0)
        self.assertEqual(self.gcm.offset[1], 7.0)
        self.assertEqual(self.gcm.offset[2], 8.0)

    def test_parse_state_current_motion_mode_radius(self):
        self.gcm.set_line('G2 X10 Y11 R42.3')
        self.gcm.parse_state()
        self.assertEqual(self.gcm.radius, 42.3)

    def test_parse_state_target_w_absolute(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G90')  # absolute
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.target_w[0], 100.5)
        self.assertEqual(self.gcm.target_w[1], 100.6)
        self.assertEqual(self.gcm.target_w[2], 100.7)

    def test_parse_state_target_m_absolute(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G90')  # absolute
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.target_m[0], 100.5 + Test.g55_offset[0])
        self.assertEqual(self.gcm.target_m[1], 100.6 + Test.g55_offset[1])
        self.assertEqual(self.gcm.target_m[2], 100.7 + Test.g55_offset[2])

    def test_parse_state_distance_absolute(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G90')  # absolute
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.dist_xyz[0], 100.5 + Test.g55_offset[0] - 1)
        self.assertEqual(self.gcm.dist_xyz[1], 100.6 + Test.g55_offset[1] - 2)
        self.assertEqual(self.gcm.dist_xyz[2], 100.7 + Test.g55_offset[2] - 3)
        self.assertAlmostEqual(self.gcm.dist, 205.82395390235803)

    def test_parse_state_target_w_relative(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G91')  # relative
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.target_w[0], 100.5 - Test.g55_offset[0] + 1)
        self.assertEqual(self.gcm.target_w[1], 100.6 - Test.g55_offset[1] + 2)
        self.assertEqual(self.gcm.target_w[2], 100.7 - Test.g55_offset[2] + 3)

    def test_parse_state_target_m_relative(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G91')  # relative
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.target_m[0], 100.5 + 1)
        self.assertEqual(self.gcm.target_m[1], 100.6 + 2)
        self.assertEqual(self.gcm.target_m[2], 100.7 + 3)

    def test_parse_state_distance_relative(self):
        self.gcm.set_line('G0 X1 Y2 Z3')
        self.gcm.parse_state()
        self.gcm.done()

        self.gcm.set_line('G91')  # relative
        self.gcm.parse_state()
        self.gcm.set_line('G55')
        self.gcm.parse_state()
        self.gcm.set_line('G1 X100.5 Y100.6 Z100.7')
        self.gcm.parse_state()

        self.assertEqual(self.gcm.dist_xyz[0], 100.5)
        self.assertEqual(self.gcm.dist_xyz[1], 100.6)
        self.assertEqual(self.gcm.dist_xyz[2], 100.7)
        self.assertAlmostEqual(self.gcm.dist, 174.24436863210244)

    def test_done_positions(self):
        self.gcm.set_line('G55')
        self.gcm.parse_state()

        self.gcm.set_line('G1 X1 Y2 Z3; move')
        self.gcm.parse_state()
        self.gcm.done()

        self.assertEqual(self.gcm.comment, '; move')

        self.assertEqual(self.gcm.current_motion_mode, 1)

        self.assertEqual(self.gcm.pos_w[0], 1)
        self.assertEqual(self.gcm.pos_w[1], 2)
        self.assertEqual(self.gcm.pos_w[2], 3)

        self.assertEqual(self.gcm.pos_m[0], Test.g55_offset[0] + 1)
        self.assertEqual(self.gcm.pos_m[1], Test.g55_offset[1] + 2)
        self.assertEqual(self.gcm.pos_m[2], Test.g55_offset[2] + 3)

    def test_done_motion_mode(self):
        self.gcm.set_line('G2 X10 Y11 I6 J7 K8')
        self.gcm.parse_state()
        self.gcm.done()

        self.assertEqual(self.gcm.current_motion_mode, None)

    def test_set_vars(self):
        self.gcm.set_line('#1=42.30000')
        self.gcm.find_vars()

        self.assertEqual(self.gcm.vars['1'], '42.3')
        self.assertEqual(self.gcm.line, ';#1=42.30000')

    def test_set_vars_undefined(self):
        self.gcm.set_line('#2')
        self.gcm.find_vars()

        self.assertEqual(self.gcm.vars['2'], None)

    def test_substitute_vars(self):
        self.gcm.set_line('#1=42.30000')
        self.gcm.find_vars()

        self.gcm.set_line('G0 X#1')
        self.gcm.substitute_vars()

        self.assertEqual(self.gcm.line, 'G0 X42.3')

    def test_substitute_vars_undefined(self):
        self.gcm.set_line('G0 X#1')
        self.gcm.substitute_vars()

        self.assertEqual(self.gcm.line, '')

    def test_fractionize_lines(self):
        self.gcm.do_fractionize_lines = True
        self.gcm.set_line('G1 X10; comment')
        self.gcm.parse_state()
        result = self.gcm.fractionize()
        self.assertEqual(result[0], ';_gcm.line_begin[G1 X10]; comment')
        self.assertEqual(result[1], 'G1X0.5')
        self.assertEqual(result[-3], 'X9.5')
        self.assertEqual(result[-2], 'X10')
        self.assertEqual(result[-1], ';_gcm.line_end')

    def test_fractionize_arcs(self):
        self.gcm.do_fractionize_arcs = True
        self.gcm.set_line('G2 X10 Y10 I5 J5; comment')
        self.gcm.parse_state()
        result = self.gcm.fractionize()
        self.assertEqual(result[0], ';_gcm.arc_begin[G2 X10 Y10 I5 J5]; comment')
        self.assertEqual(result[1], 'G1X-0.33Y0.353')
        self.assertEqual(result[-3], 'X9.647Y10.33')
        self.assertEqual(result[-2], 'X10Y10')
        self.assertEqual(result[-1], ';_gcm.arc_end')
