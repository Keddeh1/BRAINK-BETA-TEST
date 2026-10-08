import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from braink_node.automation import evolution, reconciliation, recovery, development, continuity, feedback
from braink_node.protocol.catalogue import compile_catalogue
from braink_node.owner_vfs.store import VFSStore
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.canonical import canonical_bytes
from braink_node.protocol.mesh import MeshStore


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        path = self.root / 'source/sectors/core/src/demo.py'
        path.parent.mkdir(parents=True)
        path.write_text('def work(x): return x+1\n')
        self.source = path
        self.context = SimpleNamespace(root=self.root/'automation', state=self.root/'state', catalogue=lambda: compile_catalogue(self.root/'source'))
        self.context.root.mkdir()
        self.context.state.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_delivery_qualifies_new_git_revision_when_only_supporting_source_changes(self):
        import shutil
        import subprocess
        from braink_node.automation import delivery
        from braink_node.protocol.catalogue import digest

        repository = self.root / 'source'
        scripts = repository / 'scripts/supervise_node.py'
        website = repository / 'integrations/website/development.mjs'
        scripts.parent.mkdir(parents=True)
        website.parent.mkdir(parents=True)
        scripts.write_text('VERSION = 1\n')
        website.write_text('export const version = 1;\n')
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=repository, text=True).strip()
        git('init', '--quiet')
        def commit(message):
            git('add', '.')
            git('-c', 'user.name=BRAINK qualification', '-c', 'user.email=qualification@example.invalid',
                'commit', '--quiet', '-m', message)
            return git('rev-parse', 'HEAD')
        baseline_revision = commit('Original module and supporting source')
        active = self.root / 'active-source'
        shutil.copytree(repository, active, ignore=shutil.ignore_patterns('.git'))
        active_catalogue = compile_catalogue(active)
        submitted = []
        def transport(payload):
            if payload['op'] == 'submit':
                submitted.append(payload)
                return {'job': {'id': payload['id'], 'status': 'queued'}}
            return {'jobs': []}
        self.context.source = active
        self.context.desired_source = repository
        self.context.catalogue = lambda: compile_catalogue(active)
        self.context.config = {'active_revision': baseline_revision}
        self.context.website = transport
        def action(kind, identity, execute):
            key = digest(identity)[:32]
            return {'id': key, 'result': execute(key)}
        self.context.action = action
        for path, content in ((scripts, 'VERSION = 2\n'), (website, 'export const version = 2;\n')):
            with self.subTest(source=str(path.relative_to(repository))):
                path.write_text(content)
                desired_revision = commit('Update supporting source ' + path.name)
                self.assertNotEqual(desired_revision, baseline_revision)
                self.assertEqual(compile_catalogue(repository)['definition_sha256'], active_catalogue['definition_sha256'])
                submitted.clear()
                result = delivery.run(self.context)
                self.assertEqual(result['source_commit'], desired_revision)
                self.assertEqual({row['sector'] for row in submitted}, {'core', 'cli', 'ide', 'ci'})
                self.assertTrue(all(row['parameters']['source_commit'] == desired_revision for row in submitted))

    def test_failed_daily_recovery_retries_on_next_live_cycle(self):
        import time
        from braink_node.automation.engine import AutomationEngine, ORDER
        selected=[]
        class Stop:
            stopped=False
            def is_set(self):return self.stopped
            def wait(self, seconds):self.stopped=True
        engine=AutomationEngine.__new__(AutomationEngine)
        engine.context=SimpleNamespace(flush_evidence=lambda:None,latest=lambda target:{'created':time.time(),'state':'EXECUTION_ERROR' if target=='recovery' else 'OBSERVED'},config={'target_intervals_seconds':{target:86400 for target in ORDER},'cycle_interval_seconds':30})
        engine.run=lambda targets:(selected.extend(targets) or {'completed':True,'results':[]})
        engine.serve(Stop())
        self.assertEqual(selected,['recovery'])

    def test_crlf_source_identity_binds_actual_bytes(self):
        import hashlib
        from braink_node.protocol.binding import FunctionBindings
        self.source.write_bytes(b'def work(x):\r\n    return x+1\r\n')
        catalogue = self.context.catalogue()
        module = next(iter(catalogue['modules']))
        spec = importlib.util.spec_from_file_location('demo', self.source)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        bindings = FunctionBindings(catalogue)
        bindings.bind(module, 'actual', loaded.work)
        self.assertEqual(bindings.invoke(module, [1], context='actual'), 2)
        self.assertEqual(catalogue['modules'][module]['implementation']['source_sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_failed_observations_remain_open_development_work(self):
        self.context.latest = lambda target: {'state': 'EXECUTION_ERROR', 'artifact_digest': target}
        result = development.run(self.context)
        self.assertEqual(result['state'], 'WORK_DERIVED')
        self.assertEqual(len(result['tasks']), 8)
        self.assertTrue(all(row['state'] != 'QUALIFIED' for row in result['tasks']))

    def test_idempotent_subscription_retry_retains_the_failed_service_response(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from braink_node.protocol.transport import JSONTransport
        import threading
        attempts = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                attempts.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                data = b'{"error":"temporarily unavailable"}' if len(attempts) == 1 else b'{"cursor":3}'
                self.send_response(500 if len(attempts) == 1 else 200)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        try:
            transport = JSONTransport('http://127.0.0.1:' + str(server.server_port))
            self.assertEqual(transport.request('/subscriptions', {'subscriber':'actual', 'cursor':3}), {'cursor':3})
            self.assertEqual(attempts[0], attempts[1])
            self.assertEqual(transport.failures[0]['status'], 500)
            self.assertIn('temporarily unavailable', transport.failures[0]['body'])
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_continuity_drains_native_pages_before_advancing_the_subscription(self):
        import base64
        from urllib.parse import urlparse, parse_qs
        from braink_node.protocol.transport import HubSubscription
        hub = VFSStore(self.root / 'hub')
        prefix = '/applications/actual'
        hub.subscribe('instance', prefix, 0)
        for index in range(3):
            hub.write(ArtifactWrite(prefix + '/' + str(index), str(index).encode(), 'instance'))
        class Transport:
            def request(self, path, payload=None):
                if path == '/subscriptions': return hub.subscribe(payload['subscriber'], payload['prefix'], payload['cursor'])
                if path.startswith('/subscriptions/'): return hub.subscription(path.rsplit('/', 1)[1])
                if path.startswith('/events?'): return hub.events(int(parse_qs(urlparse(path).query)['after'][0]), 2)
                if path.startswith('/artifacts/'): return {'content_b64':base64.b64encode(hub.read_content(path.rsplit('/', 1)[1])).decode()}
                raise AssertionError(path)
        directory = self.context.state / 'instances/instance'
        directory.mkdir(parents=True)
        (directory / 'ceremony.json').write_text(json.dumps({'steps':{'SUBSCRIBE_VFS':{'prefix':prefix}}}))
        self.context.hub_transport = Transport()
        self.context.hub = HubSubscription(self.context.hub_transport)
        self.context.deployment = lambda: {'instances':[{'instance':'instance'}]}
        result = continuity.run(self.context)
        self.assertEqual(result['state'], 'CONTINUOUS')
        self.assertEqual(result['mirrored_artifacts'], 3)
        self.assertEqual(hub.subscription('instance')['cursor'], 3)
        self.assertEqual(continuity.run(self.context)['mirrored_artifacts'], 0)

    def test_feedback_calibration_is_serializable_and_reaches_the_mesh_inbox(self):
        from braink_node.protocol.catalogue import digest
        lexical = self.root / 'owner/lexical_compiler.py'
        lexical.parent.mkdir()
        lexical.write_text('def observer_calibrate(subject, state, observer, context=None): return {"subject":subject,"context":context}\n')
        store = MeshStore(self.root / 'feedback-mesh', {'state':{'schema':'braink.il-llm.canonical-state.v1','rows':[]}})
        for identity in ('a', 'b'): store.subscribe({'instance':identity,'definition_sha256':identity})
        class Transport:
            def request(self, path, payload):
                if path == '/exchange':return store.exchange(payload['sender'], payload['recipient'], payload['row'], payload['message_id'])
                return store.inbox(payload['instance'], payload['after'])
        self.context.config = {'owner_export':str(lexical.parent / 'capability_broker.py')}
        self.context.deployment = lambda:{'instances':[{'instance':'a'},{'instance':'b'}]}
        self.context.latest = lambda target:{'target':target,'state':'OBSERVED','artifact_digest':target}
        self.context.mesh = Transport()
        self.context.action = lambda kind, identity, execute:{'result':execute(digest(identity))}
        result = feedback.run(self.context)
        canonical_bytes(result)
        self.assertEqual(result['state'], 'DELIVERED')
        self.assertEqual(len(store.inbox('b')), 1)
        self.assertEqual(store.inbox('b')[0]['document']['row']['relation']['calibration']['subject'], 'a')

    def test_evolution_closes_over_dependent_sectors(self):
        first = evolution.run(self.context)
        self.assertEqual(set(first['affected_sectors']), {'core','cli','ide','ci'})
        self.assertEqual(evolution.run(self.context)['state'], 'UNCHANGED')
        self.source.write_text('def work(x): return x+2\n')
        changed = evolution.run(self.context)
        self.assertEqual(len(changed['changed_modules']), 1)
        self.assertEqual(len(changed['affected_colonies']), 4)

    def test_expected_instance_occurrences_are_independent(self):
        expected = reconciliation.expected_instances(self.context.catalogue())
        function_instances = [row for row in expected.values() if row['definition_id'].startswith('function:')]
        self.assertEqual(len(function_instances), 4)
        self.assertEqual(len({row['instance'] for row in function_instances}), 4)

    def test_checkpoint_restores_and_rejects_tampering(self):
        directory = self.context.state/'instances/example'
        store = VFSStore(directory/'vfs')
        definition = {'id':'function://example','definition_sha256':'source'}
        artifact, actor = store.write(ArtifactWrite('/definition.json', canonical_bytes(definition), 'example'))
        state = {'instance':'example','steps':{'INSTANTIATE_VFS':{'root':str(directory/'vfs'),'digest':artifact.digest}}}
        (directory/'ceremony.json').write_text(json.dumps(state))
        snapshot = recovery.checkpoint(self.context)
        restored = recovery.restore(snapshot, self.root/'clean-runtime')
        self.assertEqual(restored['verified_instance_stores'], 1)
        restored_state = json.loads((self.root/'clean-runtime/instances/example/ceremony.json').read_text())
        self.assertIn('clean-runtime', restored_state['steps']['INSTANTIATE_VFS']['root'])
        (snapshot/'instances/example/ceremony.json').write_text('tampered')
        with self.assertRaises(ValueError):
            recovery.restore(snapshot, self.root/'must-not-restore')
        self.assertFalse((self.root/'must-not-restore').exists())

    def test_mesh_wire_replay_is_idempotent(self):
        store = MeshStore(self.root/'mesh', {'state':{'schema':'braink.il-llm.canonical-state.v1','rows':[]}})
        for identity in ('a','b'):
            store.subscribe({'instance':identity,'definition_sha256':identity})
        anchor = {'type':'RELATIONAL_ANCHOR','source':'a','definition':'exact','relation':'member','uncertainty':[],'contradiction':[],'next_route':'b'}
        first = store.exchange('a','b',anchor,'message-one')
        second = store.exchange('a','b',anchor,'message-one')
        self.assertEqual(first['sequence'], second['sequence'])
        self.assertEqual(len(store.inbox('b')), 1)
        with self.assertRaises(ValueError):
            store.exchange('a','b',{**anchor,'definition':'changed'},'message-one')


class SupervisorActivationTests(unittest.TestCase):
    def setUp(self):
        import venv
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        venv.EnvBuilder(with_pip=True).create(self.root / 'venv')
        old = self.root / 'venv/bin/braink-node'
        old.write_text('#!' + str(self.root / 'venv/bin/python') + '\nprint("previous")\n')
        old.chmod(0o755)
        self.config = self.root / 'automation.json'
        self.config.write_text(json.dumps({'source':'previous','active_revision':'previous'}))
        spec = importlib.util.spec_from_file_location('braink_supervisor_qualification', Path(__file__).resolve().parents[1] / 'scripts/supervise_node.py')
        self.supervisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.supervisor)

    def activation(self, revision):
        import hashlib
        import zipfile
        release = self.root / 'releases' / revision
        release.mkdir(parents=True)
        wheel = release / 'braink_activation_fixture-1.0-py3-none-any.whl'
        files = {'activation_fixture.py':'def main(): print(' + repr(revision) + ')\n',
                 'braink_activation_fixture-1.0.dist-info/METADATA':'Metadata-Version: 2.1\nName: braink-activation-fixture\nVersion: 1.0\n',
                 'braink_activation_fixture-1.0.dist-info/WHEEL':'Wheel-Version: 1.0\nGenerator: qualification\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
                 'braink_activation_fixture-1.0.dist-info/entry_points.txt':'[console_scripts]\nbraink-node = activation_fixture:main\n'}
        files['braink_activation_fixture-1.0.dist-info/RECORD'] = ''.join(name + ',,\n' for name in files)
        with zipfile.ZipFile(wheel, 'w') as archive:
            for name, body in files.items():archive.writestr(name, body)
        return {'source_commit':revision,'qualified_source':str(release / 'source'),
                'wheels':[{'path':str(wheel),'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()}]}

    def console(self, path):
        import subprocess
        return subprocess.check_output([str(path / 'bin/braink-node'), '--help'], text=True).strip()

    def test_real_console_survives_first_and_subsequent_environment_selection(self):
        first_revision, second_revision = 'a' * 40, 'b' * 40
        first = self.supervisor.activate_environment(self.root, self.activation(first_revision), self.config)
        stable = Path(first['environment'])
        self.assertTrue((self.root / 'venv').is_symlink())
        self.assertEqual(self.console(self.root / 'venv'), first_revision)
        self.assertIn(str(stable / 'bin/python'), (stable / 'bin/braink-node').read_text())
        second = self.supervisor.activate_environment(self.root, self.activation(second_revision), self.config)
        self.assertNotEqual(first['environment'], second['environment'])
        self.assertEqual(self.console(self.root / 'venv'), second_revision)
        self.assertEqual(self.console(stable), first_revision)
        self.assertEqual(json.loads(self.config.read_text())['active_revision'], second_revision)

    def test_failed_configuration_commit_restores_actual_previous_console(self):
        from unittest.mock import patch
        original = self.config.read_bytes()
        replace = Path.replace
        def fail_configuration(path, target):
            if Path(target) == self.config:raise OSError('qualification failure committing config')
            return replace(path, target)
        with patch.object(Path, 'replace', fail_configuration):
            with self.assertRaises(OSError):
                self.supervisor.activate_environment(self.root, self.activation('rejected'), self.config)
        self.assertFalse((self.root / 'venv').is_symlink())
        self.assertEqual(self.console(self.root / 'venv'), 'previous')
        self.assertEqual(self.config.read_bytes(), original)
        self.supervisor.activate_environment(self.root, self.activation('accepted'), self.config)
        selected = self.config.read_bytes()
        with patch.object(Path, 'replace', fail_configuration):
            with self.assertRaises(OSError):
                self.supervisor.activate_environment(self.root, self.activation('rejected-again'), self.config)
        self.assertTrue((self.root / 'venv').is_symlink())
        self.assertEqual(self.console(self.root / 'venv'), 'accepted')
        self.assertEqual(self.config.read_bytes(), selected)


if __name__ == '__main__':
    unittest.main()
