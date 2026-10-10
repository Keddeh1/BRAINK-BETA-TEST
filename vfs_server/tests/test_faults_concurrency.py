import tempfile,unittest,subprocess,sys,json,tarfile,hashlib,sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
class FaultConcurrencyTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=VFSStore(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_reused_carrier_keeps_binding_context(self):
  parent,_=self.store.write(ArtifactWrite('/parent',b'parent','fixture://parent'))
  first,_=self.store.write(ArtifactWrite('/a',b'same','fixture://a'))
  second,_=self.store.write(ArtifactWrite('/b',b'same','fixture://b',parent.digest,'text/plain'))
  self.assertEqual(first.digest,second.digest);self.assertEqual(second.path,'/b')
  reopened=VFSStore(self.root)
  self.assertEqual(reopened.resolve_path('/a').source,'fixture://a')
  b=reopened.resolve_path('/b');self.assertEqual((b.source,b.predecessor,b.media_type),('fixture://b',parent.digest,'text/plain'))
 def test_concurrent_shared_carrier_receipts(self):
  def write(i):return self.store.write(ArtifactWrite('/'+str(i),b'shared','fixture://'+str(i)))
  with ThreadPoolExecutor(max_workers=8) as pool:records=list(pool.map(write,range(32)))
  self.assertEqual(len({r[0].digest for r in records}),1)
  self.assertEqual(self.store.status()['paths'],32)
  for i in range(32):self.assertEqual(self.store.resolve_path('/'+str(i)).source,'fixture://'+str(i))
  self.assertEqual(self.store.verify_receipt_chain()['count'],32);self.assertTrue(self.store.verify_receipt_chain()['verified'])
 def test_receipt_failure_rolls_back_binding(self):
  initial,_=self.store.write(ArtifactWrite('/a',b'old','fixture://old'));before=self.store.status()
  with patch.object(self.store,'_receipt',side_effect=OSError('injected')):
   with self.assertRaises(OSError):self.store.write(ArtifactWrite('/a',b'new','fixture://new'))
  self.assertEqual(self.store.resolve_path('/a'),initial);self.assertEqual(self.store.status(),before)
  self.assertTrue(self.store.verify_receipt_chain()['verified'])
 def test_replace_failure_never_admits_artifact(self):
  with patch('vfs_server.store.os.replace',side_effect=OSError('injected')):
   with self.assertRaises(OSError):self.store.write(ArtifactWrite('/a',b'new','fixture://new'))
  self.assertIsNone(self.store.resolve_path('/a'));self.assertEqual(self.store.status()['artifacts'],0)
  self.assertEqual(list(self.root.rglob('.write-*')),[])
 def test_committed_corruption_and_receipt_tamper(self):
  rec,_=self.store.write(ArtifactWrite('/a',b'original','fixture://a'))
  self.store._object_path(rec.digest).write_bytes(b'corrupt')
  with self.assertRaises(RuntimeError):self.store.read_content(rec.digest)
  with self.store._connect() as db:db.execute("UPDATE receipts SET detail_json='{}'")
  self.assertFalse(self.store.verify_receipt_chain()['verified'])
 def test_invalid_predecessor_does_not_publish_binding(self):
  with self.assertRaises(ValueError):self.store.write(ArtifactWrite('/a',b'body','fixture://a','../bad'))
  self.assertIsNone(self.store.resolve_path('/a'))

 def test_process_exit_rolls_back_uncommitted_binding(self):
  code="""import os,sys
from vfs_server.store import VFSStore
from vfs_server.model import ArtifactWrite
s=VFSStore(sys.argv[1])
s._receipt=lambda *args:os._exit(73)
s.write(ArtifactWrite('/crash',b'pending','fixture://crash'))
"""
  result=subprocess.run([sys.executable,'-c',code,str(self.root)],timeout=10)
  self.assertEqual(result.returncode,73)
  reopened=VFSStore(self.root);self.assertIsNone(reopened.resolve_path('/crash'))
  self.assertEqual(reopened.status()['artifacts'],0);self.assertTrue(reopened.verify_receipt_chain()['verified'])
  # Uncommitted immutable bytes may survive, but are not an admitted binding.
  reopened.write(ArtifactWrite('/crash',b'pending','fixture://retry'))
  self.assertEqual(reopened.resolve_path('/crash').source,'fixture://retry')

 def test_backup_committed_snapshot_excludes_orphan_and_verifies(self):
  from vfs_server.backup import create_backup
  rec,_=self.store.write(ArtifactWrite('/held',b'held','fixture://held'))
  with patch.object(self.store,'_receipt',side_effect=OSError('injected')):
   with self.assertRaises(OSError):self.store.write(ArtifactWrite('/orphan',b'orphan','fixture://orphan'))
  backup=create_backup(self.root,self.root/'snapshot.tar.gz')
  with tarfile.open(backup) as tar:
   manifest=json.load(tar.extractfile('backup-manifest.json'))
   self.assertEqual(len(manifest['objects']),1)
   for obj in manifest['objects']:
    self.assertEqual(hashlib.sha256(tar.extractfile(obj['path']).read()).hexdigest(),obj['sha256'])
   self.assertEqual(hashlib.sha256(tar.extractfile('vfs.sqlite3').read()).hexdigest(),manifest['database_sha256'])

 def test_backup_failure_retains_existing_output(self):
  from vfs_server.backup import create_backup
  rec,_=self.store.write(ArtifactWrite('/held',b'held','fixture://held'))
  output=self.root/'snapshot.tar.gz';output.write_bytes(b'prior')
  self.store._object_path(rec.digest).write_bytes(b'bad')
  with self.assertRaises(ValueError):create_backup(self.root,output)
  self.assertEqual(output.read_bytes(),b'prior')

 def test_backup_snapshot_while_later_writes_commit(self):
  from vfs_server.backup import create_backup
  import shutil
  from threading import Event
  self.store.write(ArtifactWrite('/baseline',b'baseline','fixture://baseline'))
  gate=Event();original=shutil.copyfile
  def writer():
   if not gate.wait(5):raise RuntimeError('snapshot staging did not begin')
   for i in range(16):self.store.write(ArtifactWrite('/later/'+str(i),str(i).encode(),'fixture://later'))
  with ThreadPoolExecutor(max_workers=1) as pool:
   future=pool.submit(writer)
   def staged_copy(src,dst):
    gate.set();future.result(timeout=10);return original(src,dst)
   with patch('vfs_server.backup.shutil.copyfile',side_effect=staged_copy):
    output=create_backup(self.root,self.root/'concurrent.tar.gz')
  self.assertEqual(self.store.status()['artifacts'],17)
  with tarfile.open(output) as tar:
   manifest=json.load(tar.extractfile('backup-manifest.json'));self.assertEqual(len(manifest['objects']),1)
   restored=self.root/'restored.sqlite';restored.write_bytes(tar.extractfile('vfs.sqlite3').read())
   with sqlite3.connect(restored) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0],1)
