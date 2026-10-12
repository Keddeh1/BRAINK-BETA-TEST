"""HTTP security boundary tests: unauthorized requests cannot mutate storage."""
import base64
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from vfs_server.auth import MutationAuthorizer
from vfs_server.server import Handler
from vfs_server.store import VFSStore


class VFSHTTPAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        # Bind instance attributes to avoid class-wide shared mutable state.
        self.server.RequestHandlerClass = type("IsolatedHandler", (Handler,), {
            "store": VFSStore(self.tmp.name),
            "authorizer": MutationAuthorizer(),
        })
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def post(self, route, payload, token=None):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        req = Request(self.base + route, data=json.dumps(payload).encode(),
                      headers=headers, method="POST")
        try:
            with urlopen(req, timeout=3) as r:
                return r.status, json.load(r)
        except HTTPError as e:
            return e.code, json.load(e)

    def test_unauthenticated_write_is_rejected_without_effect(self):
        status, response = self.post("/artifacts", {
            "path": "/unauthorized",
            "content_b64": base64.b64encode(b"data").decode(),
            "source": "test",
        })
        self.assertEqual(status, 401)
        self.assertEqual(response["error"], "unauthorized")
        self.assertIsNone(self.server.RequestHandlerClass.store.resolve_path("/unauthorized"))

    def test_unauthenticated_verify_is_rejected(self):
        status, _ = self.post("/verify", {"digest": "0" * 64})
        self.assertEqual(status, 401)

    def test_authorized_write_and_readback(self):
        self.server.RequestHandlerClass.authorizer = MutationAuthorizer.__new__(MutationAuthorizer)
        self.server.RequestHandlerClass.authorizer.token = "test-token"
        self.server.RequestHandlerClass.authorizer.insecure_local_dev = False
        status, result = self.post("/artifacts", {
            "path": "/authorized",
            "content_b64": base64.b64encode(b"payload").decode(),
            "source": "test",
        }, token="test-token")
        self.assertEqual(status, 201)
        self.assertEqual(result["verification"], "PENDING_OBSERVER_READBACK")
        self.assertEqual(self.server.RequestHandlerClass.store.resolve_path("/authorized").path, "/authorized")


if __name__ == "__main__":
    unittest.main()
