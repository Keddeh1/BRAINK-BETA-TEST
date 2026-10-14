import unittest
from calibration import Measurements


class CalibrationTests(unittest.TestCase):
    def test_latency_exceedance_preserves_observer_and_no_coefficient_is_invented(self):
        observer=Measurements(window=3)
        self.assertEqual(observer.observe(20_000_000)['latency_acceptance'],'EXCEEDED')
        report=observer.observe(1_000_000)
        self.assertEqual(report['samples'],2)
        self.assertIsNone(report['tolerance_index'])
        self.assertIsNone(report['disk_io_saturation'])
        self.assertFalse(report['da_registrar']['affects_braink_admission'])
        observer.observe(1_000_000);report=observer.observe(1_000_000)
        self.assertEqual(report['p99_ns'],1_000_000)
        self.assertEqual(report['latency_acceptance'],'PASS')

    def test_invalid_samples_not_admitted_as_measurements(self):
        observer=Measurements()
        for value in (True,1.2,-1,'4'):
            with self.assertRaises(ValueError):observer.observe(value)
