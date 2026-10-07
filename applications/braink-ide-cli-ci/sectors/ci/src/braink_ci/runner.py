"""BRAINK-owned CI: durable jobs, local execution, logs and artifact receipts.

Runs trusted owner source on the owner's host. No hosted CI service or external
scheduler is used. Execution uses the existing owner runtime identity.
"""
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import time
import uuid

from braink_node.canonical import canonical_bytes, sha256_hex
from braink_node.storage import atomic_write


def sector_pipeline(sector="all"):
    if sector not in {"core", "cli", "ide", "ci", "all"}:
        raise ValueError("Unknown BRAINK development sector")
    return {"schema": "braink.ci.pipeline.v1", "name": f"braink-{sector}", "sector": sector,
            "stages": [
                {"name": "syntax", "command": ["{python}", "-m", "compileall", "-q", "sectors" if sector == "all" else "sectors/" + sector], "timeout": 120},
                {"name": "clean-sector-build", "command": ["{python}", "scripts/build_sector.py", "--sector", sector, "--run", "{run}", "--artifacts", "{artifacts}"], "timeout": 300},
                {"name": "test-installed-sector", "command": ["{python}", "scripts/qualify_installed.py", "{artifacts}", "{run}", sector], "timeout": 180},
            ]}


DEFAULT_PIPELINE = sector_pipeline()


def validate_pipeline(obj):
    if not isinstance(obj, dict) or obj.get("schema") != "braink.ci.pipeline.v1":
        raise ValueError("Unsupported CI pipeline schema")
    stages = obj.get("stages")
    if not isinstance(stages, list) or not stages or len(stages) > 30:
        raise ValueError("CI pipeline requires 1–30 stages")
    names = set()
    for stage in stages:
        if not isinstance(stage, dict):
            raise ValueError("Stage must be an object")
        name = stage.get("name", "")
        command = stage.get("command")
        timeout = stage.get("timeout", 180)
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", name) or name in names:
            raise ValueError("Stage names must be unique safe identifiers")
        if not isinstance(command, list) or not command or any(not isinstance(x, str) for x in command):
            raise ValueError("Stage command must be a nonempty argument list")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 3600:
            raise ValueError("Stage timeout must be within 1–3600 seconds")
        names.add(name)
    canonical_bytes(obj)
    return obj


def snapshot_source(source: Path, destination: Path):
    """Hash the copied tree, excluding generated state and hidden credentials."""
    source = source.resolve(strict=True)
    if not source.is_dir() or destination.resolve().is_relative_to(source):
        raise ValueError("CI run state must be outside the source tree")
    ignored = {"node_modules", "__pycache__", "build", "dist", "htmlcov"}
    inventory = []
    for parent, directories, filenames in os.walk(source, followlinks=False):
        directories[:] = sorted(d for d in directories if not d.startswith(".") and
                                 d not in ignored and not (Path(parent) / d).is_symlink() and
                                 not d.endswith(".egg-info"))
        for name in sorted(filenames):
            path = Path(parent) / name
            if name.startswith(".") or path.suffix == ".pyc" or path.is_symlink():
                continue
            relative = path.relative_to(source)
            data = path.read_bytes()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            inventory.append({"path": relative.as_posix(), "size": len(data), "sha256": sha256_hex(data)})
    if not inventory:
        raise ValueError("Source snapshot is empty")
    return {"digest": sha256_hex(canonical_bytes(inventory)), "files": inventory}


