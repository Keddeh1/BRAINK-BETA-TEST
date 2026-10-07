import base64,contextlib,io,json,tempfile,threading,unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from vfs_server.server import Handler,main
from vfs_server.model import ArtifactWrite
from vfs_server.store import VFSStore,sha256_bytes
from vfs_server.fleet import VFSFleet
from vfs_server.auth import MutationAuthorizer

class VFSServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=VFSStore(self.tmp.name+"/legacy")
        self.fleet=VFSFleet(self.tmp.name+"/fleet")
    def tearDown(self): self.tmp.cleanup()
    def test_store_actor_and_observer_are_separate(self):
        rec,actor=self.store.write(ArtifactWrite("/runtime/a.txt",b"alpha","test"))
        self.assertEqual(rec.digest,sha256_bytes(b"alpha"))
        observed=self.store.verify(rec.digest)
        self.assertTrue(observed["verified"])
        self.assertNotEqual(actor.receipt_digest,observed["receipt"]["receipt_digest"])
        self.assertTrue(self.store.verify_receipt_chain()["verified"])
    def test_allocation_isolation_and_ab_reconstruction(self):
        one=self.fleet.allocate("workflow one","queue#3")
        two=self.fleet.allocate("workflow two","queue#4")
        result=self.fleet.admit_ab(one["vfs_id"],b"baseline "*100,b"candidate "*100,"queue#3")
        entry=result["entry"]
        self.assertEqual(entry["b_codec"],"zlib")
        self.assertLess(entry["stored_bytes"],entry["a_bytes"]+entry["b_bytes"])
        verified=self.fleet.read_ab(one["vfs_id"],entry["entry_id"],observe=True)
        self.assertTrue(verified["verified"])
        self.assertEqual(base64.b64decode(verified["a_b64"]),b"baseline "*100)
        self.assertEqual(base64.b64decode(verified["b_b64"]),b"candidate "*100)
        self.assertEqual(len(verified["observer_receipts"]),2)
        self.assertTrue(self.fleet.store(one["vfs_id"]).verify_receipt_chain()["verified"])
        with self.assertRaises(KeyError): self.fleet.entry(two["vfs_id"],entry["entry_id"])
        restarted=VFSFleet(self.tmp.name+"/fleet")
        self.assertEqual(restarted.read_ab(one["vfs_id"],entry["entry_id"])["entry"],entry)
    def test_identical_b_is_reference_and_quota_is_enforced(self):
        instance=self.fleet.allocate("dedup","queue#5",quota_bytes=32*1024*1024)
        pair=self.fleet.admit_ab(instance["vfs_id"],b"same",b"same","queue#5")
        self.assertEqual(pair["entry"]["b_codec"],"reference:A")
        self.assertEqual(len(pair["actor_receipts"]),1)
        with patch("vfs_server.fleet.zlib.compress",side_effect=lambda value,level=9:value):
            with self.assertRaisesRegex(ValueError,"vfs_quota_exceeded"):
                self.fleet.admit_ab(instance["vfs_id"],b"x"*(32*1024*1024),b"y","queue#5")
    def test_http_auth_allocation_ab_and_observer(self):
        token_file=self.tmp.name+"/token"
        with open(token_file,"w",encoding="utf-8") as stream: stream.write("test-only-secret")
        Handler.fleet=self.fleet
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
            with self.assertRaises(HTTPError) as error: request("/vfs","POST",{"label":"x","source_ref":"queue#3"})
            self.assertEqual(error.exception.code,401)
            with request("/vfs","POST",{"label":"workflow","source_ref":"queue#3"},True) as response:
                allocation=json.load(response)["allocation"]
            ident=allocation["vfs_id"]
            body={"a_b64":base64.b64encode(b"alpha").decode(),
                  "b_b64":base64.b64encode(b"beta").decode(),"source_ref":"queue#3"}
            with request("/vfs/"+ident+"/ab","POST",body,True) as response:
                admitted=json.load(response)
            entry=admitted["entry"]["entry_id"]
            self.assertEqual(admitted["verification"],"PENDING_OBSERVER_READBACK")
            with request("/vfs/"+ident+"/ab/"+entry+"/verify","POST",{},True) as response:
                verified=json.load(response)
            self.assertTrue(verified["verified"])
            self.assertEqual(base64.b64decode(verified["b_b64"]),b"beta")
            self.assertEqual(verified["service_environment"]["classification"],"KEDDEH_SERVICE")
            with self.assertRaises(HTTPError) as error: request("/artifacts/raw","POST",{},True)
            self.assertEqual(error.exception.code,410)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
    def test_external_listener_requires_token_file(self):
        with patch("sys.argv",["vfs-server","--host","0.0.0.0"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error: main()
        self.assertEqual(error.exception.code,2)
if __name__=="__main__": unittest.main()
