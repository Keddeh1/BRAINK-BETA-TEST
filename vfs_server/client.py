"""Bounded HTTP VFS client; retry identity is frozen before transport execution."""
import base64,json,time,urllib.error,urllib.parse,urllib.request
from .model import ArtifactWrite

class VFSClient:
    def __init__(self,endpoint,token,timeout=5,attempts=2):
        parsed=urllib.parse.urlsplit(endpoint)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
            raise ValueError('Explicit HTTP(S) service origin required')
        if parsed.scheme=='http' and parsed.hostname not in ('127.0.0.1','localhost','::1'):
            raise ValueError('Remote endpoints require verified HTTPS')
        if not isinstance(token,str) or not token:raise ValueError('Owner token required')
        if type(attempts) is not int or not 1<=attempts<=3:raise ValueError('One to three attempts required')
        if type(timeout) not in (int,float) or not 0<timeout<=30:raise ValueError('Bounded timeout required')
        self.endpoint,self.token,self.timeout,self.attempts=endpoint.rstrip('/'),token,timeout,attempts
        # Loopback bypasses external HTTP proxies; HTTPS retains inherited routing.
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({})) if parsed.hostname in ('127.0.0.1','localhost','::1') else urllib.request.build_opener()

    def write(self,request:ArtifactWrite):
        body={'path':request.path,'source':request.source,'content_b64':base64.b64encode(request.content).decode(),'predecessor':request.predecessor,'media_type':request.media_type,'continuation_id':request.continuation_id,'expected_version':request.expected_version}
        wire=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
        attempts=self.attempts if request.continuation_id else 1
        for attempt in range(attempts):
            req=urllib.request.Request(self.endpoint+'/artifacts',data=wire,headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},method='POST')
            try:
                with self.opener.open(req,timeout=self.timeout) as response:
                    raw=response.read(1024*1024+1)
                    if len(raw)>1024*1024:raise ValueError('Response limit exceeded')
                    if response.status!=201:raise ValueError('Unexpected write status')
                    return json.loads(raw)
            except urllib.error.HTTPError:
                # Authorization/conflict/application errors are not connection failures.
                raise
            except (urllib.error.URLError,ConnectionError,TimeoutError):
                if attempt+1==attempts:raise
                time.sleep(.05)
