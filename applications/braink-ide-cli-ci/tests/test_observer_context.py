import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import test_protocol as fixtures
from braink_node.observer_state import observation
from braink_node.owner_vfs.store import VFSStore


class ObserverContextTests(unittest.TestCase):
    def test_zero_false_empty_and_null_values_keep_entity_context(self):
        for value in (0, False, '', [], {}, None):
            with self.subTest(value=value):
                state=observation('test-only-entity',{'anchor':'test-only-frame'},value,0,'test-domain')
                self.assertEqual(state['I'],'test-only-entity')
                self.assertEqual(state['O'],{'anchor':'test-only-frame'})
                self.assertEqual(state['t'],0)
                self.assertEqual(state['q'],value)

    def test_native_execution_receipt_retains_zero_result(self):
        fixtures.ProtocolTests.setUp(self)
        try:
            row=self.manager.instantiate(self.definition,['test-only-zero-execution'])
            bindings=SimpleNamespace(catalogue={'modules':{self.definition['id']:self.definition}},invoke=lambda *_:0)
            self.assertEqual(self.manager.invoke(row['instance'],bindings),0)
            store=VFSStore(self.root/'instances'/row['instance']/'vfs')
            # Find the retained result through the native paths index.
            with store._connect() as db:
                digest=db.execute("SELECT digest FROM paths WHERE path LIKE '/invocations/%/result.json'").fetchone()['digest']
            result=json.loads(store.read_content(digest))
            self.assertEqual(result['observer_state']['q'],0)
            self.assertEqual(result['observer_state']['I'],row['instance'])
            self.assertEqual(result['observer_state']['O']['module'],self.definition['id'])
            self.assertTrue(store.verify_receipt_chain()['verified'])
        finally: fixtures.ProtocolTests.tearDown(self)

if __name__ == '__main__': unittest.main()
