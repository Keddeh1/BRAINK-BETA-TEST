"""Real gRPC/mTLS -> official MCP SDK -> authenticated substrate -> durable VFS."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import time
import grpc
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from google.protobuf.json_format import MessageToDict
from calibration import Measurements
import triad_mesh_pb2 as pb
import triad_mesh_pb2_grpc as rpc
from triad_grpc_server import signed_bytes


def channel(tls,address,client=True):
    tls=Path(tls)
    credentials=grpc.ssl_channel_credentials((tls/'ca.pem').read_bytes(),
        (tls/'client.key').read_bytes() if client else None,
        (tls/'client.pem').read_bytes() if client else None)
    return grpc.secure_channel(address,credentials)


def qualify(config,address):
    key=Ed25519PrivateKey.from_private_bytes((Path(config['tls_root'])/'authority.key').read_bytes())
    def request(identity='qualified-hop',word='Preserve the complete supplied semantic word path.'):
        r=pb.TriadMatrixHopRequest(raw_word_input=word,target_git_revision=config['source_revision'],
            current_load_factor=850,request_id=identity,timestamp_epoch_ns=time.time_ns(),nonce=os.urandom(32),warrant_levels=[1,2,3,4])
        r.authority_signature=key.sign(signed_bytes(r)).hex();return r
    observer=Measurements()
    with channel(config['tls_root'],address) as transport:
        stub=rpc.TriadMeshOrchestratorStub(transport)
        def call(r):
            start=time.perf_counter_ns();value=stub.TraversalMatrixHop(r,timeout=20)
            observer.observe(time.perf_counter_ns()-start);return value
        first=call(request());assert first.status==pb.MATRIX_STATUS_PENDING
        assert first.concept.assigned_node_id==config['identity']
        assert first.concept.word_processed==request().raw_word_input
        assert first.integration.sdk_commit_verified and first.integration.mcp_transport_version
        assert not first.execution.HasField('kex_memory_allocation_offset')
        assert not first.integration.provenance.HasField('empirical_saturation_ratio')
        with ThreadPoolExecutor(max_workers=8) as pool:
            replay=list(pool.map(lambda _:call(request()),range(16)))
        assert all(x.SerializeToString()==first.SerializeToString() for x in replay)
        invalid=request('invalid-signature');invalid.authority_signature='00'*64
        try:call(invalid)
        except grpc.RpcError as e:assert e.code()==grpc.StatusCode.UNAUTHENTICATED
        else:raise AssertionError('Invalid signature accepted')
        try:call(request(word='Conflicting semantics'))
        except grpc.RpcError as e:assert e.code()==grpc.StatusCode.ALREADY_EXISTS
        else:raise AssertionError('Conflicting retry accepted')
        stale=request('stale');stale.timestamp_epoch_ns=1;stale.authority_signature=key.sign(signed_bytes(stale)).hex()
        try:call(stale)
        except grpc.RpcError as e:assert e.code()==grpc.StatusCode.UNAUTHENTICATED
        else:raise AssertionError('Stale request accepted')
        after=call(request());assert after.artifact_digest==first.artifact_digest
        stream=list(stub.StreamMatrixTelemetry(request(),timeout=20));assert len(stream)==1 and stream[0].artifact_digest==first.artifact_digest
        with channel(config['tls_root'],address,client=False) as anonymous:
            try:rpc.TriadMeshOrchestratorStub(anonymous).TraversalMatrixHop(request(),timeout=3)
            except grpc.RpcError as e:assert e.code()==grpc.StatusCode.UNAVAILABLE
            else:raise AssertionError('No-certificate client accepted')
        # Get the actual latency report without injecting another timed sample.
        ordered=sorted(observer.window);p99=ordered[(99*len(ordered)+99)//100-1]
        return {'schema':'keddeh.triad-live-qualification.v1','observed_at':time.time(),
          'transport':'Real gRPC with mandatory mTLS','instance':config['identity'],
          'source_revision':config['source_revision'],'source_commit_verified':True,
          'backing_mcp':config['mcp_url'],'mcp_protocol':first.integration.mcp_transport_version,
          'artifact_digest':first.artifact_digest,'receipt_digest':first.receipt_digest,
          'concurrent_replays':len(replay),'signature_rejected':True,'conflict_rejected':True,'stale_rejected':True,
          'missing_client_certificate_rejected':True,'full_word_retained':True,'state_retained_after_rejections':True,
          'kex_offset_fabricated':False,'matrix_status':'PENDING','unresolved_bindings':list(first.unresolved_bindings),
          'latency':{'samples':len(ordered),'p99_ns':p99,'budget_ns':observer.budget,
                     'acceptance':'PASS' if p99<observer.budget else 'EXCEEDED','scope':'Complete real client RPC round trip including SDK/VFS on first admission'},
          'calibration':{'tolerance_index':None,'state':'HARDWARE_BASELINE_NOT_BOUND','gates_transport':False},
          'da_registrar':{'state':'UNASSESSED','independent_of_braink':True}}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--address',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=qualify(json.loads(args.config.read_text()),args.address)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
