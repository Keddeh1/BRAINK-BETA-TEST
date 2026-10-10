"""Persistent local substrate and observed-worker watchdog; no lock-free claim."""
import argparse
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mmap
import multiprocessing as mp
import os
import resource
from pathlib import Path
import signal
import socket
import struct
import sys
import time
import zlib
import handshake_auth as auth

HEADER = struct.Struct('>4sII32sI')
CAPACITY = 65536

def constrain_worker():
    for name,cap in ((resource.RLIMIT_AS,512*1024*1024),(resource.RLIMIT_NOFILE,256)):
        soft,hard=resource.getrlimit(name)
        limit=cap if hard==resource.RLIM_INFINITY else min(cap,hard)
        resource.setrlimit(name,(limit,hard))
    return {'address_space_bytes':resource.getrlimit(resource.RLIMIT_AS)[0],'open_files':resource.getrlimit(resource.RLIMIT_NOFILE)[0]}


def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def atomic(path, content):
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('wb') as stream:
        stream.write(content); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd=os.open(path.parent,os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def encode(state, mask):
    payload=canonical(state)
    if len(payload)>CAPACITY-HEADER.size: raise ValueError('Frame exceeds substrate capacity')
    prefix=struct.pack('>4sII32s',b'KXS1',mask,len(payload),hashlib.sha256(payload).digest())
    return prefix+struct.pack('>I',zlib.crc32(prefix+payload))+payload


def decode(frame):
    if len(frame)<HEADER.size: raise ValueError('Incomplete header')
    magic,mask,length,digest,crc=HEADER.unpack(frame[:HEADER.size]);payload=frame[HEADER.size:]
    if magic!=b'KXS1' or length>CAPACITY-HEADER.size or len(payload)!=length: raise ValueError('Incomplete or invalid frame')
    if zlib.crc32(frame[:HEADER.size-4]+payload)!=crc: raise ValueError('CRC32 mismatch')
    if hashlib.sha256(payload).digest()!=digest: raise ValueError('State digest mismatch')
    return {'state':json.loads(payload),'state_digest':digest.hex(),'readiness_mask':mask,'crc32':crc,'frame_bytes':len(frame)}


def receive_exact(connection, count):
    value=b''
    while len(value)<count:
        chunk=connection.recv(count-len(value))
        if not chunk: raise ValueError('Truncated readiness frame')
        value+=chunk
    return value


def handshake(root, daemon_pid, identity):
    root=Path(root)
    pinned=auth.load(root,identity)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(2);connection.connect(str(root/'readiness.sock'))
        pid,uid,gid=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
        if pid!=daemon_pid or uid!=os.getuid():raise ValueError('UDS peer identity differs')
        context=auth.context(identity,os.getpid(),pid,uid)
        nonce=os.urandom(auth.NONCE_BYTES)
        proof=auth.private(root,'client').sign(context+b'REQUEST'+nonce)
        connection.sendall(auth.MAGIC+nonce+proof)
        server_nonce=receive_exact(connection,auth.NONCE_BYTES)
        header=receive_exact(connection,HEADER.size);length=HEADER.unpack(header)[2]
        if length>CAPACITY-HEADER.size:raise ValueError('Invalid frame capacity')
        frame=header+receive_exact(connection,length)
        auth.verify(pinned['server_public'],receive_exact(connection,auth.SIGNATURE_BYTES),context+b'RESPONSE'+nonce+server_nonce+frame)
        result=decode(frame)
    state=result['state']
    if state['I']!=identity or result['readiness_mask']!=7 or time.time()-state['t']>2 or not all(w['ready'] for w in state['workers'].values()):raise ValueError('Substrate not ready')
    result['peer_identity']={'pid':pid,'uid':uid,'gid':gid}
    result['authentication']={'protocol':'KXA2','algorithm':'Ed25519','mutual':True,'server_public':pinned['server_public'],'client_public':pinned['client_public']}
    return result


def publisher(root, stop):
    limits=constrain_worker()
    counter=0
    retained=root/'canonical_state.dat'
    if retained.exists():
        value=json.loads(retained.read_text())['q']
        if type(value) is not int or value<0:raise ValueError('Invalid retained counter')
        counter=value
    while not stop.value:
        counter+=1
        atomic(root/'publisher.json',canonical({'pid':os.getpid(),'t':time.time(),'q':counter,'resource_limits':limits}))
        time.sleep(0.1)


def writer(root, identity, daemon_pid, publisher_pid, stop):
    limits=constrain_worker()
    memory_path=root/'substrate.mmap'
    with memory_path.open('r+b') as stream, mmap.mmap(stream.fileno(),CAPACITY) as shared:
        while not stop.value:
            try:
                proposal=json.loads((root/'publisher.json').read_text())
                ready=proposal['pid']==publisher_pid and time.time()-proposal['t']<2 and Path('/proc/'+str(proposal['pid'])).exists()
                if ready:
                    state={'I':identity,'O':{'runtime':str(root),'daemon_pid':daemon_pid},'q':proposal['q'],'t':time.time(),
                           'workers':{'publisher':{'pid':proposal['pid'],'ready':True,'resource_limits':proposal['resource_limits']},'canonical_writer':{'pid':os.getpid(),'ready':True,'resource_limits':limits}}}
                    frame=encode(state,7)
                    with (root/'frame.lock').open('a') as lock:
                        fcntl.flock(lock,fcntl.LOCK_EX)
                        shared.seek(0);shared.write(frame);shared.flush();os.fsync(stream.fileno())
                        atomic(root/'canonical_state.dat',canonical(state))
            except FileNotFoundError:pass
            time.sleep(0.1)


def serve_api(root, identity, daemon_pid, stop):
    constrain_worker()
    sys.path.insert(0,str(Path(__file__).parent/'owner'))
    from stratum_engine import FullyEngineeredStratumClient
    handshake(root,daemon_pid,identity)
    client=FullyEngineeredStratumClient('UNCONFIGURED',0,identity)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):
            try:
                observed=handshake(root,daemon_pid,identity)
                if self.path=='/api/substrate':result=observed
                elif self.path=='/api/telemetry':
                    raw=client.get_live_diagnostics()
                    # Initial difficulty and efficiency in supplied source are defaults, not measurements.
                    raw['difficulty']=None;raw['efficiency_pct']=None
                    result={'mining':raw,'pool_configured':False,'substrate':observed}
                else:self.send_error(404);return
            except Exception as error:
                result={'error':type(error).__name__,'ready':False};self.send_response(503)
            else:self.send_response(200)
            content=canonical(result);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    server=HTTPServer(('127.0.0.1',0),Handler);server.timeout=0.25
    atomic(root/'api.json',canonical({'pid':os.getpid(),'host':'127.0.0.1','port':server.server_port,'identity':identity}))
    try:
        while not stop.value:server.handle_request()
    finally:server.server_close()


