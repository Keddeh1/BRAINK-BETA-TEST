from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,unquote
import argparse,base64,json
from .model import ArtifactWrite
from .store import VFSStore
from .auth import MutationAuthorizer
from .health import readiness
MAX_REQUEST_BYTES=70*1024*1024

class Handler(BaseHTTPRequestHandler):
    store=None
    def log_message(self,*args): pass
    def send_json(self,status,obj):
        b=json.dumps(obj,separators=(",",":"),sort_keys=True).encode()
        self.send_response(status); self.send_header("content-type","application/json")
        self.send_header("content-length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def body(self):
        n=int(self.headers.get("content-length","0") or 0)
        if n<1:return {}
        if n>MAX_REQUEST_BYTES:raise ValueError("request_too_large")
        return json.loads(self.rfile.read(n))
    def do_GET(self):
        p=unquote(urlparse(self.path).path)
        try:
            if p=="/status":return self.send_json(200,self.store.status())
            if p=="/ready":
                state=readiness(self.store)
                return self.send_json(200 if state["ready"] else 503,state)
            if not self.authorizer.allowed(self.headers.get("authorization")):
                return self.send_json(401,{"error":"unauthorized"})
            if p.startswith("/artifacts/"):
                digest=p.split("/",2)[2]; rec=self.store.get_artifact(digest)
                if not rec:return self.send_json(404,{"error":"artifact_not_found"})
                return self.send_json(200,{"artifact":rec.as_dict(),"content_b64":base64.b64encode(self.store.read_content(digest)).decode()})
            if p.startswith("/paths/"):
                rec=self.store.resolve_path(p[len("/paths"):])
                return self.send_json(200,{"artifact":rec.as_dict()}) if rec else self.send_json(404,{"error":"path_not_found"})
            if p.startswith("/lineage/"):
                digest=p.split("/",2)[2]; return self.send_json(200,{"digest":digest,"edges":self.store.lineage(digest)})
            return self.send_json(404,{"error":"not_found"})
        except (ValueError,KeyError) as e:return self.send_json(400,{"error":str(e)})
        except Exception:return self.send_json(500,{"error":"internal_error"})
    def do_POST(self):
        p=urlparse(self.path).path
        try:
            data=self.body()
            if p=="/artifacts":
                raw=base64.b64decode(data["content_b64"],validate=True)
                rec,receipt=self.store.write(ArtifactWrite(data["path"],raw,data["source"],data.get("predecessor"),data.get("media_type","application/octet-stream")))
                return self.send_json(201,{"artifact":rec.as_dict(),"actor_receipt":receipt.as_dict(),"verification":"PENDING_OBSERVER_READBACK"})
            if p=="/verify":return self.send_json(200,self.store.verify(data["digest"]))
            return self.send_json(404,{"error":"not_found"})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:return self.send_json(400,{"error":str(e)})
        except Exception:return self.send_json(500,{"error":"internal_error"})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default=".vfs-server")
    ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8787)
    a=ap.parse_args(); Handler.store=VFSStore(a.root); ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=="__main__":main()
