import unittest
from substrate import encode,decode

class FrameTests(unittest.TestCase):
    def test_complete_frame_preserves_zero_state(self):
        state={'I':'test-only-node','O':{'anchor':'test-frame'},'q':0,'t':0}
        self.assertEqual(decode(encode(state,7))['state'],state)
    def test_crc_rejects_modified_payload(self):
        raw=bytearray(encode({'value':1},7));raw[-2]^=1
        with self.assertRaises(ValueError):decode(bytes(raw))
    def test_truncation_rejected(self):
        frame=encode({'value':1},7)
        for size in (0,10,len(frame)-1):
            with self.assertRaises(ValueError):decode(frame[:size])
    def test_trailing_bytes_rejected(self):
        with self.assertRaises(ValueError):decode(encode({'value':1},7)+b'x')
    def test_mask_is_observed_not_assumed(self):
        self.assertEqual(decode(encode({'value':1},3))['readiness_mask'],3)

if __name__=='__main__':unittest.main()
