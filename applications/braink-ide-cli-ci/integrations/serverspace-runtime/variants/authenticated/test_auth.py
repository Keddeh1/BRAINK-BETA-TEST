import tempfile
from pathlib import Path
import unittest
from cryptography.exceptions import InvalidSignature
import handshake_auth as auth
from substrate import encode,decode

class AuthenticationTests(unittest.TestCase):
    def test_independent_wholes_remain_distinct_at_unit_value(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            one=auth.enroll(a,'node://one');two=auth.enroll(b,'node://two')
            self.assertNotEqual(one['server_public'],two['server_public'])
            self.assertNotEqual(one['client_public'],two['client_public'])
            self.assertEqual(decode(encode({'I':'node://one','q':1},7))['state']['q'],decode(encode({'I':'node://two','q':1},7))['state']['q'])
            with self.assertRaises(ValueError):auth.load(a,'node://two')
    def test_reenrollment_retains_keys(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(auth.enroll(root,'node://one'),auth.enroll(root,'node://one'))
    def test_runtime_context_cannot_be_relabelled(self):
        with tempfile.TemporaryDirectory() as root:
            auth.enroll(root,'node://one')
            with self.assertRaises(ValueError):auth.enroll(root,'node://two')
    def test_pinned_signature_and_challenge_binding(self):
        with tempfile.TemporaryDirectory() as root:
            pin=auth.enroll(root,'node://one');message=auth.context('node://one',1,2,3)+b'RESPONSE'+b'a'*32+b'b'*32+encode({'q':0},7)
            signature=auth.private(root,'server').sign(message)
            auth.verify(pin['server_public'],signature,message)
            for altered in (message+b'x',message.replace(b'a'*32,b'c'*32),message.replace(b'node://one',b'node://two')):
                with self.assertRaises(InvalidSignature):auth.verify(pin['server_public'],signature,altered)
    def test_permissive_private_key_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            auth.enroll(root,'node://one');Path(root,'handshake-server.key').chmod(0o644)
            with self.assertRaises(ValueError):auth.private(root,'server')

if __name__=='__main__':unittest.main()
