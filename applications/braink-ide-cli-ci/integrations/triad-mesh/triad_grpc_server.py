"""Owner-signed, mTLS gRPC variant over the existing SDK and per-instance VFS."""
import argparse
from concurrent import futures
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import signal
import subprocess
import threading
import time

import grpc
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from google.protobuf.json_format import MessageToDict
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore, canonical_json
import triad_mesh_pb2 as pb
import triad_mesh_pb2_grpc as rpc
from sdk_bridge import exchange


def signed_bytes(request):
    copy=pb.TriadMatrixHopRequest();copy.CopyFrom(request);copy.authority_signature=''
    return b'KEDDEH-TRIAD-GRPC-v1\0'+copy.SerializeToString(deterministic=True)


def source_matches(config):
    root=Path(__file__).resolve().parent
    revision=config['source_revision']
    if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Canonical source revision required')
    repository=Path(config['repository']).resolve(strict=True)
    for file in sorted(root.glob('*')):
        if file.suffix in {'.py','.proto'}:
            relative=file.relative_to(repository).as_posix()
            original=subprocess.check_output(['git','show',revision+':'+relative],cwd=repository,stderr=subprocess.DEVNULL)
            if file.read_bytes()!=original:raise ValueError('Installed source differs from Git revision')
    return revision


