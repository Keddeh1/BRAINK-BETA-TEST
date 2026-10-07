import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError

from braink_node.protocol.catalogue import compile_catalogue
from braink_node.protocol.binding import FunctionBindings
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.mesh import MeshStore, mesh_server
from braink_node.protocol.transport import JSONTransport
from braink_node.owner_vfs.store import VFSStore


class Hub:
    def __init__(self, root):
        self.store = VFSStore(root)
        self.fail = False

    def subscribe(self, instance, prefix):
        if self.fail:
            raise RuntimeError('transport unavailable')
        return self.store.subscribe(instance, prefix)

    def publish(self, instance, path, document):
        from braink_node.owner_vfs.model import ArtifactWrite
        from braink_node.canonical import canonical_bytes
        artifact, actor = self.store.write(ArtifactWrite(path, canonical_bytes(document), instance))
        return {'actor': actor.as_dict(), 'observer': self.store.verify(artifact.digest)}


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = {'state': {'schema': 'braink.il-llm.canonical-state.v1', 'rows': []}, 'source_sha256': 'source', 'state_sha256': 'state'}
        self.mesh = MeshStore(self.root / 'mesh', self.state)
        self.server = mesh_server(self.mesh, '127.0.0.1', 0, 'owner-credential')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.transport = JSONTransport('http://127.0.0.1:' + str(self.server.server_port), 'owner-credential')
        self.hub = Hub(self.root / 'hub')
        self.manager = InstanceManager(self.root / 'instances', self.hub, self.transport)
        self.definition = {'id': 'function://test/f', 'definition_sha256': 'abc', 'modules': []}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temporary.cleanup()

    def test_isolation_resume_and_readback(self):
        first = self.manager.instantiate(self.definition, ['colony-one'])
        second = self.manager.instantiate(self.definition, ['colony-two'])
        self.assertNotEqual(first['instance'], second['instance'])
        self.assertNotEqual(first['steps']['INSTANTIATE_VFS']['root'], second['steps']['INSTANTIATE_VFS']['root'])
        self.assertEqual(first['state'], 'READBACK')
        resumed = self.manager.instantiate(self.definition, ['colony-one'])
        self.assertEqual(first['instance'], resumed['instance'])
        self.assertEqual(first['steps']['INSTANTIATE_VFS'], resumed['steps']['INSTANTIATE_VFS'])
        reopened = MeshStore(self.root / 'mesh', self.state)
        self.assertEqual(reopened.subscription(first['instance'])['definition_sha256'], 'abc')

    def test_failure_never_completes_and_resumes(self):
        self.hub.fail = True
        with self.assertRaises(RuntimeError):
            self.manager.instantiate(self.definition, ['failure'])
        record = next((self.root / 'instances').glob('*/ceremony.json'))
        self.assertEqual(json.loads(record.read_text())['state'], 'INSTANTIATE_VFS')
        self.hub.fail = False
        self.assertEqual(self.manager.instantiate(self.definition, ['failure'])['state'], 'READBACK')

    def test_mesh_rejects_changed_identity_and_bad_auth(self):
        self.mesh.subscribe({'instance': 'a', 'definition_sha256': 'one'})
        with self.assertRaises(ValueError):
            self.mesh.subscribe({'instance': 'a', 'definition_sha256': 'two'})
        with self.assertRaises(HTTPError) as caught:
            JSONTransport(self.transport.endpoint, 'incorrect').request('/subscription', {'instance': 'a'})
        self.assertEqual(caught.exception.code, 401)

    def test_actual_network_exchange_and_restart(self):
        for instance in ('a', 'b'):
            self.transport.request('/subscribe', {'instance': instance, 'definition_sha256': instance})
        row = {'type': 'RELATIONAL_ANCHOR', 'source': 'function://test/f', 'definition': 'exact-source',
               'relation': 'member-of', 'uncertainty': [], 'contradiction': [], 'next_route': 'family://test'}
        receipt = self.transport.request('/exchange', {'sender': 'a', 'recipient': 'b', 'row': row})
        inbox = self.transport.request('/inbox', {'instance': 'b'})
        self.assertEqual(inbox[0]['document']['row'], row)
        self.assertEqual(inbox[0]['digest'], receipt['digest'])
        self.assertEqual(MeshStore(self.root / 'mesh', self.state).inbox('b'), inbox)
        with self.assertRaises(HTTPError):
            self.transport.request('/exchange', {'sender': 'unknown', 'recipient': 'b', 'row': row})

    def test_live_context_binding_preserves_closure_and_receiver(self):
        import importlib.util
        source = self.root / 'binding-source'
        path = source / 'sectors/core/src/live.py'
        path.parent.mkdir(parents=True)
        path.write_text('def factory(x):\n    def inner(y): return x+y\n    return inner\nclass C:\n    def __init__(self, x): self.x=x\n    def method(self, y): return self.x+y\nleft=lambda x:x+1; right=lambda x:x+2\n')
        spec = importlib.util.spec_from_file_location('live', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        catalogue = compile_catalogue(source)
        bindings = FunctionBindings(catalogue)
        closure = 'function://braink-development/live/factory.inner'
        bindings.bind(closure, 'first', module.factory(10))
        bindings.bind(closure, 'second', module.factory(20))
        self.assertEqual(bindings.invoke(closure, [2], context='first'), 12)
        self.assertEqual(bindings.invoke(closure, [2], context='second'), 22)
        declared = self.manager.instantiate(catalogue['modules'][closure], ['closure-instance'])
        self.assertEqual(self.manager.invoke(declared['instance'], bindings, [5], context='second'), 25)
        instance_vfs = VFSStore(Path(declared['steps']['INSTANTIATE_VFS']['root']))
        self.assertTrue(instance_vfs.verify_receipt_chain()['verified'])
        with self.assertRaises(TypeError):
            self.manager.invoke(declared['instance'], bindings, [], context='second')
        self.assertTrue(instance_vfs.verify_receipt_chain()['verified'])
        method = 'function://braink-development/live/C.method'
        bindings.bind(method, 'receiver', module.C(30).method)
        self.assertEqual(bindings.invoke(method, [3], context='receiver'), 33)
        lambdas = [key for key in catalogue['modules'] if 'lambda@' in key]
        bindings.bind(lambdas[0], 'left', module.left)
        bindings.bind(lambdas[1], 'right', module.right)
        self.assertEqual(bindings.invoke(lambdas[0], [1], context='left'), 2)
        with self.assertRaises(ValueError):
            bindings.bind(lambdas[0], 'wrong', module.right)

    def test_catalogue_packages_context_and_composition(self):
        source = self.root / 'source'
        path = source / 'sectors/core/src/demo.py'
        path.parent.mkdir(parents=True)
        path.write_text('def factory(x):\n    def inner(y):\n        return x+y\n    return inner\nclass C:\n    def method(self): return 1\n')
        catalogue = compile_catalogue(source)
        self.assertEqual(len(catalogue['modules']), 3)
        closure = catalogue['modules']['function://braink-development/demo/factory.inner']
        self.assertEqual(closure['binding']['kind'], 'closure')
        bindings = FunctionBindings(catalogue)
        with self.assertRaises(ValueError):
            bindings.resolve(closure['id'])
        self.assertEqual(len(catalogue['variants']), 4)
        self.assertIn(closure['id'], catalogue['variants'][1]['modules'])
        self.assertEqual(catalogue, compile_catalogue(source))


if __name__ == '__main__':
    unittest.main()
