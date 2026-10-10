from fractions import Fraction
import tempfile
import unittest
from braink_node.owner_vfs.store import VFSStore
from observer_algebra import frame, observe, operate, reverse_orientation, evaluate


class ObserverAlgebraTests(unittest.TestCase):
    def state(self, q, o=1, epsilon=1, identity='test-only-object'):
        return observe(identity, frame(o, epsilon, 'O'), str(Fraction(q)*epsilon+Fraction(o)), 'test-only-time')

    def test_zero_retains_complete_observer(self):
        state = observe('test-only-object', frame(1, 1, 'O'), 1, 'test-only-time')
        self.assertEqual(state, {'I':'test-only-object','O':{'anchor':'O','o':'1','epsilon':1},'q':'0','t':'test-only-time'})

    def test_supplied_signed_example_keeps_operations_distinct(self):
        a,b=self.state(-3),self.state(-14)
        self.assertEqual(operate(a,b,'coordinate_add','test-result','test-time')['q'],'-17')
        self.assertEqual(operate(a,b,'transported_add','test-result','test-time')['q'],'-16')
        self.assertEqual(a['q'],'-3')

    def test_transport_matches_underlying_arithmetic_and_identities(self):
        for o in (-3,0,1,2):
            for epsilon in (-1,1):
                for u in range(-4,5):
                    a=self.state(u,o,epsilon)
                    zero=self.state(-epsilon*o,o,epsilon)
                    one=self.state(epsilon*(1-o),o,epsilon)
                    self.assertEqual(operate(a,zero,'transported_add','r','t')['q'],str(u))
                    self.assertEqual(operate(a,one,'transported_multiply','r','t')['q'],str(u))
                    for v in range(-4,5):
                        b=self.state(v,o,epsilon)
                        x,y=epsilon*u+o,epsilon*v+o
                        self.assertEqual(Fraction(operate(a,b,'transported_add','r','t')['q']),epsilon*(x+y-o))
                        self.assertEqual(Fraction(operate(a,b,'transported_multiply','r','t')['q']),epsilon*(x*y-o))

    def test_orientation_involution_preserves_physical_position(self):
        a=self.state('-3/2')
        b=reverse_orientation(a)
        self.assertEqual(reverse_orientation(b),a)
        self.assertEqual(b['I'],a['I'])
        self.assertEqual(b['t'],a['t'])
        self.assertEqual(Fraction(a['q'])*a['O']['epsilon']+Fraction(a['O']['o']),Fraction(b['q'])*b['O']['epsilon']+Fraction(b['O']['o']))

    def test_mixed_frames_rejected_without_silent_collapse(self):
        with self.assertRaises(ValueError): operate(self.state(1),self.state(1,epsilon=-1),'coordinate_add','r','t')

    def test_retained_result_replays_and_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as root:
            VFSStore(root)
            request={'left':self.state(-3),'right':self.state(-14),'operation':'coordinate_add','result_identity':'test-result','time':'test-time'}
            first=evaluate(root,'test-only-actor',request,'test-request')
            second=evaluate(root,'test-only-actor',request,'test-request')
            self.assertEqual(first['result'],second['result'])
            self.assertTrue(second['replayed'])
            with self.assertRaises(ValueError): evaluate(root,'test-only-actor',{**request,'operation':'transported_add'},'test-request')
            self.assertTrue(VFSStore(root).verify_receipt_chain()['verified'])

if __name__ == '__main__': unittest.main()
