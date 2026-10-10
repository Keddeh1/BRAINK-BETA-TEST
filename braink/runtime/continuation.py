"""Persistent pure-work execution anchored to verified contextual VFS history.

Startup creates a fresh interpreter after a local ledger check. Requests never
spawn a process. Explicit lifecycle replacement handles uncertain worker failure.
This local ledger check does not stand in for ServerSpace's SHM handshake.
"""

import argparse
import json
import os
import select
import subprocess
import sys
import time
from threading import Lock
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore, canonical_json, normalize_vfs_path
from .circuit import simulate_circuit


class ContinuationRejected(ValueError):
    """A complete worker rejection, distinct from an uncertain protocol failure."""


def _input(store, path, version):
    if type(version) is not int or version < 1:
        raise ValueError("positive binding version required")
    history = store.binding_history(path)
    if version > len(history):
        raise ValueError("binding version missing")
    binding = history[version - 1]
    if binding["origin"] != "COMMITTED_WRITE" or not binding["receipt_id"]:
        raise ValueError("unreceipted legacy context cannot authorize execution")
    payload = store.read_content(binding["artifact"]["digest"])
    if len(payload) > 1024 * 1024:
        raise ValueError("circuit input exceeds budget")
    request = json.loads(payload)
    if type(request) is not dict:
        raise ValueError("circuit request requires a mapping")
    return binding, request


def execute_pinned(store, path, version, continuation_id, result_path):
    binding, request = _input(store, path, version)
    output = simulate_circuit(request)
    source = "binding://" + binding["binding_digest"]
    return store.write(ArtifactWrite(result_path, canonical_json(output), source,
                                    binding["artifact"]["digest"], "application/json",
                                    continuation_id, 0))


class ContinuationWorker:
    """Explicit startup/shutdown; one worker is reused across all requests.

    A timeout quarantines the worker. The caller replaces it through the lifecycle,
    then reuses the same continuation to reconcile an ambiguous durable commit.
    Supports pure deterministic circuit work only, never arbitrary side effects.
    """
    def __init__(self, store):
        chain = store.verify_receipt_chain()
        if not chain["verified"] or chain["count"] == 0:
            raise ValueError("committed substrate required before worker startup")
        self.store = store
        self.lock = Lock()
        self.halted = False
        self.process = subprocess.Popen([
            sys.executable, "-m", "braink.runtime.continuation", "--root", str(store.root.resolve())
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            if self._receive(30) != {"ready": True}:
                raise RuntimeError("worker substrate handshake failed")
        except BaseException:
            self.halted = True
            self._stop()
            raise

    def _receive(self, timeout):
        deadline = time.monotonic() + timeout
        reply = b""
        while not reply.endswith(b"\n"):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError("worker result uncertain; reconcile continuation")
            chunk = os.read(self.process.stdout.fileno(), 1024)
            if not chunk or len(reply) + len(chunk) > 1024:
                raise RuntimeError("worker reply invalid")
            reply += chunk
        return json.loads(reply)

    def execute(self, path, version, continuation_id, result_path, timeout=30):
        if type(timeout) not in (int, float) or not 0 < timeout <= 300:
            raise ValueError("invalid worker timeout")
        binding, _ = _input(self.store, path, version)
        result_path = normalize_vfs_path(result_path)
        if type(continuation_id) is not str or not 0 < len(continuation_id) <= 128:
            raise ValueError("invalid continuation identity")
        message = canonical_json({"path": binding["artifact"]["path"], "version": version,
                                  "continuation_id": continuation_id, "result_path": result_path}) + b"\n"
        with self.lock:
            if self.halted or self.process.poll() is not None:
                raise RuntimeError("worker halted; lifecycle replacement required")
            try:
                self.process.stdin.write(message)
                self.process.stdin.flush()
                response = self._receive(timeout)
                if response == {"ok": False}:
                    raise ContinuationRejected("continuation rejected")
                if response != {"ok": True}:
                    raise RuntimeError("worker reply invalid")
                history = self.store.binding_history(result_path)
                if len(history) != 1:
                    raise RuntimeError("result context changed")
                result = history[0]
                if result["artifact"]["source"] != "binding://" + binding["binding_digest"]:
                    raise RuntimeError("result input binding mismatch")
                record, receipt = self.store.write(ArtifactWrite(
                    result_path, self.store.read_content(result["artifact"]["digest"]),
                    result["artifact"]["source"], binding["artifact"]["digest"], "application/json",
                    continuation_id, 0))
                return {"artifact": record.as_dict(), "receipt": receipt.as_dict(),
                        "output": json.loads(self.store.read_content(record.digest))}
            except ContinuationRejected:
                # A complete rejection reply leaves the worker's protocol synchronized.
                raise
            except BaseException:
                self.halted = True
                self._stop()
                raise

    def _stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()

    def close(self):
        with self.lock:
            self.halted = True
            self._stop()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    store = VFSStore(args.root)
    chain = store.verify_receipt_chain()
    if not chain["verified"] or not chain["count"]:
        return 1
    print(json.dumps({"ready": True}), flush=True)
    while True:
        line = sys.stdin.buffer.readline(16385)
        if not line:
            return 0
        if len(line) > 16384 or not line.endswith(b"\n"):
            return 1
        try:
            request = json.loads(line)
            execute_pinned(store, **request)
            response = {"ok": True}
        except Exception:
            response = {"ok": False}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    sys.exit(main())
