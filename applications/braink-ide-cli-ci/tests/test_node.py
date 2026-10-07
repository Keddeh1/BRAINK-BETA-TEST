import contextlib
import io
import json
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from braink_node.align import align_project_into_dekstop, _path_hash
from braink_node.canonical import canonical_bytes, sha256_hex
from braink_node.cli import main, services
from braink_node.ide import make_server, workspace_file
from braink_node.indexer import build_interlink_index, ledger_index, write_index_artifact, _stable_hash_text
from braink_node.ingest import (_read_bytes, artifact_ref_for_path, ingest_directory,
                                ingest_file, iter_files, store_artifact_bytes, IngestedFile)
from braink_node.ledger import LedgerStore
from braink_node.pass_runner import run_dekstop_pass, _read_json, _finding_id, _discover_projects
from braink_node.paths import default_dekstop_paths
from braink_node.plan import PlanningPacket
from braink_node.registry import ProjectEntry, load_registry, store_registry, upsert_project
from braink_node.result import ExecutionResult


class NodeFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "workspace"
        self.root.mkdir()
        self.paths, self.store, self.artifacts = services(self.root, self.base / "state")

    def file(self, name, data=b"hello"):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def check(self, **kwargs):
        return run_dekstop_pass(store=self.store, dekstop=self.paths, artifacts_dir=self.artifacts,
                                pass_route="test", **kwargs)


