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

if __name__=='__main__':unittest.main()
