"""Mechanism qualification derived from owner-supplied video visual captions.

Quantum: relative phase (~26-50s), controlled-X/Bell state (~54-62s).
Sparse: logical address map vs allocated disk (~38-62s), owner fold (~66-78s).
Recovery: decoupled lineage and fresh heap (~50-70s).
Audio was not transcribed; captions are sampled, not a complete transcript.
"""

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from braink.domain.dispatcher import WorkModule, WorkModuleDispatcher, ModuleType, DispatchState
from braink.runtime.circuit import simulate_circuit
from braink.runtime.continuation import ContinuationWorker, execute_pinned
from braink.runtime.sparse import SparseWorkspace
from braink.runtime.governance import consilience_sum, JITTER_LITERAL
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore, canonical_json


def test_phase_interference_and_imaginary_amplitudes():
    result = simulate_circuit({"qubits": 1, "gates": [
        {"op": "H", "target": 0}, {"op": "Z", "target": 0}, {"op": "H", "target": 0}]})
    assert result["probabilities"] == pytest.approx([0, 1])
    result = simulate_circuit({"qubits": 1, "gates": [
        {"op": "H", "target": 0}, {"op": "S", "target": 0}]})
    assert result["amplitudes"][1] == pytest.approx([0, math.sqrt(0.5)])


def test_bell_state_and_inverse():
    gates = [{"op": "H", "target": 0}, {"op": "CX", "control": 0, "target": 1}]
    assert simulate_circuit({"qubits": 2, "gates": gates})["probabilities"] == pytest.approx([.5, 0, 0, .5])
    assert simulate_circuit({"qubits": 2, "gates": gates + gates[::-1]})["probabilities"] == pytest.approx([1, 0, 0, 0])


@pytest.mark.parametrize("circuit", [
    {"qubits": True, "gates": []}, {"qubits": 17, "gates": []},
    {"qubits": 1, "gates": [{"op": "X", "target": 1}]},
    {"qubits": 1, "gates": [{"op": "CX", "target": 0, "control": 0}]},
    {"qubits": 1, "gates": [{"op": "EXEC", "target": 0}]},
    {"qubits": 16, "gates": [{"op": "X", "target": 0}] * 65},
])
def test_circuit_admission_limits(circuit):
    with pytest.raises(ValueError):
        simulate_circuit(circuit)


def test_real_dispatcher_circuit_execution():
    dispatcher = WorkModuleDispatcher({"statevector": simulate_circuit})
    module = WorkModule("circuit", ModuleType.RUNTIME, "Classical circuit", "Phase-preserving simulation",
                        {}, {}, [], "statevector", [])
    dispatcher.register_module(module)
    dispatcher.dispatch("bell", module, {"qubits": 2, "gates": [
        {"op": "H", "target": 0}, {"op": "CX", "target": 1, "control": 0}]})
    record = dispatcher.execute_dispatch("bell")
    assert record.state == DispatchState.COMPLETED
    assert record.output_data["probabilities"] == pytest.approx([.5, 0, 0, .5])


def test_sparse_capacity_holes_and_real_allocation(tmp_path):
    with SparseWorkspace(tmp_path / "scratch", 32 * 1024**3, 8192, lambda payload: 31 * 1024**3) as space:
        initial = space.usage()
        assert initial["logical_bytes"] == 32 * 1024**3
        assert initial["allocated_disk_bytes"] < initial["logical_bytes"]
        assert space.read(0, 32) == bytes(32)
        offset = space.write(b"owner payload")
        assert space.read(offset, 13) == b"owner payload"
        after = space.usage()
        assert after["written_bytes"] == 13
        assert after["allocated_disk_bytes"] >= initial["allocated_disk_bytes"]
        assert after["allocated_disk_bytes"] < after["logical_bytes"]


def test_sparse_existing_file_and_bad_fold_preserve_data(tmp_path):
    path = tmp_path / "owned"
    path.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        SparseWorkspace(path, 1024, 64, lambda _: 0)
    assert path.read_bytes() == b"original"
    with SparseWorkspace(tmp_path / "fresh", 1024, 64, lambda _: True) as space:
        with pytest.raises(ValueError):
            space.write(b"a")
        assert space.usage()["written_bytes"] == 0


def test_sparse_bounds_and_concurrent_budget(tmp_path):
    with SparseWorkspace(tmp_path / "bounded", 1024 * 1024, 8, lambda _: 0) as space:
        with pytest.raises(ValueError):
            space.read(0, 65537)
        with pytest.raises(ValueError):
            space.read(1024 * 1024, 1)
        def write(_):
            try:
                space.write(b"a")
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            assert sum(pool.map(write, range(32))) == 8
        assert space.usage()["written_bytes"] == 8
    with pytest.raises(ValueError):
        space.read(0, 1)


def input_store(tmp_path):
    store = VFSStore(tmp_path)
    request = {"qubits": 1, "gates": [{"op": "X", "target": 0}]}
    store.write(ArtifactWrite("/request", canonical_json(request), "owner://circuit"))
    return store


