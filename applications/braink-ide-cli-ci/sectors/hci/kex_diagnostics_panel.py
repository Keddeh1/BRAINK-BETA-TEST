"""Dependency-free terminal panel. Hardware operations require native adapters."""
import argparse
import json
from pathlib import Path
from keddeh_hci_core import terminal_text


class ISOUIDiagnosticsPanel:
    def __init__(self, read_state=None, stage_update=None, compact=None):
        self.read_state = read_state
        self.actions = {'A': stage_update, 'M': compact}
        self.running = True
        self.status = 'No hardware operation executed'

    @staticmethod
    def rows(text):
        text = terminal_text(text)
        return ['| ' + text[i:i+79].ljust(79) + ' |' for i in range(0, max(1, len(text)), 79)]

    def render_accessible_console_layout(self):
        try:
            state = self.read_state() if self.read_state else {}
            if not isinstance(state, dict):
                raise ValueError('Readback must be an object')
        except Exception as exc:
            state = {}
            self.status = 'Readback unavailable: ' + type(exc).__name__
        lines = ['+' + '-' * 81 + '+']
        for text in ['KEDDEH // SHARED HCI DIAGNOSTICS',
                     *[label + ': ' + str(state.get(key, 'NOT_OBSERVED')) for key, label in (
                         ('active_slot', 'Active slot'), ('epoch', 'Network epoch'),
                         ('quorum', 'Quorum'), ('watchdog', 'Watchdog'),
                         ('mram_saturation', 'MRAM saturation'), ('node_profile', 'Node profile'),
                         ('seed_verification', 'Seed verification'), ('certification', 'Certification'))],
                     *['[ ' + key + ' ] ' + label + (' (UNBOUND)' if self.actions[key] is None else ' (BOUND)')
                       for key, label in (('A', 'Stage A/B update'), ('M', 'Compact MRAM'))],
                     '[ X ] Exit', 'STATUS: ' + self.status]:
            lines.extend(self.rows(text))
        lines.append('+' + '-' * 81 + '+')
        return '\n'.join(lines)

    def process_user_interaction(self, command):
        if type(command) is not str:
            raise TypeError('Command must be text')
        clean = command.strip().upper()
        if not clean:
            return
        if clean == 'X':
            self.running = False
            self.status = 'Session ended'
        elif clean not in self.actions:
            self.status = 'Invalid command; use A, M or X'
        elif self.actions[clean] is None:
            self.status = 'UNBOUND: no operation dispatched'
        else:
            try:
                result = self.actions[clean]()
                # A returned value is not automatically proof of commit or compaction.
                self.status = 'Adapter result: ' + json.dumps(result, ensure_ascii=True, sort_keys=True)
            except Exception as exc:
                # Do not retry: the runtime operation may already have occurred.
                self.status = 'OUTCOME_UNKNOWN: ' + type(exc).__name__ + '; reconcile native receipt'

    def run_interactive_loop(self, read_input=input, write_output=print):
        # Append-only plain text supports redirected output and screen readers.
        while self.running:
            write_output(self.render_accessible_console_layout())
            try:
                self.process_user_interaction(read_input('Action (A / M / X): '))
            except (KeyboardInterrupt, EOFError):
                self.running = False
                self.status = 'Session interrupted; no automatic operation dispatched'
        write_output(self.status)


def native_colony_readback(root):
    """Read actual deployed colony custody; do not convert it into hardware telemetry."""
    from braink_node.owner_vfs.store import VFSStore
    document = json.loads((Path(root) / 'deployment.json').read_text())
    rows = document['instances']
    checked = []
    for row in rows:
        instance = row['instance']
        if not instance.startswith('braink-') or any(c not in '0123456789abcdef' for c in instance[7:]):
            raise ValueError('Invalid native instance identifier')
        directory = Path(root) / 'instances' / instance / 'vfs'
        if not directory.is_dir() or not (directory / 'vfs.sqlite3').is_file():
            raise ValueError('Missing native VFS backing')
        store = VFSStore(directory)
        artifact = store.resolve_path('/definition.json')
        if artifact is None:
            raise ValueError('Missing definition custody')
        definition = store.read_content(artifact.digest)
        observed = json.loads(definition)
        if (artifact.digest != row['steps']['INSTANTIATE_VFS']['digest']
                or observed['definition_sha256'] != row['definition_sha256']
                or observed['id'] != row['definition_id']):
            raise ValueError('Definition differs from deployment manifest')
        if not store.verify_receipt_chain()['verified']:
            raise ValueError('Native receipt chain rejected')
        checked.append(instance)
    return {'node_profile': 'Native VFS definitions and receipt chains read back: ' + str(len(checked))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-automated-audit', action='store_true')
    parser.add_argument('--native-root', type=Path)
    args = parser.parse_args()
    panel = ISOUIDiagnosticsPanel(read_state=(lambda: native_colony_readback(args.native_root)) if args.native_root else None)
    if args.test_automated_audit:
        assert all(len(line) == 83 for line in panel.render_accessible_console_layout().splitlines())
        print('Layout audit passed: 83 ASCII columns; hardware and standards not qualified')
    else:
        panel.run_interactive_loop()


if __name__ == '__main__':
    main()
