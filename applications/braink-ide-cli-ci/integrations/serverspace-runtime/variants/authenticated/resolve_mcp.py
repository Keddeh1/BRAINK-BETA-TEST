"""Official SDK RESOLVE surface with an independent retained VFS instance."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re

from mcp.server.fastmcp import FastMCP
from pydantic import StrictInt
from starlette.responses import JSONResponse
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore, canonical_json
from consilience import aggregate
from hci import RuntimePanel


class ResolveNode:
    def __init__(self, root, substrate_root, identity):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.identity = identity
        metadata = json.loads((Path(substrate_root)/'daemon.json').read_text())
        self.panel = RuntimePanel(substrate_root, metadata['identity'])
        self.panel.read()  # Substrate-first: no listener before authentication succeeds.
        self.store = VFSStore(self.root/'vfs')

    def resolve(self, request_id, levels, environment, family, custody):
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,128}',request_id):
            raise ValueError('Explicit bounded request identity required')
        for value in (environment, family, custody):
            if not isinstance(value,str) or not 1 <= len(value) <= 256:
                raise ValueError('Explicit bounded environment, family and custody required')
        if len(levels)>4096: raise ValueError('At most 4096 warrant terms per submission')
        arithmetic = aggregate(levels)
        # Request bytes retain custody and context separately; a hash is an artifact key.
        request={'request_id':request_id,'levels':levels,'environment':environment,
                 'family':family,'custody':custody,'instance':self.identity}
        fingerprint=hashlib.sha256(canonical_json(request)).hexdigest()
        path='/resolve/'+hashlib.sha256(request_id.encode()).hexdigest()+'.json'
        with (self.root/'resolve.lock').open('a') as lock:
            (self.root/'resolve.lock').chmod(0o600);fcntl.flock(lock,fcntl.LOCK_EX)
            existing=self.store.resolve_path(path)
            if existing:
                saved=json.loads(self.store.read_content(existing.digest))
                if saved['request_fingerprint']!=fingerprint:
                    raise ValueError('Request identity conflict; prior result retained')
                return {'replayed':True,'artifact_digest':existing.digest,'result':saved,
                        'chain':self.store.verify_receipt_chain()}
            frame=self.panel.read()
            saved={'schema':'keddeh.resolve-result.v1','request':request,
                   'request_fingerprint':fingerprint,'arithmetic':arithmetic,
                   'origin_anchor':1,'unity_variable':'X','unity_assignment':None,
                   'substrate_identity':frame['state']['I'],
                   'substrate_digest':frame['state_digest'],
                   'warrant_policy':'Explicit caller classification retained; never elevated by persistence'}
            content=canonical_json(saved)
            artifact,receipt=self.store.write(ArtifactWrite(path,content,
                'module://serverspace/resolve/'+self.identity,media_type='application/json'))
            if self.store.read_content(artifact.digest)!=content:
                raise RuntimeError('Durable result readback differs')
            return {'replayed':False,'artifact_digest':artifact.digest,'receipt':receipt.as_dict(),
                    'result':saved,'chain':self.store.verify_receipt_chain()}

    def read(self,digest):
        return {'artifact_digest':digest,'result':json.loads(self.store.read_content(digest)),
                'chain':self.store.verify_receipt_chain()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True);parser.add_argument('--substrate-root',required=True)
    parser.add_argument('--identity',required=True);parser.add_argument('--port',type=int,required=True)
    args=parser.parse_args()
    node=ResolveNode(args.root,args.substrate_root,args.identity)
    server=FastMCP('Keddeh ServerSpace RESOLVE '+args.identity,host='127.0.0.1',port=args.port,
                   stateless_http=True,json_response=True)

    @server.tool()
    def resolve_q32(request_id:str, levels:list[StrictInt], environment:str, family:str, custody:str)->dict:
        """Compute canonical Q32.32, commit to this instance's VFS and verify readback."""
        return node.resolve(request_id,levels,environment,family,custody)

    @server.tool()
    def read_resolve_receipt(artifact_digest:str)->dict:
        """Read verified retained result bytes and the instance receipt chain."""
        return node.read(artifact_digest)

    @server.custom_route('/health',methods=['GET'])
    async def health(request):
        try:
            frame=node.panel.read()
            return JSONResponse({'identity':node.identity,'readiness_mask':frame['readiness_mask'],
                                 'deployment_revision':Path(__file__).parent.name,
                                 'mutual_authentication':frame['authentication']['mutual'],
                                 'receipt_chain':node.store.verify_receipt_chain()})
        except Exception as exc:
            return JSONResponse({'identity':node.identity,'error':type(exc).__name__},status_code=503)
    server.run(transport='streamable-http')


if __name__=='__main__':main()
