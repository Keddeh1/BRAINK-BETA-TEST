import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore, BindingConflict

class BindingHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=VFSStore(self.root)
    def tearDown(self): self.tmp.cleanup()
    def request(self, content=b'one', source='source://one', continuation='undertaking-1', expected=0):
        return ArtifactWrite('/context',content,source,media_type='text/plain',continuation_id=continuation,expected_version=expected)
    def test_context_versions_shared_bytes(self):
        self.store.write(self.request())
        self.store.write(self.request(source='source://two',continuation='undertaking-2',expected=1))
        history=self.store.binding_history('/context')
        self.assertEqual([x['version'] for x in history],[1,2])
        self.assertEqual([x['artifact']['source'] for x in history],['source://one','source://two'])
        self.assertEqual(history[0]['artifact']['digest'],history[1]['artifact']['digest'])
        self.assertEqual(history[1]['previous_binding_digest'],history[0]['binding_digest'])
    def test_retry_after_later_version_returns_original(self):
        first=self.store.write(self.request())
        self.store.write(self.request(b'two','source://two','undertaking-2',1))
        self.assertEqual(VFSStore(self.root).write(self.request()),first)
        self.assertEqual(len(self.store.binding_history('/context')),2)
        self.assertEqual(self.store.verify_receipt_chain()['count'],2)
        self.assertEqual(self.store.resolve_path('/context').source,'source://two')
    def test_changed_continuation_request_conflicts(self):
        self.store.write(self.request())
        with self.assertRaises(BindingConflict):self.store.write(self.request(source='source://changed'))
        self.assertEqual(len(self.store.binding_history('/context')),1)
    def test_stale_failover_rejected(self):
        self.store.write(self.request())
        with self.assertRaises(BindingConflict):VFSStore(self.root).write(self.request(b'two',continuation='replacement'))
        self.assertEqual(self.store.verify_receipt_chain()['count'],1)
    def test_concurrent_retry_one_receipt(self):
        def invoke(_): return VFSStore(self.root).write(self.request())
        with ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(invoke,range(16)))
        self.assertTrue(all(x==results[0] for x in results))
        self.assertEqual(self.store.verify_receipt_chain()['count'],1)
    def test_concurrent_failover_writers_one_version(self):
        def invoke(i):
            try:return VFSStore(self.root).write(self.request(continuation='worker-'+str(i)))
            except BindingConflict:return None
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(invoke,range(8)))
        self.assertEqual(sum(x is not None for x in results),1)
    def test_receipt_failure_rolls_back_continuation(self):
        with patch.object(self.store,'_receipt',side_effect=OSError('storage')):
            with self.assertRaises(OSError):self.store.write(self.request())
        self.assertEqual(self.store.binding_history('/context'),[])
        self.assertEqual(self.store.write(self.request())[1].detail['binding_version'],1)
    def test_process_exit_before_commit_retry(self):
        code="""import os,sys
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
s=VFSStore(sys.argv[1]);s._receipt=lambda *args:os._exit(73)
s.write(ArtifactWrite('/context',b'one','source://one',media_type='text/plain',continuation_id='undertaking-1',expected_version=0))
"""
        self.assertEqual(subprocess.run([sys.executable,'-c',code,str(self.root)],timeout=10).returncode,73)
        reopened=VFSStore(self.root)
        self.assertEqual(reopened.binding_history('/context'),[])
        reopened.write(self.request())
        self.assertEqual(reopened.verify_receipt_chain()['count'],1)
    def test_process_exit_after_commit_retry(self):
        code="""import os,sys
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
VFSStore(sys.argv[1]).write(ArtifactWrite('/context',b'one','source://one',media_type='text/plain',continuation_id='undertaking-1',expected_version=0));os._exit(74)
"""
        self.assertEqual(subprocess.run([sys.executable,'-c',code,str(self.root)],timeout=10).returncode,74)
        self.store.write(self.request())
        self.assertEqual(self.store.verify_receipt_chain()['count'],1)
    def test_history_tamper_rejected(self):
        self.store.write(self.request())
        with self.store._connect() as db:db.execute("UPDATE binding_history SET binding_json='{}'")
        with self.assertRaises(RuntimeError):self.store.binding_history('/context')
        with self.assertRaises(RuntimeError):self.store.write(self.request())
    def test_rehashed_history_still_rejected_by_receipt(self):
        from vfs_server.store import canonical_json, sha256_bytes
        self.store.write(self.request())
        with self.store._connect() as db:
            row=db.execute('SELECT * FROM binding_history').fetchone()
            body=json.loads(row['binding_json']);body['artifact']['source']='forged'
            raw=canonical_json(body)
            db.execute('UPDATE binding_history SET binding_json=?,binding_digest=?',(raw.decode(),sha256_bytes(raw)))
        with self.assertRaises(RuntimeError):self.store.binding_history('/context')
    def test_continuation_mapping_tamper_rejected(self):
        self.store.write(self.request())
        self.store.write(self.request(b'two','source://two','undertaking-2',1))
        with self.store._connect() as db:db.execute("UPDATE continuations SET version=2 WHERE continuation_id='undertaking-1'")
        with self.assertRaises(RuntimeError):self.store.write(self.request())
    def test_retry_corrupt_carrier_rejected(self):
        record,_=self.store.write(self.request());self.store._object_path(record.digest).write_bytes(b'corrupt')
        with self.assertRaises(RuntimeError):self.store.write(self.request())
    def test_backup_failover_retains_versions_and_retry(self):
        from vfs_server.backup import create_backup
        first=self.store.write(self.request())
        self.store.write(self.request(b'two','source://two','undertaking-2',1))
        archive=create_backup(self.root,self.root/'snapshot.tar.gz')
        destination=self.root/'restored';destination.mkdir()
        with tarfile.open(archive) as tar:tar.extractall(destination,filter='data')
        restored=VFSStore(destination)
        self.assertEqual(restored.write(self.request()),first)
        self.assertEqual(restored.binding_history('/context'),self.store.binding_history('/context'))
        self.assertEqual(restored.verify_receipt_chain()['count'],2)
    def test_legacy_snapshot_migration_is_explicit_and_repeatable(self):
        self.store.write(self.request())
        with self.store._connect() as db:
            db.execute('DROP TABLE binding_history');db.execute('DROP TABLE continuations')
        history=VFSStore(self.root).binding_history('/context')
        self.assertEqual(history[0]['origin'],'LEGACY_CURRENT_SNAPSHOT')
        self.assertIsNone(history[0]['receipt_id'])
        self.assertEqual(VFSStore(self.root).binding_history('/context'),history)
    def test_independent_process_retries_share_one_durable_receipt(self):
        code = """import json,sys
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
record,receipt=VFSStore(sys.argv[1]).write(ArtifactWrite('/context',b'one','source://one',media_type='text/plain',continuation_id='undertaking-1',expected_version=0))
print(json.dumps({'artifact':record.as_dict(),'receipt':receipt.as_dict()},sort_keys=True))
"""
        workers=[subprocess.Popen([sys.executable,'-c',code,str(self.root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(8)]
        outputs=[]
        for worker in workers:
            stdout,stderr=worker.communicate(timeout=15)
            self.assertEqual(worker.returncode,0,stderr)
            outputs.append(json.loads(stdout))
        self.assertTrue(all(value==outputs[0] for value in outputs))
        reopened=VFSStore(self.root)
        self.assertEqual(reopened.verify_receipt_chain()['count'],1)
        self.assertEqual(len(reopened.binding_history('/context')),1)

    def test_replacement_process_retry_preserves_later_current_binding(self):
        first=self.store.write(self.request())
        self.store.write(self.request(b'two','source://two','undertaking-2',1))
        code="""import json,sys
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
s=VFSStore(sys.argv[1]);record,receipt=s.write(ArtifactWrite('/context',b'one','source://one',media_type='text/plain',continuation_id='undertaking-1',expected_version=0))
print(json.dumps({'record':record.as_dict(),'receipt':receipt.as_dict(),'current_source':s.resolve_path('/context').source,'receipt_count':s.verify_receipt_chain()['count']}))
"""
        worker=subprocess.run([sys.executable,'-c',code,str(self.root)],capture_output=True,text=True,timeout=15)
        self.assertEqual(worker.returncode,0,worker.stderr)
        result=json.loads(worker.stdout)
        self.assertEqual(result['record'],first[0].as_dict())
        self.assertEqual(result['receipt'],first[1].as_dict())
        self.assertEqual(result['current_source'],'source://two')
        self.assertEqual(result['receipt_count'],2)

    def test_invalid_version_and_continuation_rejected(self):
        for request in [self.request(expected=True),self.request(expected=-1),self.request(continuation='')]:
            with self.assertRaises(ValueError): self.store.write(request)
        self.assertEqual(self.store.status()['receipts'],0)

if __name__=='__main__':unittest.main()
