"""Execute sector jobs from the existing owner's website/runtime control plane."""
import json
import os
from pathlib import Path
import threading
import time
import urllib.request
import subprocess
import shlex
import sys
import base64
from urllib.parse import urlparse

from .runner import sector_pipeline
from braink_node.storage import atomic_write
from braink_node.canonical import canonical_bytes, sha256_hex


class WebsiteRelay:
    def __init__(self, runner, source, website):
        self.runner = runner
        self.source = Path(source).resolve(strict=True)
        parsed = urlparse(website)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Use the configured owner's HTTPS runtime endpoint")
        self.endpoint = website.rstrip("/") + "/api/braink-development/worker"
        self.token = os.getenv("BRAINK_CI_AGENT_TOKEN")
        if not self.token:
            raise ValueError("Configure the CI node worker credential in its runtime")
        self.worker_id = os.getenv("BRAINK_CI_WORKER_ID", "braink-development-sector")
        self.outbox = runner.root / "website-outbox.json"
        self.active = runner.root / "website-active.json"

    def call(self, body):
        request = urllib.request.Request(self.endpoint, data=json.dumps(body).encode(),
                    headers={"User-Agent": "BRAINK-CI/0.1", "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
        if result.get("error"):
            raise RuntimeError("Owner runtime rejected the CI operation: " + str(result["error"]))
        return result

    def flush(self):
        if self.outbox.exists():
            self.call(json.loads(self.outbox.read_text()))
            self.outbox.unlink()
            self.active.unlink(missing_ok=True)

    def execute(self, job):
        if job.get("operation", "qualify") != "qualify":
            atomic_write(self.active, json.dumps({"remote": job}).encode())
            return self.execute_action(job)
        if self.active.exists():
            record = json.loads(self.active.read_text())
            if record["remote"]["id"] != job["id"]:
                raise ValueError("An earlier sector execution must finish before a new claim")
            local_id = record["local_id"]
        else:
            source = self.source
            pipeline = sector_pipeline(job["sector"])
            revision = job.get("parameters", {}).get("source_commit")
            if revision:
                import re, io, tarfile
                if not re.fullmatch(r"[a-f0-9]{40}", revision):
                    raise ValueError("Invalid source commit")
                prefix = subprocess.check_output(["git", "rev-parse", "--show-prefix"], cwd=self.source, text=True).strip().rstrip("/")
                repository = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=self.source, text=True).strip()
                archive = subprocess.check_output(["git", "archive", revision + (":" + prefix if prefix else "")], cwd=repository)
                source = self.runner.root / "commit-snapshots" / revision
                if not source.exists() or not any(source.iterdir()):
                    source.mkdir(parents=True, exist_ok=True)
                    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
                        bundle.extractall(source, filter="data")
                pipeline["source_commit"] = revision
            queued = self.runner.submit(source, pipeline)
            local_id = queued["id"]
            atomic_write(self.active, json.dumps({"remote": job, "local_id": local_id}).encode())
        report = self.runner.get(local_id)
        if report["status"] == "running":
            # This relay is the sole node worker; a prior process may have stopped mid-stage.
            report = self.runner.interrupt(local_id)
        if report["status"] == "queued":
            heartbeat_stop = threading.Event()
            def heartbeat():
                while not heartbeat_stop.wait(10):
                    try:self.call({"op": "heartbeat", "id": job["id"], "lease_token": job["lease_token"]})
                    except Exception:pass  # Durable result outbox retries independently.
            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                while self.runner.get(local_id)["status"] == "queued":
                    self.runner.execute_next()
                report = self.runner.get(local_id)
            finally:
                heartbeat_stop.set()
                thread.join(timeout=1)
        # Include actual stage logs and hashes, never runtime credentials or source contents.
        receipt_body = canonical_bytes({key: value for key, value in report.items() if key != "receipt_sha256"}).decode()
        public = json.loads(json.dumps({key: report[key] for key in ("id", "status", "source_digest", "source_commit", "stages", "artifacts", "finished", "receipt_sha256") if key in report}))
        for stage in public["stages"]:
            stage["log_text"] = self.runner.read_log(local_id, stage["name"])
        blobs = [{"path": artifact["path"], "base64": base64.b64encode((self.runner.root / "runs" / local_id / artifact["path"]).read_bytes()).decode()} for artifact in report["artifacts"]]
        atomic_write(self.outbox, json.dumps({"op": "result", "id": job["id"],
                     "lease_token": job["lease_token"], "report": public,
                     "receipt_body": receipt_body, "artifact_blobs": blobs}).encode())
        self.flush()
        return public

    def execute_action(self, job):
        request = job.get("parameters", {})
        operation = job["operation"]
        report = {"id": job["id"], "sector": job["sector"], "operation": operation,
                  "status": "running", "stages": [], "artifacts": []}
        try:
            if operation == "cli":
                runtime = self.runner.root.parent.parent
                workspace = Path(os.getenv("BRAINK_WORKSPACE", str(runtime / "workspace")))
                state = self.runner.root.parent
                argv = shlex.split(request.get("command", ""))
                result = subprocess.run([sys.executable, "-m", "braink_cli.cli", "--workspace", str(workspace),
                                         "--state-dir", str(state)] + argv,
                                        capture_output=True, text=True)
                report.update(status="passed" if result.returncode == 0 else "failed",
                              outputs={"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
            else:
                route = "/api/files" if operation == "file-list" else "/api/file"
                if operation == "file-read":
                    from urllib.parse import urlencode
                    route += "?" + urlencode({"path": request.get("path", "")})
                payload = json.dumps(request).encode() if operation == "file-save" else None
                headers = {"Content-Type": "application/json"}
                if os.getenv("BRAINK_NODE_TOKEN"):
                    headers["Authorization"] = "Bearer " + os.environ["BRAINK_NODE_TOKEN"]
                local = urllib.request.Request(os.getenv("BRAINK_IDE_ENDPOINT", "http://127.0.0.1:8765") + route,
                                               data=payload, headers=headers)
                with urllib.request.urlopen(local, timeout=30) as response:
                    report.update(status="passed", outputs=json.load(response))
        except Exception as error:
            report.update(status="error", reason=str(error))
        report["finished"] = time.time()
        report["receipt_sha256"] = sha256_hex(canonical_bytes(report))
        self.runner.ledger.append(event_type="braink.sector.action.completed", route="braink-node/ci",
                                   payload={"job_id": job["id"], "operation": operation,
                                            "status": report["status"], "receipt_sha256": report["receipt_sha256"]})
        atomic_write(self.outbox, json.dumps({"op": "result", "id": job["id"],
                     "lease_token": job["lease_token"], "report": report}).encode())
        self.flush()
        return report

    def tick(self):
        self.flush()
        job = json.loads(self.active.read_text())["remote"] if self.active.exists() else self.call({"op": "claim", "worker_id": self.worker_id}).get("job")
        if not job:
            return None
        try:
            return self.execute(job)
        except (ValueError, subprocess.CalledProcessError) as error:
            report = {"id": job["id"], "status": "error", "reason": str(error),
                      "stages": [], "artifacts": [], "finished": time.time()}
            report["receipt_sha256"] = sha256_hex(canonical_bytes(report))
            self.runner.ledger.append(event_type="braink.ci.source.error", route="braink-node/ci",
                                      payload={"job_id": job["id"], "reason": report["reason"]})
            atomic_write(self.outbox, json.dumps({"op": "result", "id": job["id"],
                         "lease_token": job["lease_token"], "report": report}).encode())
            self.flush()
            return report

    def serve(self):
        import fcntl
        # One persistent relay owns this worker identity and its recovery outbox.
        lock = (self.runner.root / "relay.lock").open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while True:
            try:
                result = self.tick()
                if result:
                    print(json.dumps({"sector_job": result["id"], "status": result["status"]}), flush=True)
            except Exception as error:
                print(json.dumps({"event": "ci-relay-retry", "reason": type(error).__name__}), flush=True)
            time.sleep(3)
