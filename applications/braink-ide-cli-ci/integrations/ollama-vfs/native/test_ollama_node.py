import json
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO
from pathlib import Path
import ollama_node
from braink_node.owner_vfs.store import VFSStore

class NativeActorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        ollama_node.attach(self.root,'native-actor','http://127.0.0.1:11434',
            'volume://keddeh/braink/root','volume://keddeh/braink/models')
    def tearDown(self):
        self.temp.cleanup()
    def test_binding_survives_store_reopen(self):
        self.assertEqual(ollama_node.binding(self.root)['actor'],'native-actor')
        self.assertTrue(VFSStore(self.root).verify_receipt_chain()['verified'])
    def test_transport_failure_preserves_receipt_and_actor(self):
        with patch.object(ollama_node,'urlopen',side_effect=ConnectionError('closed')):
            result=ollama_node.execute(self.root,'chat',{'model':'resident','messages':[]})
        self.assertEqual(result['state'],'OUTCOME_UNKNOWN')
        self.assertEqual(result['actor'],'native-actor')
        retained=json.loads(VFSStore(self.root).read_content(result['receipt']['digest']))
        self.assertTrue(retained['request_digest'])
        self.assertTrue(VFSStore(self.root).verify_receipt_chain()['verified'])
    def test_incomplete_response_is_not_completed_inference(self):
        with patch.object(ollama_node,'urlopen',return_value=BytesIO(b'{"done":false,"message":{"content":"partial"}}')):
            result=ollama_node.execute(self.root,'chat',{'model':'resident','messages':[]})
        self.assertEqual(result['state'],'OUTCOME_UNKNOWN')
    def test_dispatch_requires_retained_binding(self):
        with tempfile.TemporaryDirectory() as absent:
            with patch.object(ollama_node,'urlopen') as transport:
                with self.assertRaises(ValueError):ollama_node.execute(absent,'inventory')
                transport.assert_not_called()

    def test_same_execution_replays_without_second_dispatch(self):
        with patch.object(ollama_node,'urlopen',return_value=BytesIO(b'{"models":[]}')) as transport:
            first=ollama_node.execute(self.root,'inventory',request_id='retained')
            replay=ollama_node.execute(self.root,'inventory',request_id='retained')
        self.assertEqual(transport.call_count,1)
        self.assertEqual(first['receipt']['digest'],replay['receipt']['digest'])
        self.assertTrue(replay['replayed'])
    def test_uncertain_execution_is_not_automatically_retried(self):
        with patch.object(ollama_node,'urlopen',side_effect=ConnectionError('closed')) as transport:
            ollama_node.execute(self.root,'chat',{'model':'resident'},request_id='uncertain')
            replay=ollama_node.execute(self.root,'chat',{'model':'resident'},request_id='uncertain')
        self.assertEqual(transport.call_count,1)
        self.assertEqual(replay['state'],'OUTCOME_UNKNOWN')
    def test_execution_identity_cannot_change_payload(self):
        with patch.object(ollama_node,'urlopen',side_effect=ConnectionError('closed')):
            ollama_node.execute(self.root,'chat',{'model':'one'},request_id='same')
            with self.assertRaises(ValueError):
                ollama_node.execute(self.root,'chat',{'model':'two'},request_id='same')
    def test_nested_volume_resolves_backed_child_without_copying_objects(self):
        with tempfile.TemporaryDirectory() as child:
            ollama_node.retain(child,'/definition.json',{'volume':'models'},'model-volume')
            retained=ollama_node.mount_model_volume(self.root,child,'volume://models','native-actor')
            self.assertTrue(retained['observer']['verified'])
            resolved=ollama_node.resolve_model_volume(self.root)
            self.assertEqual(resolved['child_root'],str(Path(child).resolve()))
            self.assertEqual(resolved['mount_kind'],'REFERENCE')
    def test_successful_pull_requires_provider_completion(self):
        with patch.object(ollama_node,'urlopen',return_value=BytesIO(b'{"status":"downloading"}')):
            result=ollama_node.execute(self.root,'pull',{'model':'resident'})
        self.assertEqual(result['state'],'OUTCOME_UNKNOWN')

    def test_process_interruption_after_retention_does_not_redispatch(self):
        ollama_node.retain(self.root,'/executions/interrupted/request.json',
            {'actor':'native-actor','operation':'chat','payload':{'model':'resident'}},'native-actor')
        with patch.object(ollama_node,'urlopen') as transport:
            result=ollama_node.execute(self.root,'chat',{'model':'resident'},request_id='interrupted')
        transport.assert_not_called()
        self.assertEqual(result['state'],'OUTCOME_UNKNOWN')
    def test_missing_child_definition_cannot_be_mounted(self):
        with tempfile.TemporaryDirectory() as child:
            with self.assertRaises(ValueError):
                ollama_node.mount_model_volume(self.root,child,'volume://models','native-actor')

    def test_model_backing_is_verified_without_claiming_inference(self):
        weights=self.root/'model-test-bytes.bin'
        weights.write_bytes(b'test backing bytes, not an LLM')
        ollama_node.index_model_file(self.root,weights,'test-artifact',{'classification':'TEST_ONLY'},'native-actor')
        observed=ollama_node.verify_model_file(self.root,'test-artifact')
        self.assertTrue(observed['backing_verified'])
        self.assertEqual(observed['inference_qualification'],'NOT_EXECUTED')
        weights.write_bytes(b'altered')
        with self.assertRaises(RuntimeError):ollama_node.verify_model_file(self.root,'test-artifact')
    def test_deleted_volume_is_not_silently_recreated(self):
        import shutil
        child=self.root/'child'
        ollama_node.retain(child,'/definition.json',{'volume':'models'},'volume')
        ollama_node.mount_model_volume(self.root,child,'volume://models','native-actor')
        shutil.rmtree(child)
        with self.assertRaises(FileNotFoundError):ollama_node.resolve_model_volume(self.root)
        self.assertFalse(child.exists())

if __name__=='__main__':unittest.main()
