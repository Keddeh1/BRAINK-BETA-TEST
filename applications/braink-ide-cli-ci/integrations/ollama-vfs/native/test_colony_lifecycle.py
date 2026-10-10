"""Native custody tests use labelled fixture definitions, not replacement KEX semantics."""
import json
from pathlib import Path
import tempfile
import unittest
from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore
from braink_node.protocol.catalogue import digest
from colony_lifecycle import checkpoint, inspect_instances, recovery_snapshot


class ColonyLifecycleTests(unittest.TestCase):
    def fixture(self, root):
        definition = {'id': 'colony://test-only/recovery', 'definition_sha256': 'test-only-source', 'variants': []}
        instance = 'braink-' + digest({'definition': definition['definition_sha256'], 'occurrence': [definition['id']]})
        store = VFSStore(root / 'instances' / instance / 'vfs')
        record, _ = store.write(ArtifactWrite('/definition.json', canonical_bytes(definition), instance))
        row = {'instance': instance, 'definition_id': definition['id'], 'definition_sha256': definition['definition_sha256'],
               'occurrence': [definition['id']], 'state': 'READBACK', 'steps': {'INSTANTIATE_VFS': {'digest': record.digest}}}
        deployment = {'catalogue': {'modules': {}, 'families': [], 'variants': [], 'colonies': [definition]}, 'instances': [row]}
        (root / 'deployment.json').write_text(json.dumps(deployment))
        return deployment, store

    def test_snapshot_survives_missing_deployment_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deployment, _ = self.fixture(root)
            result = checkpoint(root)
            (root / 'deployment.json').unlink()
            self.assertEqual(result['state'], 'CHECKPOINT_READBACK')
            self.assertEqual(recovery_snapshot(root)['deployment'], deployment)

    def test_missing_backing_rejected_without_recreation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deployment, store = self.fixture(root)
            store.db_path.unlink()
            with self.assertRaises(FileNotFoundError): inspect_instances(root, deployment)
            self.assertFalse(store.db_path.exists())

    def test_changed_definition_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deployment, store = self.fixture(root)
            store.write(ArtifactWrite('/definition.json', b'{"changed":true}', 'test-only-actor'))
            with self.assertRaises(ValueError): inspect_instances(root, deployment)

    def test_snapshot_bytes_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, store = self.fixture(root)
            result = checkpoint(root)
            target = store._object_path(result['pointer']['snapshot_digest'])
            target.write_bytes(b'{}')
            with self.assertRaises(RuntimeError): recovery_snapshot(root)

if __name__ == '__main__': unittest.main()
