from decimal import Decimal, localcontext, ROUND_FLOOR
import unittest
from consilience import aggregate, LOG_Q32, SCALE


class ConsilienceTests(unittest.TestCase):
    def test_constants_and_cumulative_bound(self):
        for precision in (80, 120):
            with localcontext() as context:
                context.prec = precision
                for level, constant in LOG_Q32.items():
                    self.assertEqual(constant,int((Decimal(level).ln()*SCALE).to_integral_value(rounding=ROUND_FLOOR)))
                levels=[2,3,4,2,4]
                exact=sum(Decimal(level).ln() for level in levels)
                measured=Decimal(aggregate(levels)['raw_q32'])/SCALE
                self.assertGreaterEqual(exact-measured,0)
                self.assertLess(exact-measured,Decimal(len(levels))/SCALE)

    def test_no_inferred_or_zero_warrant(self):
        for level in (0,-1,5,True,2.0,'2'):
            with self.assertRaises(ValueError): aggregate([level])

    def test_identity_and_commutativity(self):
        self.assertEqual(aggregate([1,1])['raw_q32'],0)
        self.assertEqual(aggregate([2,3,4])['raw_q32'],aggregate([4,2,3])['raw_q32'])
        self.assertEqual(aggregate([])['terms'],0)


if __name__ == '__main__': unittest.main()
