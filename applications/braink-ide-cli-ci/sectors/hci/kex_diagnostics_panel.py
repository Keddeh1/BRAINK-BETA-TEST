"""Dependency-free terminal panel. Hardware operations require native adapters."""
import argparse
import json
import os
import sys
from pathlib import Path
from keddeh_hci_core import terminal_text


class ISOUIDiagnosticsPanel:
    def __init__(self, read_state=None, stage_update=None, compact=None):
        self.read_state = read_state
        self.actions = {'A': stage_update, 'M': compact}
        self.running = True
        self.status = 'No hardware operation executed'

    @staticmethod
    def rows(text, width=83):
        text = terminal_text(text)
        if width < 5:
            return [text[i:i+width] for i in range(0, max(1, len(text)), width)]
        content_width = width - 4
        return ['| ' + text[i:i+content_width].ljust(content_width) + ' |'
                for i in range(0, max(1, len(text)), content_width)]

    def render_accessible_console_layout(self, columns=83):
        if type(columns) is not int or columns < 1:
            raise ValueError('Terminal columns must be a positive integer')
        width = min(83, columns)
        try:
            state = self.read_state() if self.read_state else {}
            if not isinstance(state, dict):
                raise ValueError('Readback must be an object')
        except Exception as exc:
            state = {}
            self.status = 'Readback unavailable: ' + type(exc).__name__
        border = '+' + '-' * (width - 2) + '+' if width >= 5 else '-' * width
        lines = [border]
        for text in ['KEDDEH // SHARED HCI DIAGNOSTICS',
                     *[label + ': ' + str(state.get(key, 'NOT_OBSERVED')) for key, label in (
                         ('active_slot', 'Active slot'), ('epoch', 'Network epoch'),
                         ('quorum', 'Quorum'), ('watchdog', 'Watchdog'),
                         ('mram_saturation', 'MRAM saturation'), ('node_profile', 'Node profile'),
                         ('seed_verification', 'Seed verification'), ('certification', 'Certification'))],
                     *['[ ' + key + ' ] ' + label + (' (UNBOUND)' if self.actions[key] is None else ' (BOUND)')
                       for key, label in (('A', 'Stage A/B update'), ('M', 'Compact MRAM'))],
                     '[ X ] Exit', 'STATUS: ' + self.status]:
            lines.extend(self.rows(text, width))
        if 'observer_state' in state:
            observation = state['observer_state']
            for key in ('I', 'O', 'q', 't', 'operation'):
                if key in observation:
                    lines.extend(self.rows('Observer ' + key + ': ' + str(observation[key]), width))
        lines.append(border)
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

    def run_interactive_loop(self, read_input=input, write_output=print,
                             columns_provider=lambda: 83):
        # One callback per complete frame; this is not a cross-process stdout lock.
        while self.running:
            write_output(self.render_accessible_console_layout(columns_provider()))
            try:
                self.process_user_interaction(read_input('Action (A / M / X): '))
            except (KeyboardInterrupt, EOFError):
                self.running = False
                self.status = 'Session interrupted; no automatic operation dispatched'
        write_output(self.status)


def terminal_columns(stream):
    if not stream.isatty():
        return 83
    try:
        return max(1, os.get_terminal_size(stream.fileno()).columns)
    except OSError:
        return 83


def run_terminal(panel, stream, alternate_screen=False, read_input=input):
    use_alternate = alternate_screen and stream.isatty()
    def write_frame(text):
        # A single Python write avoids line-by-line output, but is not OS atomicity.
        stream.write(('\x1b[H\x1b[2J' if use_alternate else '') + text + '\n')
        stream.flush()
    try:
        if use_alternate:
            stream.write('\x1b[?1049h')
            stream.flush()
        panel.run_interactive_loop(read_input, write_frame, lambda: terminal_columns(stream))
    finally:
        if use_alternate:
            stream.write('\x1b[?1049l')
            stream.flush()


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
    parser.add_argument('--alternate-screen', action='store_true')
    args = parser.parse_args()
    panel = ISOUIDiagnosticsPanel(read_state=(lambda: native_colony_readback(args.native_root)) if args.native_root else None)
    if args.test_automated_audit:
        assert all(len(line) == 83 for line in panel.render_accessible_console_layout().splitlines())
        print('Layout audit passed: 83 ASCII columns; hardware and standards not qualified')
    else:
        run_terminal(panel, sys.stdout, args.alternate_screen)


if __name__ == '__main__':
    main()
