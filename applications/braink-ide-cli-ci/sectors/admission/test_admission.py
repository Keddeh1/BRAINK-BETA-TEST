"""Local test doubles exercise the scaffold, not production cryptography."""
import struct
import unittest
from types import SimpleNamespace
from web4_admission import Web4Runtime, AdmissionError

class AdmissionTests(unittest.TestCase):
    def runtime(self, epoch=2, floor=1, payload=b"body", signature=True, valid=True, receipt="receipt"):
        wire=struct.pack(">4sQ4sI32s", b"KEX!", epoch, b"ARCH", 4, bytes(32))+bytes(64)
        self.commits=[]
        def accept(*args):
            self.commits.append(args)
            if isinstance(receipt, Exception):
                raise receipt
            return receipt
        return Web4Runtime(b"ARCH", SimpleNamespace(receive=lambda:(wire,payload)), SimpleNamespace(verify=lambda *_:signature), SimpleNamespace(validate=lambda *_:valid), SimpleNamespace(epoch_floor=lambda:floor, accept=accept))
    def test_unbound_never_receives(self):
        r=Web4Runtime(b"ARCH")
        with self.assertRaisesRegex(AdmissionError,"UNBOUND"): r.receive_update()
    def test_success_passes_expected_floor_and_complete_bytes(self):
        r=self.runtime()
        self.assertEqual(r.receive_update(),"receipt")
        self.assertEqual(self.commits[0][:2],(1,2))
        self.assertEqual(len(self.commits[0][2]),116)
        self.assertEqual(self.commits[0][3],b"body")
        self.assertEqual(r.state,"IDLE")
    def test_replay_rejected_before_commit(self):
        r=self.runtime(epoch=1)
        with self.assertRaisesRegex(AdmissionError,"REPLAY_OR_DOWNGRADE"): r.receive_update()
        self.assertEqual(self.commits,[])
    def test_verification_failures_never_commit(self):
        for kwargs in ({"signature":False},{"signature":1},{"valid":False},{"payload":b"bad"},{"floor":True}):
            with self.subTest(kwargs=kwargs):
                r=self.runtime(**kwargs)
                with self.assertRaises(AdmissionError): r.receive_update()
                self.assertEqual(self.commits,[])
                self.assertEqual(r.state,"HALTED")
    def test_commit_exception_halts_and_prevents_automatic_retry(self):
        r=self.runtime(receipt=OSError("commit result unknown"))
        with self.assertRaisesRegex(AdmissionError,"OSError"): r.receive_update()
        with self.assertRaisesRegex(AdmissionError,"HALTED"): r.receive_update()
        self.assertEqual(len(self.commits),1)
    def test_missing_receipt_after_commit_halts(self):
        r=self.runtime(receipt="")
        with self.assertRaisesRegex(AdmissionError,"DURABLE_RECEIPT_MISSING"): r.receive_update()
        self.assertEqual(len(self.commits),1)
        self.assertEqual(r.state,"HALTED")

if __name__ == "__main__": unittest.main()