class NodeTests(NodeFixture, unittest.TestCase):
    def test_canonical_and_hash_helpers(self):
        self.assertEqual(canonical_bytes({"b": 1, "a": 2}), canonical_bytes({"a": 2, "b": 1}))
        self.assertEqual(_stable_hash_text("hello"), _path_hash("hello"))
        with self.assertRaises(ValueError):
            canonical_bytes({"x": float("nan")})

    def test_paths_are_explicit(self):
        self.assertEqual(self.paths.root, self.root)
        self.assertEqual(default_dekstop_paths(self.root).interconnect_root,
                         self.root / "K_SYSTEM_INTERCONNECT")

    def test_registry_create_upsert_preserves_extensions(self):
        path = self.base / "new" / "registry.json"
        self.assertEqual(load_registry(path), {"projects": []})
        original = {"projects": [{"project_id": "p", "name": "old", "path": "abc",
                                  "kind": "python", "custom": 42}], "sector": "apps"}
        result = upsert_project(original, ProjectEntry("p", "new", "abc", "python"))
        self.assertEqual(original["projects"][0]["name"], "old")
        self.assertEqual(result["projects"][0]["custom"], 42)
        store_registry(path, result)
        self.assertEqual(load_registry(path), result)
        result = upsert_project(result, ProjectEntry("q", "other", "xyz", "python"))
        self.assertEqual(len(result["projects"]), 2)

    def test_registry_invalid_shapes(self):
        for obj in ([], {"projects": None}, {"projects": [1]},
                    {"projects": [{"project_id": "p"}]}):
            with self.subTest(obj=obj), self.assertRaises(ValueError):
                store_registry(self.base / "bad.json", obj)

    def test_alignment_idempotence(self):
        project = self.root / "projects" / "demo"
        project.mkdir(parents=True)
        kwargs = dict(store=self.store, dekstop=self.paths, project_name="demo", project_path=project)
        first = align_project_into_dekstop(**kwargs)
        second = align_project_into_dekstop(**kwargs)
        self.assertTrue(first.registry_updated)
        self.assertFalse(second.registry_updated)
        self.assertEqual(first.project_id, second.project_id)
        self.assertEqual(self.store.verify()["event_count"], 2)

    def test_alignment_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            align_project_into_dekstop(store=self.store, dekstop=self.paths,
                                       project_name="missing", project_path=self.root / "missing")

    def test_alignment_concurrent_updates_are_retained(self):
        errors = []
        def align(i):
            try:
                path = self.root / "projects" / str(i)
                path.mkdir(parents=True, exist_ok=True)
                align_project_into_dekstop(store=self.store, dekstop=self.paths,
                                           project_name=str(i), project_path=path)
            except Exception as error:
                errors.append(error)
        threads = [threading.Thread(target=align, args=(i,)) for i in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(load_registry(self.paths.unified_project_registry_json)["projects"]), 8)

    def test_deterministic_traversal_and_limits(self):
        for name in ("z.py", "a.py", "d/c.py", ".hidden/x.py", "__pycache__/x.py"):
            self.file(name)
        self.assertEqual([p.relative_to(self.root).as_posix() for p in iter_files(self.root)],
                         ["a.py", "z.py", "d/c.py"])
        self.assertEqual(list(iter_files(self.root, max_files=0)), [])
        self.assertEqual(len(list(iter_files(self.root, max_files=1))), 1)
        with self.assertRaises(ValueError):
            list(iter_files(self.root, max_files=-1))

    def test_symlinks_not_ingested(self):
        external = self.base / "secret"
        external.write_text("secret")
        (self.root / "link").symlink_to(external)
        self.assertEqual(list(iter_files(self.root)), [])
        with self.assertRaises(ValueError):
            ingest_file(store=self.store, file_path=self.root / "link",
                         artifacts_dir=self.artifacts, route="test")

    def test_index_repeatable_and_self_exclusion(self):
        self.file("a.txt")
        self.assertEqual(build_interlink_index(dekstop_root=self.root, max_entries=0).entries, [])
        inside = self.root / "artifacts"
        one = ledger_index(store=self.store, dekstop_root=self.root, artifacts_dir=inside, route="test")
        two = ledger_index(store=self.store, dekstop_root=self.root, artifacts_dir=inside, route="test")
        self.assertEqual(one["artifact_ref"], two["artifact_ref"])
        self.assertEqual(two["entry_count"], 1)
        obj = build_interlink_index(dekstop_root=self.root, excluded_roots=(inside,)).to_obj()
        self.assertEqual(write_index_artifact(artifacts_dir=inside, index_obj=obj), one["artifact_ref"])

    def test_artifact_integrity(self):
        data = b"artifact"
        ref = sha256_hex(data)
        path = store_artifact_bytes(artifacts_dir=self.artifacts, artifact_ref=ref, data=data)
        self.assertEqual(store_artifact_bytes(artifacts_dir=self.artifacts, artifact_ref=ref, data=data), path)
        with self.assertRaises(ValueError):
            store_artifact_bytes(artifacts_dir=self.artifacts, artifact_ref="../bad", data=data)
        path.write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            store_artifact_bytes(artifacts_dir=self.artifacts, artifact_ref=ref, data=data)

    def test_large_file_rejected_without_false_capture(self):
        path = self.file("big", b"12345")
        self.assertEqual(_read_bytes(path, 5), b"12345")
        with self.assertRaises(ValueError):
            ingest_file(store=self.store, file_path=path, artifacts_dir=self.artifacts,
                         route="test", max_artifact_bytes=4)
        self.assertEqual(self.store.verify()["event_count"], 0)
        self.assertEqual(artifact_ref_for_path(path), sha256_hex(b"12345"))

    def test_ingestion_pagination(self):
        for name in ("z", "a", "b"):
            self.file(name)
        result = ingest_directory(store=self.store, directory=self.root, artifacts_dir=self.artifacts,
                                   route="test", max_files=1, offset=1)
        self.assertEqual(result["summary"]["files"][0]["rel_path"], "b")
        self.assertEqual(self.store.verify()["event_count"], 2)
        self.assertEqual(IngestedFile("a", "a", 0, "ref").to_obj()["size"], 0)
        with self.assertRaises(ValueError):
            ingest_directory(store=self.store, directory=self.root, artifacts_dir=self.artifacts,
                              route="test", offset=-1)

    def test_ingestion_excludes_own_state(self):
        self.file("data")
        store = LedgerStore(self.root / ".state" / "ledger.sqlite3")
        artifacts = self.root / "artifacts"
        for _ in range(2):
            result = ingest_directory(store=store, directory=self.root, artifacts_dir=artifacts, route="test")
            self.assertEqual(result["summary"]["count"], 1)

    def test_pass_missing_root(self):
        self.root.rmdir()
        self.assertEqual(self.check()["findings"][0]["severity"], "blocker")

    def test_pass_malformed_json_and_schema(self):
        for raw in ("broken", "[]", '{"projects":null}', '{"projects":[1]}'):
            self.file("K_SYSTEM_INTERCONNECT/UNIFIED_PROJECT_REGISTRY.json", raw.encode())
            self.assertTrue(any(f["severity"] == "blocker" for f in self.check()["findings"]))
        self.file("K_SYSTEM_INTERCONNECT/INTERCONNECT_STATUS.json", b"[]")
        self.assertIsNone(_read_json(self.paths.interconnect_status_json))
        self.assertIsNone(_read_json(self.root / "missing"))

    def test_pass_project_discovery_and_ingestion(self):
        self.file("projects/demo/main.py")
        self.file("projects/.hidden/main.py")
        store_registry(self.paths.unified_project_registry_json, {"projects": []})
        self.file("K_SYSTEM_INTERCONNECT/INTERCONNECT_STATUS.json", b'{"status":"ready"}')
        self.assertEqual([p.name for p in _discover_projects(self.root)], ["demo"])
        result = self.check(ingest_dekstop_root=True)
        self.assertTrue(any("missing from registry" in f["title"] for f in result["findings"]))
        self.assertEqual(_finding_id("a", {"b": 2, "a": 1}), _finding_id("a", {"a": 1, "b": 2}))

    def test_packet_validation_and_export_isolation(self):
        packet = PlanningPacket("edit", {"a": 1}, [], [], [])
        export = packet.to_obj()
        export["scope"]["a"] = 2
        self.assertEqual(packet.scope["a"], 1)
        with self.assertRaises(ValueError):
            PlanningPacket("", {}, [], [], [])
        with self.assertRaises(ValueError):
            PlanningPacket("edit", {}, [1], [], [])
        result = ExecutionResult(True, None, {"x": 1}, [])
        result.to_obj()["outputs"]["x"] = 2
        self.assertEqual(result.outputs["x"], 1)
        with self.assertRaises(ValueError):
            ExecutionResult("yes", None, {}, [])

    def test_ledger_concurrent_append_and_tamper_detection(self):
        threads = [threading.Thread(target=lambda: self.store.append(event_type="test", route="test", payload={})) for _ in range(12)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(self.store.verify()["event_count"], 12)
        with sqlite3.connect(self.store.path) as db:
            db.execute("UPDATE events SET body='{}' WHERE sequence=1")
        with self.assertRaises(ValueError): self.store.verify()

    def test_cli_lifecycle_and_exit_codes(self):
        args = ["--workspace", str(self.root), "--state-dir", str(self.base / "state")]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ["init"]), 0)
            self.assertEqual(main(args + ["check", "--fail-on", "warn"]), 0)
            self.file("projects/demo/a.py")
            self.assertEqual(main(args + ["check", "--fail-on", "warn"]), 1)
            self.assertEqual(main(args + ["align", str(self.root / "projects/demo"), "--name", "demo"]), 0)
            self.assertEqual(main(args + ["check", "--fail-on", "warn", "--ingest"]), 0)
            self.assertEqual(main(args + ["index"]), 0)
            self.assertEqual(main(args + ["ingest", str(self.root / "projects/demo/a.py")]), 0)
            self.assertEqual(main(args + ["ingest", str(self.root / "projects/demo")]), 0)
            self.assertEqual(main(args + ["verify-ledger"]), 0)
            self.assertEqual(main(args + ["index", "--max-entries", "-1"]), 2)


