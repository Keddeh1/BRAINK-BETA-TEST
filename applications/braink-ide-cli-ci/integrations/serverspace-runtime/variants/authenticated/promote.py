"""Promote one observed ServerSpace instance, retaining the other and rollback data."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

parser=argparse.ArgumentParser();parser.add_argument('role',choices=['primary','replica']);args=parser.parse_args()
manifest=Path('/workspace/braink-setup/service-activation/source/services.json')
baseline=Path('/workspace/work/braink-node-repo/applications/braink-ide-cli-ci/integrations/serverspace-runtime/substrate.py')
data=json.loads(manifest.read_text());canary=next(s for s in data['services'] if s['id']=='serverspace-auth-canary');variant=Path(canary['command'][1]);sys.path.insert(0,str(variant.parent));import substrate
spec=importlib.util.spec_from_file_location('baseline',baseline);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def check(service):
    root=Path(service['probe']['root']);metadata=json.loads((root/'daemon.json').read_text())
    module=substrate if service['command'][1]==str(variant) else old
    return module.handshake(root,metadata['pid'],service['probe']['identity'])

lock=Path(data['state_root'])/'activation.lock'
with lock.open('a') as stream:
    fcntl.flock(stream,fcntl.LOCK_EX)
    data=json.loads(manifest.read_text());target=next(s for s in data['services'] if s['id']=='serverspace-'+args.role)
    other=next(s for s in data['services'] if s['id']=='serverspace-'+('replica' if args.role=='primary' else 'primary'))
    check(other);before=check(target);root=Path(target['probe']['root'])
    checkpoint={'service':target,'canonical':json.loads((root/'canonical_state.dat').read_text()),'frame':before,'observed_at':time.time()}
    backup=root/'pre-authenticated-promotion.json'
    if not backup.exists():backup.write_text(json.dumps(checkpoint,indent=2));backup.chmod(0o600)
    pid=before['peer_identity']['pid'];live=Path('/proc/'+str(pid)+'/cmdline').read_bytes()
    assert target['command'][1].encode() in live and str(root).encode() in live
    os.kill(pid,signal.SIGTERM)
    for _ in range(150):
        with (root/'daemon.lock').open('a') as ownership:
            try:fcntl.flock(ownership,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:time.sleep(.1)
    else:raise RuntimeError('Prior daemon retained ownership; target unchanged')
    retained=json.loads((root/'canonical_state.dat').read_text())
    target['command']=[canary['command'][0],str(variant),'--root',str(root),'--identity',target['probe']['identity'],'daemon'];target['cwd']=str(variant.parent)
    pending=manifest.with_suffix('.pending');pending.write_text(json.dumps(data,indent=2));pending.replace(manifest)

for _ in range(300):
    try:
        after=check(target)
        if after['peer_identity']['pid']!=pid:break
    except Exception:pass
    time.sleep(.1)
else:raise RuntimeError('Promotion not ready; rollback service retained in '+str(backup))
assert after['state']['I']==retained['I'] and after['state']['q']>=retained['q']
assert after['authentication']['mutual'] and after['readiness_mask']==7
other_frame=check(other)
receipt={'schema':'keddeh.serverspace-promotion.v1','role':args.role,'observed_at':time.time(),'before_daemon_pid':pid,'after':after,'other_instance':{'identity':other_frame['state']['I'],'mask':other_frame['readiness_mask'],'peer':other_frame['peer_identity']},'retained_counter':retained['q'],'rollback_record':str(backup),'source':str(variant)}
path=root/'promotion.json';path.write_text(json.dumps(receipt,indent=2));path.chmod(0o600);print(json.dumps(receipt))
