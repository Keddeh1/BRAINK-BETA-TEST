import hashlib,json,tempfile,unittest
from pathlib import Path
from model_store import attach_model_store,verify_model_store

class ModelStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.models=self.root/'ollama';self.models.mkdir();(self.models/'blobs').mkdir();self.vault=self.root/'vault'
        data=b'test-only backing, not LLM weights';digest=hashlib.sha256(data).hexdigest();self.blob=self.models/'blobs'/('sha256-'+digest);self.blob.write_bytes(data)
        layer={'digest':'sha256:'+digest,'size':len(data),'mediaType':'application/vnd.ollama.image.model'}
        (self.models/'manifest.json').write_text(json.dumps({'schemaVersion':2,'config':layer,'layers':[layer]}))
    def tearDown(self):self.temp.cleanup()
    def test_reference_custody_deduplicates_shared_blob(self):
        report=attach_model_store(self.vault,self.models,'manifest.json','test-model','native-vault')
        self.assertEqual(len(report['blobs']),1);self.assertEqual(report['unique_backing_bytes'],self.blob.stat().st_size)
        self.assertEqual(verify_model_store(self.vault,'test-model')['inference_qualification'],'NOT_EXECUTED')
    def test_blob_tamper_invalidates_readback(self):
        attach_model_store(self.vault,self.models,'manifest.json','test-model','native-vault');self.blob.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):verify_model_store(self.vault,'test-model')
    def test_incorrect_manifest_never_publishes_complete_custody(self):
        self.blob.write_bytes(b'bad')
        with self.assertRaises(RuntimeError):attach_model_store(self.vault,self.models,'manifest.json','test-model','native-vault')
        with self.assertRaises(ValueError):verify_model_store(self.vault,'test-model')
    def test_manifest_tamper_invalidates_readback(self):
        attach_model_store(self.vault,self.models,'manifest.json','test-model','native-vault');(self.models/'manifest.json').write_text('{}')
        with self.assertRaises(RuntimeError):verify_model_store(self.vault,'test-model')