class CIRunner:
    def __init__(self, root: Path, ledger, python=None):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "ci.sqlite3"
        self.ledger = ledger
        self.python = python or os.getenv("BRAINK_CI_PYTHON", sys.executable)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL, "
                       "created REAL NOT NULL, source TEXT NOT NULL, report TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.database, timeout=30)

    def submit(self, source: Path, pipeline=None):
        source = source.resolve(strict=True)
        if not source.is_dir():
            raise ValueError("CI source must be a directory")
        pipeline = validate_pipeline(pipeline or DEFAULT_PIPELINE)
        job_id = uuid.uuid4().hex
        run = self.root / "runs" / job_id
        run.mkdir(parents=True)
        snapshot = snapshot_source(source, run / "source")
        atomic_write(run / "source-manifest.json", canonical_bytes(snapshot))
        report = {"id": job_id, "status": "queued", "source": str(source),
                  "source_digest": snapshot["digest"], "source_commit": pipeline.get("source_commit"), "pipeline": pipeline,
                  "created": time.time(), "stages": [], "artifacts": []}
        with self.connect() as db:
            db.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?)",
                       (job_id, "queued", report["created"], str(source), json.dumps(report)))
        self.ledger.append(event_type="braink.ci.queued", route="braink-node/ci",
                           payload={"job_id": job_id, "source_digest": snapshot["digest"]})
        return report

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT report FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown CI job")
        return json.loads(row[0])

    def list(self, limit=20):
        if not 1 <= limit <= 100:
            raise ValueError("CI list limit must be 1–100")
        with self.connect() as db:
            rows = db.execute("SELECT report FROM jobs ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _save(self, report):
        raw = json.dumps(report)
        with self.connect() as db:
            db.execute("UPDATE jobs SET status=?, report=? WHERE id=?",
                       (report["status"], raw, report["id"]))
        atomic_write(self.root / "runs" / report["id"] / "report.json", raw.encode())

    def claim(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id, report FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if row is None:
                return None
            report = json.loads(row[1])
            report.update(status="running", started=time.time(), worker_pid=os.getpid())
            db.execute("UPDATE jobs SET status='running', report=? WHERE id=?", (json.dumps(report), row[0]))
        return report

    def execute_next(self):
        report = self.claim()
        if report is None:
            return None
        return self._execute(report)

    def _execute(self, report):
        run = self.root / "runs" / report["id"]
        artifacts = run / "artifacts"
        artifacts.mkdir(exist_ok=True)
        values = {"python": self.python, "source": str(run / "source"),
                  "run": str(run), "artifacts": str(artifacts)}
        self.ledger.append(event_type="braink.ci.started", route="braink-node/ci",
                           payload={"job_id": report["id"], "source_digest": report["source_digest"]})
        try:
            for stage in report["pipeline"]["stages"]:
                command = [arg.format_map(values) for arg in stage["command"]]
                log = run / (stage["name"] + ".log")
                result = {"name": stage["name"], "command": command, "started": time.time(),
                          "log": log.name, "status": "running"}
                report["stages"].append(result)
                self._save(report)
                # Keep runtime transport configuration without passing controller authority to builds.
                safe = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT", "COMSPEC",
                        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy",
                        "https_proxy", "all_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR",
                        "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "PIP_CERT", "PIP_INDEX_URL"}
                environment = {key: value for key, value in os.environ.items() if key in safe}
                environment["PYTHONPATH"] = os.pathsep.join(str(p) for p in (run / "source" / "sectors").glob("*/src"))
                with log.open("wb") as output:
                    process = subprocess.Popen(command, cwd=run / "source", env=environment,
                                                stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                                start_new_session=True)
                    try:
                        code = process.wait(timeout=stage.get("timeout", 180))
                        result.update(returncode=code, status="passed" if code == 0 else "failed")
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        result.update(returncode=process.returncode, status="timed_out")
                result["finished"] = time.time()
                result["log_sha256"] = sha256_hex(log.read_bytes())
                self._save(report)
                if result["status"] != "passed":
                    report["status"] = "failed"
                    break
            else:
                report["status"] = "passed"
            for path in sorted(artifacts.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    data = path.read_bytes()
                    report["artifacts"].append({"path": str(path.relative_to(run)),
                                                "size": len(data), "sha256": sha256_hex(data)})
        except Exception as error:
            report.update(status="error", reason=str(error))
        report["finished"] = time.time()
        report["receipt_sha256"] = sha256_hex(canonical_bytes(report))
        self._save(report)
        self.ledger.append(event_type="braink.ci.completed", route="braink-node/ci",
                           payload={"job_id": report["id"], "status": report["status"],
                                    "receipt_sha256": report["receipt_sha256"],
                                    "source_digest": report["source_digest"]})
        return report

    def interrupt(self, job_id):
        """Finalize a stopped execution with a verifiable terminal receipt."""
        report = self.get(job_id)
        if report["status"] != "running":
            return report
        report.update(status="error", reason="Runtime interrupted during sector execution", finished=time.time())
        for stage in report["stages"]:
            if stage["status"] == "running":
                stage.update(status="interrupted", finished=report["finished"])
                log = self.root / "runs" / job_id / stage["log"]
                if log.exists():
                    stage["log_sha256"] = sha256_hex(log.read_bytes())
        report["receipt_sha256"] = sha256_hex(canonical_bytes(report))
        self._save(report)
        self.ledger.append(event_type="braink.ci.completed", route="braink-node/ci",
                           payload={"job_id": job_id, "status": "error", "receipt_sha256": report["receipt_sha256"]})
        return report

    def read_log(self, job_id, stage):
        report = self.get(job_id)
        matches = [x for x in report["stages"] if x["name"] == stage]
        if not matches:
            raise ValueError("Unknown CI stage")
        path = self.root / "runs" / job_id / matches[0]["log"]
        if not path.exists():
            return ""
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 100_000))
            return stream.read().decode("utf-8", errors="replace")

    def worker(self, stop, poll_seconds=1):
        while not stop.is_set():
            if self.execute_next() is None:
                stop.wait(poll_seconds)
