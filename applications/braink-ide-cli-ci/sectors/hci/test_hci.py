import unittest
from keddeh_hci_core import KEDDEHHCIContract, BRAINKSurface
from kex_diagnostics_panel import ISOUIDiagnosticsPanel


class HCITests(unittest.TestCase):
    def test_layout_handles_long_unicode_and_control_input(self):
        p = ISOUIDiagnosticsPanel(lambda: {'quorum': '\x1b[2J' + '界' * 150})
        lines = p.render_accessible_console_layout().splitlines()
        self.assertTrue(all(len(line) == 83 and line.isascii() for line in lines))
        self.assertNotIn('\x1b', '\n'.join(lines))

    def test_unobserved_hardware_is_not_certified(self):
        layout = ISOUIDiagnosticsPanel().render_accessible_console_layout()
        self.assertIn('NOT_OBSERVED', layout)
        self.assertNotIn('CERTIFIED', layout)
        self.assertNotIn('SYSTEM SECURE', layout)

    def test_unbound_compaction_does_not_mutate_telemetry(self):
        state = {'mram_saturation': 24}
        p = ISOUIDiagnosticsPanel(lambda: state)
        p.process_user_interaction('m')
        self.assertEqual(state['mram_saturation'], 24)
        self.assertIn('UNBOUND', p.status)

    def test_bound_action_calls_once_and_displays_actual_result(self):
        calls = []
        p = ISOUIDiagnosticsPanel(compact=lambda: calls.append('M') or {'receipt': 'test-only'})
        p.process_user_interaction(' m ')
        self.assertEqual(calls, ['M'])
        self.assertIn('test-only', p.status)

    def test_exception_never_retries_operation(self):
        calls = []
        def failing():
            calls.append('A')
            raise OSError('uncertain')
        p = ISOUIDiagnosticsPanel(stage_update=failing)
        p.process_user_interaction('A')
        self.assertEqual(calls, ['A'])
        self.assertIn('OUTCOME_UNKNOWN', p.status)

    def test_invalid_input_never_dispatches(self):
        calls = []
        p = ISOUIDiagnosticsPanel(compact=lambda: calls.append('M'))
        for command in ('', 'MM', 'M\nA', '\x1bM'):
            p.process_user_interaction(command)
        self.assertEqual(calls, [])

    def test_eof_ends_session_without_action(self):
        p = ISOUIDiagnosticsPanel()
        def eof(_): raise EOFError()
        p.run_interactive_loop(eof, lambda _: None)
        self.assertFalse(p.running)

    def test_surface_trace_does_not_claim_signature_or_custody(self):
        text = BRAINKSurface(KEDDEHHCIContract('BRAINK')).execute_view_render({'buffer_bytes': 4})
        self.assertIn('LOCAL_TRACE:', text)
        self.assertNotIn('NOMINAL', text)
        self.assertNotIn('EVIDENCE_OK', text)

if __name__ == '__main__': unittest.main()
