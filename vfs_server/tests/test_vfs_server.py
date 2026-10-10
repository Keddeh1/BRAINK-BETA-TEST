import tempfile,unittest
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore,sha256_bytes
from vfs_server.auth import MutationAuthorizer

class VFSServerTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.store=VFSStore(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_actor_and_observer_are_separate(self):
        rec,actor=self.store.write(ArtifactWrite("/runtime/a.txt",b"alpha","test"))
        self.assertEqual(rec.digest,sha256_bytes(b"alpha"))
        self.assertEqual(self.store.read_content(rec.digest),b"alpha")
        self.assertEqual(actor.kind,"VFS_ARTIFACT_WRITE")
        observed=self.store.verify(rec.digest)
        self.assertTrue(observed["verified"])
        self.assertEqual(observed["receipt"]["kind"],"OBSERVER_VFS_READBACK")
        self.assertNotEqual(actor.receipt_digest,observed["receipt"]["receipt_digest"])
    def test_lineage_and_path_resolution(self):
        a,_=self.store.write(ArtifactWrite("/a",b"a","test"))
        b,_=self.store.write(ArtifactWrite("/b",b"b","test",a.digest))
        self.assertEqual(self.store.resolve_path("/b").digest,b.digest)
        self.assertEqual(self.store.lineage(b.digest)[0]["parent_digest"],a.digest)
    def test_receipt_chain_survives_restart(self):
        rec,_=self.store.write(ArtifactWrite("/chain",b"chain","test"))
        self.store.verify(rec.digest)
        reopened=VFSStore(self.tmp.name)
        self.assertTrue(reopened.verify_receipt_chain()["verified"])
    def test_authorizer(self):
        self.assertTrue(MutationAuthorizer().allowed(None))
    def test_unknown_predecessor_fails(self):
        with self.assertRaises(ValueError):
            self.store.write(ArtifactWrite("/x",b"x","test","0"*64))
if __name__=="__main__":unittest.main()
