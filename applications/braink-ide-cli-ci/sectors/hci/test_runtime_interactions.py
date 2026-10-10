"""Real native VFS/runtime checks; local HTTP provider is a labelled test fixture."""
import concurrent.futures
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'integrations/ollama-vfs/native'))
from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.store import VFSStore
from braink_node.owner_vfs.model import ArtifactWrite
from ollama_node import attach, execute
from kex_diagnostics_panel import ISOUIDiagnosticsPanel, native_colony_readback


class RuntimeInteractionTests(unittest.TestCase):
    def test_rapid_same_identity_dispatches_once_through_native_runtime(self):
        calls = []
        class FixtureHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                body = b'{"models":[]}'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'vfs'
                attach(root, 'test-only-actor', f'http://127.0.0.1:{server.server_port}', 'test-parent', 'test-model-volume')
                def submit(_):
                    panel = ISOUIDiagnosticsPanel(stage_update=lambda: execute(root, 'inventory', request_id='test-shared-identity'))
                    panel.process_user_interaction('A')
                    return panel.status
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                    results = list(pool.map(submit, range(32)))
                self.assertEqual(calls, ['/api/tags'])
                self.assertTrue(all('RETURNED' in result for result in results))
                self.assertTrue(VFSStore(root).verify_receipt_chain()['verified'])
                # Distinct submissions are distinct operations, not silently deduplicated.
                for identity in ('test-distinct-1', 'test-distinct-2'):
                    execute(root, 'inventory', request_id=identity)
                self.assertEqual(len(calls), 3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_layout_during_native_vfs_writes_and_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = 'braink-' + 'a' * 64
            vfs_root = root / 'instances' / instance / 'vfs'
            store = VFSStore(vfs_root)
            definition = {'id': 'test-only-hci-definition', 'definition_sha256': 'test-source-pin'}
            artifact, _ = store.write(ArtifactWrite('/definition.json', canonical_bytes(definition), 'test-only-actor'))
            manifest = {'instances': [{'instance': instance, 'definition_id': definition['id'],
                                      'definition_sha256': definition['definition_sha256'],
                                      'steps': {'INSTANTIATE_VFS': {'digest': artifact.digest}}}]}
            (root / 'deployment.json').write_text(json.dumps(manifest))
            start = threading.Barrier(2)
            def writer():
                writing = VFSStore(vfs_root)
                start.wait(timeout=5)
                for number in range(64):
                    writing.write(ArtifactWrite('/test-only/concurrent.json', canonical_bytes({'number': number}), 'test-only-writer'))
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                writing = pool.submit(writer)
                start.wait(timeout=5)
                panel = ISOUIDiagnosticsPanel(lambda: native_colony_readback(root))
                for _ in range(32):
                    output = panel.render_accessible_console_layout()
                    self.assertTrue(all(len(line) == 83 and line.isascii() for line in output.splitlines()))
                    self.assertNotIn('Readback unavailable', output)
                    self.assertIn('receipt chains read back: 1', output)
                writing.result(timeout=10)
            reopened = VFSStore(vfs_root)
            latest = reopened.resolve_path('/test-only/concurrent.json')
            self.assertEqual(json.loads(reopened.read_content(latest.digest)), {'number': 63})
            self.assertTrue(reopened.verify_receipt_chain()['verified'])

    def test_rapid_serial_commands_stop_after_exit(self):
        calls = []
        panel = ISOUIDiagnosticsPanel(stage_update=lambda: calls.append('A'), compact=lambda: calls.append('M'))
        commands = iter(['A'] * 16 + ['M'] * 16 + ['X', 'A'])
        panel.run_interactive_loop(lambda _: next(commands), lambda _: None)
        self.assertEqual(calls, ['A'] * 16 + ['M'] * 16)
        self.assertEqual(next(commands), 'A')

    def test_fixed_frame_requires_at_least_83_terminal_columns(self):
        lines = ISOUIDiagnosticsPanel().render_accessible_console_layout().splitlines()
        for width, fits in ((40, False), (80, False), (83, True), (120, True)):
            with self.subTest(columns=width):
                self.assertEqual(all(len(line) <= width for line in lines), fits)


if __name__ == '__main__': unittest.main()
