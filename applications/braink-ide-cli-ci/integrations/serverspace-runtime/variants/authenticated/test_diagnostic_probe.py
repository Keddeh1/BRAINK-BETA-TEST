from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from diagnostic_probe import incident, persist, probe, seal, MAX_BYTES


class ProbeTests(unittest.TestCase):
    def test_concurrent_rolling_ledger_and_seals(self):
        with tempfile.TemporaryDirectory() as root:
            records = [incident('/missing/'+str(i), 'ROUTE', 'unmapped') for i in range(230)]
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda record: persist(root, record), records))
            path = Path(root)/'IT_INCIDENT_DISPATCH_LEDGER.ndjson'
            retained = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(retained),200)
            self.assertLessEqual(path.stat().st_size, MAX_BYTES)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertTrue(all(record['seal']==seal(record) for record in retained))
            self.assertEqual(len({record['incidentId'] for record in retained}),200)

    def test_oversize_existing_ledger_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'IT_INCIDENT_DISPATCH_LEDGER.ndjson'
            with path.open('wb') as target: target.truncate(MAX_BYTES+1)
            with self.assertRaises(ValueError): persist(root, incident('/', 'FAIL', 'test'))
            self.assertEqual(path.stat().st_size,MAX_BYTES+1)

    def test_only_loopback_is_probed(self):
        for uri in ('http://example.com/', 'http://127.0.0.1.evil/', 'https://127.0.0.1/'):
            with self.assertRaises(ValueError): probe(uri)


if __name__ == '__main__': unittest.main()
