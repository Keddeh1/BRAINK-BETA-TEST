import unittest
import json
import threading
import urllib.request
import urllib.error
from fixtures import NodeFixture
from braink_ide.ide import make_server, workspace_file
from braink_node.canonical import sha256_hex

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