def test_fresh_worker_retry_after_new_parent_version(tmp_path):
    store = input_store(tmp_path)
    with ContinuationWorker(store) as worker:
        first = worker.execute("/request", 1, "work-1", "/result")
        store.write(ArtifactWrite("/request", canonical_json({"qubits": 1, "gates": []}), "owner://replacement"))
        with patch("braink.runtime.continuation.subprocess.Popen") as spawn:
            second = worker.execute("/request", 1, "work-1", "/result")
            spawn.assert_not_called()
        assert first == second
        assert first["output"]["probabilities"] == [0, 1]
        with pytest.raises(ValueError):
            worker.execute("/request", 2, "work-1", "/result")
    assert store.verify_receipt_chain()["count"] == 3


def test_concurrent_fresh_workers_one_result_receipt(tmp_path):
    store = input_store(tmp_path)
    with ContinuationWorker(store) as a, ContinuationWorker(VFSStore(tmp_path)) as b:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda i: (a if i % 2 else b).execute("/request", 1, "work", "/result"), range(4)))
    assert all(result == results[0] for result in results)
    assert store.verify_receipt_chain()["count"] == 2


def test_actual_worker_timeout_and_retry(tmp_path):
    store = input_store(tmp_path)
    with ContinuationWorker(store) as worker:
        with pytest.raises(TimeoutError):
            worker.execute("/request", 1, "work", "/result", timeout=.000001)
        with patch("braink.runtime.continuation.subprocess.Popen") as spawn:
            with pytest.raises(RuntimeError):
                worker.execute("/request", 1, "work", "/result")
            spawn.assert_not_called()
    # Explicit lifecycle replacement, rather than respawning inside a request.
    with ContinuationWorker(VFSStore(tmp_path)) as replacement:
        result = replacement.execute("/request", 1, "work", "/result")
    assert result["output"]["probabilities"] == [0, 1]
    assert store.verify_receipt_chain()["count"] == 2


def test_input_tamper_prevents_worker_launch(tmp_path):
    store = input_store(tmp_path)
    record = store.resolve_path("/request")
    with ContinuationWorker(store) as worker:
        store._object_path(record.digest).write_bytes(b"corrupt")
        with pytest.raises(RuntimeError):
            worker.execute("/request", 1, "work", "/result")
    assert store.resolve_path("/result") is None


def test_legacy_unreceipted_snapshot_cannot_authorize_work(tmp_path):
    store = input_store(tmp_path)
    with store._connect() as db:
        db.execute("DROP TABLE binding_history")
        db.execute("DROP TABLE continuations")
    with pytest.raises(ValueError):
        execute_pinned(VFSStore(tmp_path), "/request", 1, "work", "/result")


def test_actual_worker_exit_after_commit_and_failover(tmp_path):
    store = input_store(tmp_path)
    code = """import os,sys
from braink.runtime.continuation import execute_pinned
from vfs_server.store import VFSStore
execute_pinned(VFSStore(sys.argv[1]),'/request',1,'work','/result')
os._exit(74)
"""
    assert subprocess.run([sys.executable, "-c", code, str(tmp_path)], timeout=10).returncode == 74
    with ContinuationWorker(VFSStore(tmp_path)) as replacement:
        assert replacement.execute("/request", 1, "work", "/result")["output"]["probabilities"] == [0, 1]
    assert store.verify_receipt_chain()["count"] == 2


def test_empty_substrate_does_not_start_worker(tmp_path):
    with patch("braink.runtime.continuation.subprocess.Popen") as spawn:
        with pytest.raises(ValueError):
            ContinuationWorker(VFSStore(tmp_path))
        spawn.assert_not_called()


def test_distinct_requests_spawn_no_processes(tmp_path):
    store = input_store(tmp_path)
    with ContinuationWorker(store) as worker:
        pid = worker.process.pid
        with patch("braink.runtime.continuation.subprocess.Popen") as spawn:
            worker.execute("/request", 1, "first", "/first")
            worker.execute("/request", 1, "second", "/second")
            spawn.assert_not_called()
        assert worker.process.pid == pid
        assert worker.process.poll() is None
    assert store.verify_receipt_chain()["count"] == 3


def test_q32_warrant_arithmetic_preserves_levels_and_zero():
    assert JITTER_LITERAL == "0.297"
    assert consilience_sum([2, 3, 4])["sum_q32"] == 13649637264
    assert consilience_sum([4, 2, 3])["sum_q32"] == 13649637264
    assert consilience_sum([0, 4]) == {"input_levels": [0, 4], "sum_q32": None,
                                       "absorbing_zero": True, "scale": 4294967296}
    assert consilience_sum([1])["input_levels"] == [1]
    assert consilience_sum([1])["sum_q32"] == 0


def test_q32_warrant_domain_and_bounds():
    for levels in ([], [True], [1.0], [5], [-1], [4] * 4097):
        with pytest.raises(ValueError):
            consilience_sum(levels)