class Node(rpc.TriadMeshOrchestratorServicer):
    def __init__(self,config):
        self.config=config;self.identity=config['identity']
        self.revision=source_matches(config)
        self.root=Path(config['root']).resolve();self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.store=VFSStore(self.root/'vfs')
        self.authority=Ed25519PublicKey.from_public_bytes(bytes.fromhex(config['authority_public']))
        self.authority_id='ed25519:'+hashlib.sha256(bytes.fromhex(config['authority_public'])).hexdigest()
        self.thread_lock=threading.Lock()
        # A real authenticated substrate readback must precede listener startup.
        import urllib.request
        health_url=config['mcp_url'].removesuffix('/mcp')+'/health'
        with urllib.request.urlopen(health_url,timeout=3) as response:health=json.load(response)
        if health.get('readiness_mask')!=7 or health.get('mutual_authentication') is not True:
            raise RuntimeError('Backing substrate has not qualified startup')

    def authenticate(self,request,context):
        if not request.request_id or not re.fullmatch('[A-Za-z0-9._-]{1,100}',request.request_id):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,'Explicit request identity required')
        if not request.raw_word_input or len(request.raw_word_input.encode())>8192:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,'Bounded nonempty word input required')
        if not math.isfinite(request.current_load_factor) or request.current_load_factor<0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,'Finite nonnegative load observation required')
        if not request.warrant_levels or len(request.warrant_levels)>4096 or any(x not in (1,2,3,4) for x in request.warrant_levels):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,'Explicit warrant classifications required')
        if len(request.nonce)!=32 or abs(time.time_ns()-request.timestamp_epoch_ns)>300_000_000_000:
            context.abort(grpc.StatusCode.UNAUTHENTICATED,'Fresh signed request context required')
        try:self.authority.verify(bytes.fromhex(request.authority_signature),signed_bytes(request))
        except (ValueError,InvalidSignature):context.abort(grpc.StatusCode.UNAUTHENTICATED,'Authority signature rejected')
        if request.target_git_revision!=self.revision:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION,'Requested revision is not installed')

    def TraversalMatrixHop(self,request,context):
        self.authenticate(request,context)
        payload={'word':request.raw_word_input,'revision':request.target_git_revision,
                 'load_observation':request.current_load_factor,'warrants':list(request.warrant_levels),
                 'instance':self.identity,'authority':self.authority_id}
        fingerprint=hashlib.sha256(canonical_json(payload)).hexdigest()
        path='/triad/'+request.request_id+'.json'
        # OS and thread locks serialize competing retries in this VFS instance.
        with self.thread_lock,(self.root/'admission.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            existing=self.store.resolve_path(path)
            if existing:
                value=json.loads(self.store.read_content(existing.digest))
                if value['fingerprint']!=fingerprint:
                    context.abort(grpc.StatusCode.ALREADY_EXISTS,'Conflicting request identity; prior state retained')
                response=pb.TriadMatrixHopResponse.FromString(bytes.fromhex(value['response_wire']))
                response.artifact_digest=existing.digest
                if not self.store.verify_receipt_chain()['verified']:
                    context.abort(grpc.StatusCode.DATA_LOSS,'Local receipt chain differs')
                return response
            intent_path='/triad-intent/'+request.request_id+'.json'
            intent=self.store.resolve_path(intent_path)
            if intent:
                retained=json.loads(self.store.read_content(intent.digest))
                if retained['fingerprint']!=fingerprint:
                    context.abort(grpc.StatusCode.ALREADY_EXISTS,'Conflicting durable intent; prior state retained')
            else:
                self.store.write(ArtifactWrite(intent_path,canonical_json({'fingerprint':fingerprint,'request':payload}),
                    'module://triad/'+self.identity,media_type='application/json'))
            try:observed=exchange(self.config['mcp_url'],request,self.identity)
            except Exception:
                # No state purge, synthetic signature or allocation on backend failure.
                context.abort(grpc.StatusCode.UNAVAILABLE,'SDK/substrate verification unavailable; prior state retained')
            response=pb.TriadMatrixHopResponse(
                status=pb.MATRIX_STATUS_PENDING,authority_lock=self.authority_id,timestamp_epoch_ns=time.time_ns(),
                concept=pb.ConceptTier(word_processed=request.raw_word_input,assigned_node_id=self.identity,vfs_mount_path=str(self.root/'vfs')),
                execution=pb.ExecutionTier(il_llm_state='NOT_BOUND',braink_verdict='SIGNED_REQUEST_COMMITTED'),
                integration=pb.IntegrationTier(sdk_commit_verified=True,mcp_transport_version=observed['protocol_version'],
                    provenance=pb.ResearchProvenance(source_git_revision=self.revision)),
                receipt_digest=observed['receipt_chain']['head'],
                unresolved_bindings=['IL_LLM_EXECUTION','KEX_ALLOCATION','EMPIRICAL_CAPACITY_CALIBRATION'])
            value={'schema':'keddeh.triad-hop.v1','fingerprint':fingerprint,'request':payload,
                   'sdk':observed,'response_wire':response.SerializeToString(deterministic=True).hex(),
                   'receipt_digest_scope':'Backing RESOLVE receipt chain head',
                   'da_registrar':{'state':'UNASSESSED','independent_of_braink_admission':True}}
            content=canonical_json(value)
            artifact,receipt=self.store.write(ArtifactWrite(path,content,'module://triad/'+self.identity,media_type='application/json'))
            if self.store.read_content(artifact.digest)!=content or not self.store.verify_receipt_chain()['verified']:
                context.abort(grpc.StatusCode.DATA_LOSS,'Committed VFS readback differs')
            response.artifact_digest=artifact.digest
            return response

    def StreamMatrixTelemetry(self,request,context):
        # Bounded observed snapshot, not a fabricated periodic hardware feed.
        yield self.TraversalMatrixHop(request,context)


def start(config):
    node=Node(config)
    server=grpc.server(futures.ThreadPoolExecutor(max_workers=4),maximum_concurrent_rpcs=16,
        options=[('grpc.max_receive_message_length',65536),('grpc.max_send_message_length',65536)])
    rpc.add_TriadMeshOrchestratorServicer_to_server(node,server)
    tls=Path(config['tls_root'])
    credentials=grpc.ssl_server_credentials([( (tls/'server.key').read_bytes(),(tls/'server.pem').read_bytes())],
        root_certificates=(tls/'ca.pem').read_bytes(),require_client_auth=True)
    port=server.add_secure_port(config.get('bind','127.0.0.1:0'),credentials)
    if not port:raise RuntimeError('gRPC secure listener could not bind')
    server.start()
    return server,node,port


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    config=json.loads(args.config.read_text());server,node,port=start(config)
    from braink_node.storage import atomic_write
    atomic_write(node.root/'daemon.json',canonical_json({'port':port,'identity':node.identity,'revision':node.revision,'pid':__import__('os').getpid()}))
    def stop(*_):server.stop(5)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    server.wait_for_termination()


if __name__=='__main__':main()
