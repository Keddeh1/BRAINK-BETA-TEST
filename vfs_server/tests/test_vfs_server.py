import base64,contextlib,io,json,tempfile,threading,unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from vfs_server.server import Handler,main
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore,sha256_bytes
from vfs_server.auth import MutationAuthorizer

class VFSServerTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.store=VFSStore(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_actor_and_observer_are_separate(self):
        rec,actor=self.store.write(ArtifactWrite("/runtime/a.txt",b"alpha","test"))
        self.assertEqual(rec.digest,sha256_bytes(b"alpha"))
        self.assertEqual(self.store.read_content(rec.digest),b"alpha")
        self.assertEqual(actor.kind,"VFS_ARTIFACT_WRITE")
        observed=self.store.verify(rec.digest)
        self.assertTrue(observed["verified"])
        self.assertEqual(observed["receipt"]["kind"],"OBSERVER_VFS_READBACK")
        self.assertNotEqual(actor.receipt_digest,observed["receipt"]["receipt_digest"])
    def test_lineage_and_path_resolution(self):
        a,_=self.store.write(ArtifactWrite("/a",b"a","test"))
        b,_=self.store.write(ArtifactWrite("/b",b"b","test",a.digest))
        self.assertEqual(self.store.resolve_path("/b").digest,b.digest)
        self.assertEqual(self.store.lineage(b.digest)[0]["parent_digest"],a.digest)
    def test_receipt_chain_survives_restart(self):
        rec,_=self.store.write(ArtifactWrite("/chain",b"chain","test"))
        self.store.verify(rec.digest)
        reopened=VFSStore(self.tmp.name)
        self.assertTrue(reopened.verify_receipt_chain()["verified"])
    def test_authorizer(self):
        self.assertTrue(MutationAuthorizer().allowed(None))
    def test_http_auth_write_and_observer_readback(self):
        token_file=self.tmp.name+"/token"
        with open(token_file,"w",encoding="utf-8") as stream: stream.write("test-only-secret")
        Handler.store=self.store
        Handler.authorizer=MutationAuthorizer(token_file)
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url="http://127.0.0.1:"+str(server.server_port)
        def request(path,method="GET",payload=None,authorized=False):
            headers={"Content-Type":"application/json"}
            if authorized: headers["Authorization"]="Bearer test-only-secret"
            data=None if payload is None else json.dumps(payload).encode()
            return urlopen(Request(url+path,data=data,method=method,headers=headers),timeout=3)
        try:
            body={"path":"/runtime/http.txt","content_b64":base64.b64encode(b"through-host").decode(),"source":"http-test"}
            with self.assertRaises(HTTPError) as error:request("/artifacts","POST",body)
            self.assertEqual(error.exception.code,401)
            with request("/artifacts","POST",body,True) as response:
                created=json.load(response)
            self.assertEqual(created["verification"],"PENDING_OBSERVER_READBACK")
            digest=created["artifact"]["digest"]
            with self.assertRaises(HTTPError) as error:request("/artifacts/"+digest)
            self.assertEqual(error.exception.code,401)
            with request("/artifacts/"+digest,authorized=True) as response:
                observed=json.load(response)
            self.assertEqual(base64.b64decode(observed["content_b64"]),b"through-host")
            with request("/verify","POST",{"digest":digest},True) as response:
                verified=json.load(response)
            self.assertTrue(verified["verified"])
            self.assertEqual(verified["receipt"]["kind"],"OBSERVER_VFS_READBACK")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

    def test_external_listener_requires_token_file(self):
        with patch("sys.argv",["vfs-server","--host","0.0.0.0"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:main()
        self.assertEqual(error.exception.code,2)

    def test_unknown_predecessor_fails(self):
        with self.assertRaises(ValueError):
            self.store.write(ArtifactWrite("/x",b"x","test","0"*64))
if __name__=="__main__":unittest.main()
