import contextlib,hashlib,hmac,io,json,secrets,tempfile,threading,time,unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from unittest.mock import patch
from vfs_server.auth import MutationAuthorizer
from vfs_server.codec import encode,decode,graph
from vfs_server.fleet import VFSFleet
from vfs_server.model import ArtifactWrite
from vfs_server.server import Handler,main
from vfs_server.store import VFSStore,sha256_bytes

class VFSContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fleet=VFSFleet(self.temp.name+"/fleet")
    def test_binary_codec_and_implicit_origin(self):
        for size in range(1,10):
            for pattern in range(1<<size):
                bits=format(pattern,f"0{size}b")
                packed=encode(bits)
                self.assertEqual(decode(packed,size),bits)
                mapped=graph(packed,size)
                self.assertEqual(mapped["origin"],{"from":1,"to":2,"powered":True,"addressable":False})
                self.assertEqual([m["address"] for m in mapped["mappings"]],list(range(2,size+2)))
        with self.assertRaises(ValueError):decode(b"\xff",1)
    def test_allocation_reversible_state_and_isolation(self):
        one=self.fleet.allocate("one","queue#3",quota_bytes=2)
        two=self.fleet.allocate("two","queue#4")
        self.assertEqual(len(one["vfs_id"]),64)
        admitted=self.fleet.admit_ab(one["vfs_id"],"101010101","queue#3")
        entry=admitted["entry"]
        self.assertEqual(entry["packed_bytes"],2)
        self.assertEqual(admitted["verification"],"PENDING_OBSERVER_READBACK")
        self.assertEqual(self.fleet.read_ab(one["vfs_id"],entry["entry_id"],observe=True)["proof"]["bits"],"101010101")
        self.assertTrue(self.fleet.store(one["vfs_id"]).verify_receipt_chain()["verified"])
        with self.assertRaises(KeyError):self.fleet.entry(two["vfs_id"],entry["entry_id"])
        with self.assertRaisesRegex(ValueError,"vfs_quota_exceeded"):
            self.fleet.admit_ab(one["vfs_id"],"101010101","queue#3")
        reopened=VFSFleet(self.temp.name+"/fleet")
        self.assertEqual(reopened.read_ab(one["vfs_id"],entry["entry_id"])["proof"]["bits"],"101010101")
    def test_storage_receipt_and_restart(self):
        store=VFSStore(self.temp.name+"/standalone")
        record,actor=store.write(ArtifactWrite("/runtime/a",b"alpha","test"))
        self.assertEqual(record.digest,sha256_bytes(b"alpha"))
        observer=store.verify(record.digest)
        self.assertNotEqual(actor.receipt_digest,observer["receipt"]["receipt_digest"])
        self.assertTrue(VFSStore(self.temp.name+"/standalone").verify_receipt_chain()["verified"])
    def test_http_surface_scope_signature_and_replay(self):
        token_file=self.temp.name+"/token"
        with open(token_file,"w",encoding="utf-8") as out:out.write("owner-secret")
        Handler.fleet=self.fleet
        Handler.authorizer=MutationAuthorizer(token_file)
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        self.addCleanup(lambda:(server.shutdown(),server.server_close(),worker.join(timeout=3)))
        base="http://127.0.0.1:"+str(server.server_port)
        def request(path,method="GET",obj=None,headers=None,owner=True):
            data=None if obj is None else json.dumps(obj,separators=(",",":")).encode()
            supplied={"Content-Type":"application/json",**({"Authorization":"Bearer owner-secret"} if owner else {}),**(headers or {})}
            return urlopen(Request(base+path,data=data,method=method,headers=supplied),timeout=3)
        def signed(secret,path,body,command,nonce=None):
            payload=json.dumps(body,separators=(",",":")).encode()
            at=str(int(time.time()))
            nonce=nonce or secrets.token_hex(16)
            message="|".join(("POST",path,"site-runtime",hashlib.sha256(payload).hexdigest(),at,nonce,command)).encode()
            sig=hmac.new(bytes.fromhex(secret),message,hashlib.sha256).hexdigest()
            return {"X-VFS-Surface":"site-runtime","X-VFS-Time":at,
                    "X-VFS-Nonce":nonce,"X-VFS-Signature":sig}
        with request("/vfs","POST",{"label":"workflow","source_ref":"queue#3"}) as response:
            allocation=json.load(response)["allocation"]
        ident=allocation["vfs_id"]
        path=f"/vfs/{ident}/ab"
        body={"bits":"101010101","source_ref":"queue#3"}
        with self.assertRaises(HTTPError) as denied:
            request(path,"POST",body)
        self.assertEqual(denied.exception.code,403)
        with request(f"/vfs/{ident}/surfaces","POST",
                     {"surface_id":"site-runtime","commands":["ab.admit","ab.observe"]}) as response:
            secret=json.load(response)["actuator_secret"]
        proof=signed(secret,path,body,"ab.admit")
        with self.assertRaises(HTTPError) as invalid:
            request(path,"POST",body,{**proof,"X-VFS-Signature":"0"*64})
        self.assertEqual(invalid.exception.code,403)
        with request(path,"POST",body,proof) as response:
            created=json.load(response)
        self.assertEqual(created["entry"]["codec"],"KEDDEH_AB_BINARY_V1")
        entry=created["entry"]["entry_id"]
        with self.assertRaises(HTTPError) as replay:
            request(path,"POST",body,proof)
        self.assertEqual(replay.exception.code,409)
        with request(f"{path}/{entry}") as response:
            self.assertEqual(json.load(response)["proof"]["bits"],body["bits"])
        observe=f"{path}/{entry}/verify"
        with request(observe,"POST",{},signed(secret,observe,{},"ab.observe")) as response:
            self.assertTrue(json.load(response)["verified"])
        with self.assertRaises(HTTPError) as ownerless:
            request(f"{path}/{entry}",owner=False)
        self.assertEqual(ownerless.exception.code,401)
        with self.assertRaises(HTTPError) as retired:
            request("/artifacts/raw","POST",{})
        self.assertEqual(retired.exception.code,410)
    def test_external_listener_requires_token(self):
        with patch("sys.argv",["vfs-server","--host","0.0.0.0"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:main()
        self.assertEqual(result.exception.code,2)

if __name__=="__main__":unittest.main()
