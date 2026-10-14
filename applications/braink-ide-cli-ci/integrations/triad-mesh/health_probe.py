"""A real signed/mTLS probe plus fresh backing readiness, not synthetic telemetry."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from braink_node.owner_vfs.store import VFSStore
import triad_mesh_pb2 as pb
import triad_mesh_pb2_grpc as rpc
from triad_grpc_server import signed_bytes
from qualify_live import channel


def probe(config):
    r=pb.TriadMatrixHopRequest(raw_word_input='Signed transport readiness probe',target_git_revision=config['source_revision'],
         request_id='runtime-readiness',timestamp_epoch_ns=time.time_ns(),nonce=os.urandom(32),warrant_levels=[1])
    key=Ed25519PrivateKey.from_private_bytes((Path(config['tls_root'])/'authority.key').read_bytes())
    r.authority_signature=key.sign(signed_bytes(r)).hex()
    with channel(config['tls_root'],config['bind']) as transport:
        response=rpc.TriadMeshOrchestratorStub(transport).TraversalMatrixHop(r,timeout=3)
    assert response.concept.assigned_node_id==config['identity']
    store=VFSStore(Path(config['root'])/'vfs');store.read_content(response.artifact_digest)
    assert store.verify_receipt_chain()['verified']
    with urllib.request.urlopen(config['mcp_url'].removesuffix('/mcp')+'/health',timeout=3) as result:backing=json.load(result)
    assert backing['readiness_mask']==7 and backing['mutual_authentication'] is True
    return {'identity':config['identity'],'readiness_mask':7,'transport':'gRPC/mTLS',
            'matrix_status':pb.MatrixStatus.Name(response.status),'source_revision':config['source_revision'],
            'artifact_digest':response.artifact_digest,'receipt_verified':True,
            'backing_readiness_mask':backing['readiness_mask']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);args=p.parse_args()
    print(json.dumps(probe(json.loads(args.config.read_text()))))
