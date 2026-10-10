"""Read-only HCI over the enrolled ServerSpace runtime; no synthetic consensus."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys

import substrate


def audit_context(frame, architecture, epoch_floor):
    """Parse a complete KEX envelope, without claiming signature or KEX validation.

    target remains opaque: its meaning belongs to the KEX implementation.
    Successful parsing is not admission; web4_admission owns that sequence.
    """
    if type(architecture) is not bytes or len(architecture) != 4:
        raise ValueError('Architecture requires four canonical bytes')
    if type(epoch_floor) is not int or not 0 <= epoch_floor < 2**64:
        raise ValueError('Invalid epoch floor')
    if type(frame) is not bytes or len(frame) != 116:
        raise ValueError('Envelope must contain exactly 116 bytes')
    magic, epoch, arch, length, target = struct.unpack('>4sQ4sI32s', frame[:52])
    if magic != b'KEX!' or arch != architecture:
        raise ValueError('Magic or architecture differs')
    if epoch <= epoch_floor:
        raise ValueError('Replay or downgrade')
    return {'epoch': epoch, 'architecture': arch, 'payload_length': length,
            'target': target, 'signature': frame[52:], 'admitted': False}


def safe_text(value):
    # Prevent runtime strings from injecting ANSI controls or wide glyphs.
    return ''.join(c if 32 <= ord(c) <= 126 else '?' for c in str(value))


def render(frame, width=83):
    width = max(1, min(83, width))
    state = frame['state']
    lines = ['KEDDEH / SERVERSPACE / AUTHENTICATED RUNTIME',
             'Identity: ' + safe_text(state['I']),
             'Origin: ' + safe_text(state.get('O', 'not reported')),
             'Coordinate q: ' + safe_text(state['q']),
             'Time: ' + safe_text(state['t']),
             'Readiness: ' + str(frame['readiness_mask']),
             'State SHA256: ' + frame['state_digest'],
             'CRC32: ' + str(frame['crc32']),
             'Frame bytes: ' + str(frame['frame_bytes']),
             'Transport: Ed25519 / mutual KXA2',
             'Local unity: unassigned; independent contexts retained']
    for name, worker in state['workers'].items():
        lines.append(safe_text(name) + ': PID ' + str(worker['pid']) +
                     ' / ready ' + str(worker['ready']))
    lines.append('[R] Refresh authenticated view | [X] Exit')
    if width < 4:
        return '\n'.join(line[:width].ljust(width) for line in lines)
    inner = width - 4
    def row(line):
        line = safe_text(line)
        if len(line) > inner:
            line = line[:max(0, inner - 3)] + '.' * min(3, inner)
        return '| ' + line.ljust(inner) + ' |'
    return '\n'.join(['+' + '-' * (width - 2) + '+'] +
                     [row(line) for line in lines] +
                     ['+' + '-' * (width - 2) + '+'])


class RuntimePanel:
    def __init__(self, root, identity):
        self.root = Path(root).resolve()
        self.identity = identity
        self.running = True

    def read(self):
        metadata = json.loads((self.root / 'daemon.json').read_text())
        return substrate.handshake(self.root, metadata['pid'], self.identity)

    def dispatch(self, command):
        command = command.strip().upper()
        if command == 'X':
            self.running = False
            return None
        if command == 'R':
            return self.read()
        raise ValueError('Available controls: R / X')

    def run(self):
        while self.running:
            try:
                frame = self.read()
                # One buffered write; no claim of atomicity against other writers.
                sys.stdout.write(render(frame, shutil.get_terminal_size((83, 24)).columns) + '\n')
                sys.stdout.flush()
            except Exception as exc:
                print('Runtime read unavailable: ' + safe_text(exc) + '; retained state is unchanged')
            try:
                # Exactly one dispatch per entered submission, with no mutations.
                self.dispatch(input('R / X: '))
            except (EOFError, KeyboardInterrupt):
                self.running = False
            except ValueError as exc:
                print(safe_text(exc))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    panel = RuntimePanel(args.root, args.identity)
    if args.once:
        print(render(panel.read(), shutil.get_terminal_size((83, 24)).columns))
    else:
        panel.run()


if __name__ == '__main__':
    main()
