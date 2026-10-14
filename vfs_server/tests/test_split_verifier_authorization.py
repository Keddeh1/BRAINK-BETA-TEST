"""HTTP regression: writer and verifier capabilities must not overlap."""
import base64
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from vfs_server.auth import MutationAuthorizer
from vfs_server.server import Handler
from vfs_server.store import VFSStore


class SplitVerifierAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        writer = root / "writer.token"
        verifier = root / "verifier.token"
        writer.write_text("writer-only-token")
        verifier.write_text("verifier-only-token")
        self.handler = type("IsolatedSecurityHandler", (Handler,), {
            "store": VFSStore(root / "data"),
            "authorizer": MutationAuthorizer(str(writer)),
            "verifier_authorizer": MutationAuthorizer(str(verifier)),
        })
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def post(self, path, data, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.url + path, data=json.dumps(data).encode(),
                          headers=headers, method="POST")
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_writer_cannot_self_verify_and_verifier_cannot_write(self):
        payload = {"path": "/controlled", "content_b64": base64.b64encode(b"test").decode(),
                   "source": "actor"}
        status, written = self.post("/artifacts", payload, "writer-only-token")
        self.assertEqual(status, 201)
        digest = written["artifact"]["digest"]
        self.assertEqual(self.post("/verify", {"digest": digest}, "writer-only-token")[0], 401)
        self.assertEqual(self.post("/artifacts", payload, "verifier-only-token")[0], 401)
        self.assertEqual(self.post("/verify", {"digest": digest})[0], 401)
        verified_status, verified = self.post("/verify", {"digest": digest}, "verifier-only-token")
        self.assertEqual(verified_status, 200)
        self.assertTrue(verified["verified"])
        self.assertEqual(self.handler.store.read_content(digest), b"test")


if __name__ == "__main__":
    unittest.main()
