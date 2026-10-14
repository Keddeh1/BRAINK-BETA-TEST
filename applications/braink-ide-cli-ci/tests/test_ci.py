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
        self.file('application/source.txt', b'committed')
        for command in (["init", "-q"], ["config", "user.name", "BRAINK test"], ["config", "user.email", "fixture@example.test"], ["add", "."], ["commit", "-qm", "fixture"]):
            subprocess.run(["git", *command], cwd=self.root, check=True)
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.file('application/source.txt', b'uncommitted edit')
        runner = self.runner()
        pipeline = self.pipeline(["{python}", "-c", "from pathlib import Path; print(Path('source.txt').read_text())"])
        with patch.dict(os.environ, {"BRAINK_CI_AGENT_TOKEN": "test-agent"}), patch('braink_ci.relay.sector_pipeline', return_value=pipeline):
            relay = WebsiteRelay(runner, self.root/'application', 'https://www.keddeh.com')
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

    def test_invalid_source_revision_finishes_remote_job(self):
        import os
        from unittest.mock import patch
        self.file('source.txt')
        with patch.dict(os.environ, {'BRAINK_CI_AGENT_TOKEN':'test-agent'}):
            relay = WebsiteRelay(self.runner(), self.root, 'https://www.keddeh.com')
        calls=[]
        job={'id':'remote','sector':'core','lease_token':'lease','parameters':{'source_commit':'invalid'}}
        def transport(payload):
            calls.append(payload)
            return {'job':job} if payload['op']=='claim' else {'ok':True}
        relay.call=transport
        report=relay.tick()
        self.assertEqual(report['status'],'error')
        self.assertEqual(calls[-1]['op'],'result')
        self.assertFalse(relay.outbox.exists())


class CiIntegrityTests(NodeFixture, unittest.TestCase):
    def test_tampered_snapshot_never_executes(self):
        self.file('source.txt', b'original')
        runner = CIRunner(self.base / 'ci', self.store)
        marker = self.base / 'must-not-exist'
        queued = runner.submit(self.root, {'schema':'braink.ci.pipeline.v1', 'stages':[
            {'name':'mutation', 'command':[sys.executable, '-c', f"open({str(marker)!r}, 'w').write('ran')"]}]})
        (runner.root / 'runs' / queued['id'] / 'source/source.txt').write_bytes(b'tampered')
        result = runner.execute_next()
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['stages'], [])
        self.assertFalse(marker.exists())
        self.assertTrue(self.store.verify()['ok'])

    def test_added_source_and_rewritten_manifest_are_rejected(self):
        from braink_ci.runner import verify_source_snapshot
        from braink_node.canonical import canonical_bytes, sha256_hex
        self.file('source.txt')
        runner = CIRunner(self.base / 'ci', self.store)
        queued = runner.submit(self.root)
        run = runner.root / 'runs' / queued['id']
        extra = run / 'source/injected.py'
        extra.write_text('raise SystemExit(0)')
        with self.assertRaisesRegex(ValueError, 'file set'):
            verify_source_snapshot(run, queued['source_digest'])
        extra.unlink()
        manifest_path = run / 'source-manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['files'][0]['sha256'] = '0' * 64
        manifest['digest'] = sha256_hex(canonical_bytes(manifest['files']))
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'submitted receipt'):
            verify_source_snapshot(run, queued['source_digest'])

    def test_qualification_cleanup_preserves_evidence_and_rejects_symlinks(self):
        import importlib.util
        script = Path(__file__).resolve().parents[1] / 'scripts/qualify_installed.py'
        spec = importlib.util.spec_from_file_location('qualification_lifecycle', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = self.base / 'run'; run.mkdir()
        env = run / 'qualification-venv'; env.mkdir()
        (env / 'pyvenv.cfg').write_text('home = test')
        evidence = run / 'report.json'; evidence.write_text('retained')
        module.release_environment(run)
        self.assertFalse(env.exists())
        self.assertEqual(evidence.read_text(), 'retained')
        protected = self.base / 'protected'; protected.mkdir()
        (protected / 'pyvenv.cfg').write_text('preserve')
        env.symlink_to(protected)
        with self.assertRaises(ValueError): module.release_environment(run)
        self.assertTrue((protected / 'pyvenv.cfg').exists())

    def test_modified_artifact_and_log_cannot_be_published(self):
        self.file('source.txt')
        runner = CIRunner(self.base / 'ci', self.store)
        runner.submit(self.root, {'schema':'braink.ci.pipeline.v1', 'stages':[
            {'name':'produce', 'command':[sys.executable, '-c', "from pathlib import Path; print('log'); Path(r'{artifacts}/output').write_bytes(b'original')"]}]})
        report = runner.execute_next()
        self.assertTrue(runner.verify_report(report))
        run = runner.root / 'runs' / report['id']
        artifact = run / report['artifacts'][0]['path']
        artifact.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'artifact differs'): runner.verify_report(report)
        artifact.write_bytes(b'original')
        (run / report['stages'][0]['log']).write_text('changed log')
        with self.assertRaisesRegex(ValueError, 'log differs'): runner.verify_report(report)
        report['status'] = 'error'
        with self.assertRaisesRegex(ValueError, 'terminal receipt'): runner.verify_report(report)

    def test_maintenance_retains_failed_and_active_run_tools(self):
        import subprocess
        from braink_ci.maintenance import reclaim_qualified_environments
        root = self.base / 'ci'
        for name, status in [('successful', 'passed'), ('failed', 'failed'), ('active', 'passed')]:
            run = root / 'runs' / name
            env = run / 'qualification-venv'; env.mkdir(parents=True)
            (env / 'pyvenv.cfg').write_text('test')
            (run / 'report.json').write_text(json.dumps({'status':status, 'finished':1}))
        process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', str(root / 'runs/active')])
        try:
            result = reclaim_qualified_environments(root)
            self.assertEqual(result['removed'], ['successful'])
            self.assertTrue((root / 'runs/failed/qualification-venv').exists())
            self.assertTrue((root / 'runs/active/qualification-venv').exists())
            self.assertTrue((root / 'runs/successful/report.json').exists())
        finally:
            process.terminate(); process.wait(timeout=5)

    def test_restarted_supervisor_uses_activated_source_and_git_checkout(self):
        import importlib.util
        script = Path(__file__).resolve().parents[1] / 'scripts/supervise_node.py'
        spec = importlib.util.spec_from_file_location('supervisor_binding', script)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        old = self.base / 'old'; new = self.base / 'new'; checkout = self.base / 'checkout'
        for path in (old, new, checkout): path.mkdir()
        config = self.base / 'config.json'
        config.write_text(json.dumps({'source':str(new), 'desired_source':str(checkout)}))
        self.assertEqual(module.configured_sources(old, config), (new, checkout))
        self.assertEqual(module.configured_sources(old, None), (old, old))
