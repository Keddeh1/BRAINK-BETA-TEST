"""Exercise the installed owner canary and retain observed execution evidence."""
import concurrent.futures
import fcntl
import http.client
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import sys
import time

root=Path('/workspace/braink-setup/families/SERVERSPACE/runtime/substrate-auth-canary')
manifest=json.loads(Path('/workspace/braink-setup/service-activation/source/services.json').read_text())
service=next(s for s in manifest['services'] if s['id']=='serverspace-auth-canary')
sys.path.insert(0,str(Path(service['command'][1]).parent))
import substrate

def current():
    metadata=json.loads((root/'daemon.json').read_text())
    return substrate.handshake(root,metadata['pid'],service['probe']['identity'])

def ready(deadline=30):
    end=time.monotonic()+deadline
    while time.monotonic()<end:
        try:return current()
        except Exception:time.sleep(.1)
    raise RuntimeError('Canary readiness deadline exceeded')

before=ready()
frames=list(concurrent.futures.ThreadPoolExecutor(max_workers=8).map(lambda _:current(),range(32)))
assert all(f['readiness_mask']==7 and f['authentication']['mutual'] for f in frames)
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
    client.settimeout(2);client.connect(str(root/'readiness.sock'));client.sendall(b'KXA2'+b'x'*96)
    assert client.recv(1)==b'', 'Invalid client signature was admitted'
after_invalid=current()
api=json.loads((root/'api.json').read_text());connection=http.client.HTTPConnection(api['host'],api['port'],timeout=3)
connection.request('GET','/api/substrate');response=connection.getresponse();api_frame=json.loads(response.read());connection.close();assert response.status==200 and api_frame['readiness_mask']==7
limits={}
for name,worker in before['state']['workers'].items():
    text=Path('/proc/'+str(worker['pid'])+'/limits').read_text()
    assert '536870912' in text and '256' in text
    status=Path('/proc/'+str(worker['pid'])+'/status').read_text()
    rss=next(int(line.split()[1])*1024 for line in status.splitlines() if line.startswith('VmRSS:'))
    assert rss<worker['resource_limits']['address_space_bytes']
    limits[name]={'pid':worker['pid'],'resident_bytes':rss,'enforced':worker['resource_limits']}
inode=(root/'substrate.mmap').stat().st_ino
retained=json.loads((root/'canonical_state.dat').read_text())
worker=before['state']['workers']['publisher']['pid'];old_pid=before['peer_identity']['pid'];os.kill(worker,signal.SIGTERM)
recovered=None;unavailable=False;started=time.monotonic()
for _ in range(300):
    try:
        observed=current()
        if observed['peer_identity']['pid']!=old_pid:recovered=observed;break
    except Exception:unavailable=True
    time.sleep(.1)
assert unavailable and recovered is not None, 'Automated recovery did not fence the failed worker'
assert recovered['authentication']['server_public']==before['authentication']['server_public']
assert recovered['state']['I']==retained['I'] and recovered['state']['q']>retained['q']
assert (root/'substrate.mmap').stat().st_ino==inode
assert root.stat().st_mode&0o777==0o700
assert (root/'readiness.sock').stat().st_mode&0o777==0o600
assert (root/'canonical_state.dat').stat().st_mode&0o777==0o600
evidence={'schema':'keddeh.serverspace-canary-evidence.v1','observed_at':time.time(),'rapid_authenticated_handshakes':len(frames),'invalid_client_signature':'REJECTED','api_handshake':'PASS','resource_observations':limits,'recovery':{'old_daemon_pid':old_pid,'new_daemon_pid':recovered['peer_identity']['pid'],'elapsed_seconds':time.monotonic()-started,'unready_interval_observed':unavailable,'enrolled_key_retained':True,'mmap_inode_retained':True,'last_committed_q':retained['q'],'recovered_q':recovered['state']['q']},'final_frame':recovered,'scope':'Authenticated local UDS canary; does not establish distributed failover or loss-free networks'}
output=root/'qualification.json';output.write_text(json.dumps(evidence,indent=2));output.chmod(0o600)
print(json.dumps(evidence))
