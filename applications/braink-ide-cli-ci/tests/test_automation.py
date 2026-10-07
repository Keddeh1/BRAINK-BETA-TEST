import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from braink_node.automation import evolution, reconciliation, recovery
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


if __name__ == '__main__':
    unittest.main()