class IdeTests(NodeFixture, unittest.TestCase):
    def start(self, token="test-token"):
        server = make_server(paths=self.paths, store=self.store, artifacts_dir=self.artifacts,
                              host="127.0.0.1", port=0, token=token)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.url = f"http://127.0.0.1:{server.server_port}"

    def request(self, route, body=None, token="test-token"):
        req = urllib.request.Request(self.url + route,
                                      data=json.dumps(body).encode() if body is not None else None,
                                      headers={"Authorization": "Bearer " + token,
                                               "Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if "json" in response.headers["Content-Type"] else raw

    def test_ide_load_save_conflict_and_provenance(self):
        self.file("projects/demo.py", b"before")
        self.start()
        self.assertEqual(self.request("/")[0], 200)
        self.assertEqual(self.request("/health", token="")[0], 200)
        self.assertEqual(self.request("/api/files", token="wrong")[0], 401)
        self.assertIn("projects/demo.py", self.request("/api/files")[1]["files"])
        _, file = self.request("/api/file?path=projects/demo.py")
        body = {"path": file["path"], "content": "after", "revision": file["revision"]}
        self.assertEqual(self.request("/api/file", body)[0], 200)
        self.assertEqual(self.request("/api/file", body)[0], 409)
        self.assertEqual(self.artifacts.joinpath(sha256_hex(b"before")).read_bytes(), b"before")
        self.assertEqual(self.request("/api/ledger")[1]["event_count"], 2)
        self.assertEqual(self.request("/api/check", {})[0], 200)
        self.assertEqual(self.request("/api/index", {})[0], 200)

    def test_ide_path_containment_and_remote_auth(self):
        for name in ("../escape", "/absolute", ".hidden"):
            with self.assertRaises(ValueError): workspace_file(self.root, name)
        (self.root / "link").symlink_to(self.base)
        with self.assertRaises(ValueError): workspace_file(self.root, "link/file")
        with self.assertRaises(ValueError):
            make_server(paths=self.paths, store=self.store, artifacts_dir=self.artifacts,
                         host="0.0.0.0", port=0, token="")
        self.start()
        self.assertEqual(self.request("/api/file", {"path": "../bad", "content": "bad"})[0], 400)


if __name__ == "__main__":
    unittest.main()
