"""HTTP carrier for an allocated fleet of VFS instances and A/B admissions."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
import argparse,json,re
from .fleet import VFSFleet
from .auth import MutationAuthorizer

MAX_REQUEST_BYTES=16*1024
VFS_ID="[0-9a-f]{64}"
ENTRY_ID="[0-9a-f]{32}"

class Handler(BaseHTTPRequestHandler):
    fleet=None
    authorizer=MutationAuthorizer()
    service_environment={"classification":"KEDDEH_SERVICE","system":"KEDDEH_SYSTEMS",
                         "subsystem":"VFS_SERVER","carrier_id":"VFS_SERVER:loopback","transport":"HTTP"}
    def log_message(self,*args): pass
    def send_json(self,status,obj):
        if isinstance(obj,dict): obj={**obj,"service_environment":self.service_environment}
        b=json.dumps(obj,separators=(",",":"),sort_keys=True).encode()
        self.send_response(status)
        self.send_header("content-type","application/json")
        self.send_header("content-length",str(len(b)))
        self.send_header("cache-control","no-store")
        self.end_headers()
        self.wfile.write(b)
    def body(self):
        raw_length=self.headers.get("content-length")
        if raw_length is None: raise ValueError("content_length_required")
        n=int(raw_length)
        if n<1 or n>MAX_REQUEST_BYTES: raise ValueError("invalid_request_size")
        raw=self.rfile.read(n)
        if len(raw)!=n: raise ValueError("incomplete_body")
        data=json.loads(raw)
        if not isinstance(data,dict): raise ValueError("object_required")
        return data
    def _authorized(self):
        if not self.authorizer.allowed(self.headers.get("authorization")):
            self.send_json(401,{"error":"unauthorized"})
            return False
        return True
    def _error(self,error):
        if isinstance(error,KeyError): return self.send_json(404,{"error":str(error.args[0])})
        if isinstance(error,(ValueError,TypeError,KeyError,json.JSONDecodeError)):
            return self.send_json(400,{"error":str(error)})
        return self.send_json(500,{"error":"internal_error"})
    def do_GET(self):
        p=urlparse(self.path).path
        try:
            if p=="/status":
                return self.send_json(200,self.fleet.status())
            if p=="/ready":
                return self.send_json(200,{"ready":True,**self.fleet.status()})
            if not self._authorized(): return
            if p=="/vfs": return self.send_json(200,{"allocations":self.fleet.list()})
            m=re.fullmatch(r"/vfs/("+VFS_ID+r")",p)
            if m: return self.send_json(200,{"allocation":self.fleet.get(m[1])})
            m=re.fullmatch(r"/vfs/("+VFS_ID+r")/ab",p)
            if m: return self.send_json(200,{"allocation":self.fleet.get(m[1]),"entries":self.fleet.entries(m[1])})
            m=re.fullmatch(r"/vfs/("+VFS_ID+r")/ab/("+ENTRY_ID+r")",p)
            if m: return self.send_json(200,self.fleet.read_ab(m[1],m[2]))
            return self.send_json(404,{"error":"not_found"})
        except Exception as error: return self._error(error)
    def do_POST(self):
        p=urlparse(self.path).path
        if not self._authorized(): return
        try:
            if p=="/vfs":
                data=self.body()
                allocation=self.fleet.allocate(data["label"],data["source_ref"],
                                                data.get("quota_bytes",1024*1024))
                return self.send_json(201,{"allocation":allocation,"next":f"/vfs/{allocation['vfs_id']}/ab"})
            m=re.fullmatch(r"/vfs/("+VFS_ID+r")/ab",p)
            if m:
                data=self.body()
                result=self.fleet.admit_ab(m[1],data["bits"],data["source_ref"])
                return self.send_json(201,result)
            m=re.fullmatch(r"/vfs/("+VFS_ID+r")/ab/("+ENTRY_ID+r")/verify",p)
            if m: return self.send_json(200,self.fleet.read_ab(m[1],m[2],observe=True))
            if p in ("/artifacts","/artifacts/raw","/verify"):
                return self.send_json(410,{"error":"direct_artifact_commit_retired","next":"POST /vfs then POST /vfs/{vfs_id}/ab"})
            return self.send_json(404,{"error":"not_found"})
        except Exception as error: return self._error(error)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".vfs-server")
    ap.add_argument("--host",default="127.0.0.1")
    ap.add_argument("--port",type=int,default=8787)
    ap.add_argument("--token-file")
    ap.add_argument("--carrier-id",default="VFS_SERVER:loopback")
    a=ap.parse_args()
    if not a.token_file and a.host not in ("127.0.0.1","::1","localhost"):
        ap.error("--token-file is required for non-loopback listeners")
    Handler.authorizer=MutationAuthorizer(a.token_file)
    Handler.service_environment={**Handler.service_environment,"carrier_id":a.carrier_id}
    Handler.fleet=VFSFleet(a.root)
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=="__main__":main()
