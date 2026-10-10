import io
import os
import unittest
from unittest.mock import patch
from kex_diagnostics_panel import ISOUIDiagnosticsPanel, run_terminal, terminal_columns


class TerminalGeometryTests(unittest.TestCase):
    def test_narrow_frames_wrap_without_losing_state_text(self):
        marker = 'abcdefghijklmnopqrstuvwxyz' * 4
        panel = ISOUIDiagnosticsPanel(lambda: {'node_profile': marker})
        for width in (1, 4, 5, 20, 40, 80, 83, 120):
            with self.subTest(width=width):
                rows = panel.render_accessible_console_layout(width).splitlines()
                self.assertTrue(all(len(row) <= min(width, 83) for row in rows))
                if width >= 5:
                    content = ''.join(row[2:-2].rstrip() for row in rows[1:-1])
                    self.assertIn(marker, content)

    def test_geometry_is_read_for_each_frame(self):
        widths = iter((40, 80))
        commands = iter(('', 'X'))
        frames = []
        ISOUIDiagnosticsPanel().run_interactive_loop(lambda _: next(commands), frames.append, lambda: next(widths))
        self.assertEqual(len(frames[0].splitlines()[0]), 40)
        self.assertEqual(len(frames[1].splitlines()[0]), 80)

    def test_pty_geometry_detection(self):
        import fcntl
        import struct
        import termios
        master, slave = os.openpty()
        try:
            with os.fdopen(os.dup(slave), 'w') as stream:
                for width in (40, 80, 83):
                    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, width, 0, 0))
                    self.assertEqual(terminal_columns(stream), width)
        finally:
            os.close(master)
            os.close(slave)

    def test_alternate_screen_restored_on_exception(self):
        class TTY(io.StringIO):
            def isatty(self): return True
        stream = TTY()
        panel = ISOUIDiagnosticsPanel()
        with patch.object(panel, 'run_interactive_loop', side_effect=RuntimeError('test-only')):
            with self.assertRaises(RuntimeError): run_terminal(panel, stream, True)
        self.assertEqual(stream.getvalue(), '\x1b[?1049h\x1b[?1049l')

    def test_redirected_output_never_emits_ansi(self):
        stream = io.StringIO()
        run_terminal(ISOUIDiagnosticsPanel(), stream, True, lambda _: 'X')
        self.assertNotIn('\x1b', stream.getvalue())

if __name__ == '__main__': unittest.main()
