import struct
import unittest
from unittest.mock import patch
from hci import audit_context, render, RuntimePanel


class HCITests(unittest.TestCase):
    def frame(self):
        return {'state': {'I': 'independent/node', 'O': {'origin': 1}, 'q': 0,
                         't': 10, 'workers': {'publisher': {'pid': 123, 'ready': True}}},
                'readiness_mask': 7, 'state_digest': 'a' * 64,
                'crc32': 1234, 'frame_bytes': 320}

    def test_widths_include_narrow_terminals(self):
        for width in (1, 3, 4, 20, 80, 83, 120):
            for line in render(self.frame(), width).splitlines():
                self.assertEqual(len(line), min(width, 83))

    def test_zero_retains_identity_and_origin(self):
        output = render(self.frame())
        self.assertIn('independent/node', output)
        self.assertIn("Origin: {'origin': 1}", output)
        self.assertIn('Coordinate q: 0', output)

    def test_untrusted_text_cannot_inject_terminal_controls(self):
        frame = self.frame()
        frame['state']['I'] = '\x1b[2J\n\u754c'
        output = render(frame)
        self.assertNotIn('\x1b', output)
        self.assertTrue(all(len(line) == 83 for line in output.splitlines()))

    def test_single_dispatch_and_exit(self):
        panel = RuntimePanel('/tmp', 'node')
        with patch.object(panel, 'read', return_value=self.frame()) as read:
            panel.dispatch(' r ')
            read.assert_called_once()
            panel.dispatch('X')
            self.assertFalse(panel.running)

    def test_invalid_commands_do_not_read_or_mutate(self):
        panel = RuntimePanel('/tmp', 'node')
        with patch.object(panel, 'read') as read:
            with self.assertRaises(ValueError): panel.dispatch('M')
            read.assert_not_called()

    def test_context_parse_is_not_admission(self):
        wire = struct.pack('>4sQ4sI32s', b'KEX!', 2, b'ARM6', 4, b'x'*32) + b'y'*64
        value = audit_context(wire, b'ARM6', 1)
        self.assertFalse(value['admitted'])
        self.assertEqual(value['signature'], b'y'*64)
        self.assertEqual(value['target'], b'x'*32)

    def test_malformed_replay_and_architecture_rejected(self):
        wire = struct.pack('>4sQ4sI32s', b'KEX!', 2, b'ARM6', 4, b'x'*32) + b'y'*64
        for args in ((wire[:52], b'ARM6', 1), (wire+b'x', b'ARM6', 1),
                     (wire, b'ARM6', 2), (wire, b'ARCH', 1),
                     (wire, b'ARM6', True), (wire, b'ARM666', 1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError): audit_context(*args)


if __name__ == '__main__': unittest.main()
