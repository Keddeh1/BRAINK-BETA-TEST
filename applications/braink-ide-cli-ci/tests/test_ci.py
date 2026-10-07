import json
from pathlib import Path
import sys
import threading
import unittest
from fixtures import NodeFixture
from braink_ci.runner import CIRunner, validate_pipeline, sector_pipeline
from braink_ci.relay import WebsiteRelay


class CiTests(NodeFixture, unittest.TestCase):
    def runner(self):
        return CIRunner(self.base / "ci", self.store, python=sys.executable)

    def pipeline(self, command, timeout=10):
        return {"schema": "braink.ci.pipeline.v1", "name": "fixture",
                "stages": [{"name": "actual-process", "command": command, "timeout": timeout}]}

    def test_actual_success_logs_artifacts_and_receipt(self):
        self.file("source.txt", b"original")
        runner = self.runner()
        pipeline = self.pipeline(["{python}", "-c", "from pathlib import Path; print('ran'); Path(r'{artifacts}/result.txt').write_text('artifact')"])
        queued = runner.submit(self.root, pipeline)
        self.file("source.txt", b"changed after submission")
        result = runner.execute_next()
        self.assertEqual(result["status"], "passed")
        self.assertEqual((runner.root / "runs" / queued["id"] / "source/source.txt").read_bytes(), b"original")
        self.assertEqual(result["artifacts"][0]["size"], 8)
        self.assertIn("ran", runner.read_log(queued["id"], "actual-process"))
        self.assertEqual(runner.get(queued["id"])["receipt_sha256"], result["receipt_sha256"])
        self.assertEqual(runner.list()[0]["status"], "passed")
        self.assertTrue(self.store.verify()["ok"])

    def test_real_nonzero_exit_stops_pipeline(self):
        self.file("source.txt")
        runner = self.runner()
        pipeline = self.pipeline(["{python}", "-c", "raise SystemExit(7)"])
        pipeline["stages"].append({"name": "must-not-run", "command": ["{python}", "-c", "raise Exception()"]})
        runner.submit(self.root, pipeline)
        result = runner.execute_next()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stages"][0]["returncode"], 7)
        self.assertEqual(len(result["stages"]), 1)

    def test_timeout_terminates_stage(self):
        self.file("source.txt")
        runner = self.runner()
        runner.submit(self.root, self.pipeline(["{python}", "-c", "import time; time.sleep(30)"], timeout=0.1))
        result = runner.execute_next()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stages"][0]["status"], "timed_out")

    def test_two_workers_claim_once(self):
        self.file("source.txt")
        runner = self.runner()
        runner.submit(self.root, self.pipeline(["{python}", "-c", "print('once')"]))
        results = []
        threads = [threading.Thread(target=lambda: results.append(runner.execute_next())) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(sum(result is not None for result in results), 1)

    def test_sector_build_definition(self):
        for sector in ("core", "cli", "ide", "ci", "all"):
            self.assertEqual(validate_pipeline(sector_pipeline(sector))["sector"], sector)
        with self.assertRaises(ValueError):sector_pipeline("unknown")
        with self.assertRaises(ValueError):validate_pipeline({"stages": []})

    def test_result_outbox_retries_before_claim(self):
        self.file("source.txt")
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"BRAINK_CI_AGENT_TOKEN": "test-agent"}):
            relay = WebsiteRelay(self.runner(), self.root, "https://www.keddeh.com")
        relay.outbox.write_text(json.dumps({"op": "result", "id": "job"}))
        calls = []
        relay.call = lambda payload: calls.append(payload) or ({"job": None} if payload["op"] == "claim" else {"ok": True})
        self.assertIsNone(relay.tick())
        self.assertEqual([call["op"] for call in calls], ["result", "claim"])
        self.assertFalse(relay.outbox.exists())

    def test_interrupted_execution_has_terminal_receipt(self):
        from braink_node.canonical import canonical_bytes, sha256_hex
        self.file("source.txt")
        runner = self.runner()
        queued = runner.submit(self.root, self.pipeline(["{python}", "-c", "print('ok')"]))
        runner.claim()
        report = runner.interrupt(queued["id"])
        self.assertEqual(report["status"], "error")
        self.assertIn("finished", report)
        self.assertEqual(report["receipt_sha256"], sha256_hex(canonical_bytes({k:v for k,v in report.items() if k != "receipt_sha256"})))

    def test_branch_submission_builds_exact_committed_source(self):
        import os
        import subprocess
        from unittest.mock import patch
        self.file('source.txt', b'committed')
        for command in (["init", "-q"], ["config", "user.name", "BRAINK test"], ["config", "user.email", "fixture@example.test"], ["add", "."], ["commit", "-qm", "fixture"]):
            subprocess.run(["git", *command], cwd=self.root, check=True)
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.file('source.txt', b'uncommitted edit')
        runner = self.runner()
        pipeline = self.pipeline(["{python}", "-c", "from pathlib import Path; print(Path('source.txt').read_text())"])
        with patch.dict(os.environ, {"BRAINK_CI_AGENT_TOKEN": "test-agent"}), patch('braink_ci.relay.sector_pipeline', return_value=pipeline):
            relay = WebsiteRelay(runner, self.root, 'https://www.keddeh.com')
            receipts = []
            relay.call = lambda payload: receipts.append(payload) or {'ok':True}
            result = relay.execute({'id':'remote','sector':'core','lease_token':'lease','parameters':{'source_commit':revision}})
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['stages'][0]['log_text'].strip(), 'committed')
        self.assertEqual(runner.list()[0]['pipeline']['source_commit'], revision)
        self.assertEqual(receipts[0]['op'], 'result')

    def test_interrupted_stage_without_log_still_reports(self):
        self.file('source.txt')
        runner = self.runner()
        queued = runner.submit(self.root, self.pipeline(["{python}", "-c", "print('ok')"]))
        report = runner.claim()
        report['stages'].append({'name':'actual-process','status':'running','log':'actual-process.log'})
        runner._save(report)
        result = runner.interrupt(queued['id'])
        self.assertEqual(result['stages'][0]['status'], 'interrupted')
        self.assertEqual(runner.read_log(queued['id'], 'actual-process'), '')