def daemon(root, identity):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/'daemon.lock').open('a') as ownership:
        fcntl.flock(ownership,fcntl.LOCK_EX|fcntl.LOCK_NB)
        retained=root/'canonical_state.dat'
        if retained.exists():
            previous=json.loads(retained.read_text())
            if previous['I']!=identity or previous['O']['runtime']!=str(root):raise ValueError('Retained independent context differs')
        enrollment=auth.enroll(root,identity)
        stop=mp.RawValue('b',False)
        def halt(*_):setattr(stop,'value',True)
        signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
        pid=os.getpid();atomic(root/'daemon.json',canonical({'pid':pid,'identity':identity}))
        memory=root/'substrate.mmap'
        with memory.open('a+b') as stream:
            if memory.stat().st_size!=CAPACITY:stream.truncate(CAPACITY)
        endpoint=root/'readiness.sock'
        if endpoint.exists():endpoint.unlink()
        server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(str(endpoint));os.chmod(endpoint,0o600);server.listen();server.settimeout(0.1)
        # Child workers must not inherit the daemon ownership lock or listening socket.
        ctx=mp.get_context('spawn');stop=ctx.RawValue('b',False)
        published=ctx.Process(target=publisher,args=(root,stop));published.start()
        written=ctx.Process(target=writer,args=(root,identity,pid,published.pid,stop));written.start()
        workers=[published,written]
        api=None
        try:
            while not stop.value:
                if not all(worker.is_alive() for worker in workers):raise RuntimeError('Worker exited')
                if api is None:
                    try:
                        state=json.loads((root/'canonical_state.dat').read_text())
                        if state['O']['daemon_pid']==pid and time.time()-state['t']<2:
                            api=ctx.Process(target=serve_api,args=(root,identity,pid,stop));api.start()
                    except FileNotFoundError:pass
                try:connection,_=server.accept()
                except socket.timeout:continue
                with connection:
                    connection.settimeout(1)
                    try:
                        client_pid,client_uid,_=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                        if client_uid!=os.getuid():raise ValueError('Client owner differs')
                        hello=receive_exact(connection,auth.HELLO_BYTES)
                        if hello[:4]!=auth.MAGIC:raise ValueError('Handshake protocol differs')
                        nonce=hello[4:36];context=auth.context(identity,client_pid,pid,client_uid)
                        auth.verify(enrollment['client_public'],hello[36:],context+b'REQUEST'+nonce)
                        with (root/'frame.lock').open('a') as lock:
                            fcntl.flock(lock,fcntl.LOCK_SH)
                            with memory.open('rb') as stream:
                                header=stream.read(HEADER.size);length=HEADER.unpack(header)[2]
                                if length>CAPACITY-HEADER.size:raise ValueError('Invalid shared frame')
                                frame=header+stream.read(length)
                            result=decode(frame)
                            if [result['state']['workers'][name]['pid'] for name in ('publisher','canonical_writer')]!=[worker.pid for worker in workers]:raise ValueError('Worker identity differs')
                            if canonical(result['state'])!=(root/'canonical_state.dat').read_bytes():raise ValueError('Canonical writer differs')
                            if time.time()-result['state']['t']>2:raise ValueError('Stale worker frame')
                        server_nonce=os.urandom(auth.NONCE_BYTES)
                        signature=auth.private(root,'server').sign(context+b'RESPONSE'+nonce+server_nonce+frame)
                        connection.sendall(server_nonce+frame+signature)
                    except Exception:continue
                if api is None:
                    api=ctx.Process(target=serve_api,args=(root,identity,pid,stop));api.start()
                elif not api.is_alive():raise RuntimeError('Mining API exited')
        finally:
            setattr(stop,'value',True);server.close();endpoint.unlink(missing_ok=True)
            for process in workers+([api] if api else []):
                process.join(timeout=3)
                if process.is_alive():process.terminate();process.join(timeout=2)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--identity',required=True);parser.add_argument('operation',choices=['daemon','verify'])
    args=parser.parse_args()
    if args.operation=='daemon':daemon(args.root,args.identity)
    else:
        metadata=json.loads((args.root/'daemon.json').read_text());print(json.dumps(handshake(args.root,metadata['pid'],args.identity)))
