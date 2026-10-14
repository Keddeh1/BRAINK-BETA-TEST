"""Saved owner-service activation with exact-command adoption and runtime readback."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import shutil
import subprocess
import time
import http.client
from urllib.parse import urlsplit

def processes(command):
    found=[]
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args=[x.decode() for x in p.read_bytes().split(b'\0') if x]
            if args==command and p.parent.joinpath('stat').read_text().split()[2]!='Z':
                found.append(int(p.parent.name))
        except (OSError,UnicodeError): pass
    return found

def readback(service):
    probe=service['probe']
    if probe['kind']=='grpc':
        value=subprocess.run(probe['command'],check=True,capture_output=True,text=True,timeout=8)
        result=json.loads(value.stdout)
        if result.get('identity')!=probe['identity'] or result.get('backing_readiness_mask')!=7 or result.get('receipt_verified') is not True:
            raise RuntimeError('gRPC authenticated readback differs')
        return result
    if probe['kind']=='substrate':
        spec=importlib.util.spec_from_file_location('owner_substrate',service['command'][1])
        module=importlib.util.module_from_spec(spec)
        # Load the configured executable's sibling authentication module just as
        # direct execution does; don't turn a healthy daemon into a false fault.
        source_dir=str(Path(service['command'][1]).resolve().parent)
        sys.path.insert(0,source_dir)
        try:spec.loader.exec_module(module)
        finally:sys.path.remove(source_dir)
        root=Path(probe['root']);meta=json.loads((root/'daemon.json').read_text())
        result=module.handshake(root,meta['pid'],probe['identity'])
        return {'mask':result['readiness_mask'],'digest':result['state_digest'],'peer':result['peer_identity'],'workers':result['state']['workers']}
    headers={}
    if probe.get('token_file'):headers['Authorization']='Bearer '+Path(probe['token_file']).read_text().strip()
    body=json.dumps(probe['body']).encode() if 'body' in probe else None
    if body is not None:headers['Content-Type']='application/json'
    url=urlsplit(probe['url'])
    if url.scheme!='http' or url.hostname!='127.0.0.1':raise ValueError('Probe must target configured local runtime')
    client=http.client.HTTPConnection(url.hostname,url.port,timeout=3)
    try:
        client.request('POST' if body is not None else 'GET',url.path,body=body,headers=headers)
        response=client.getresponse();value=json.loads(response.read())
        if response.status!=200:raise RuntimeError('Readback HTTP '+str(response.status))
        return {'http_status':response.status,'response':value}
    finally:client.close()

def activate(manifest_path, include_additional=True):
    manifest=json.loads(Path(manifest_path).read_text());results=[]
    for service in manifest['services']:
        row={'id':service['id']}
        try:
            command=service['command'];found=processes(command)
            if len(found)>1:raise RuntimeError('Multiple existing command owners; retain them for reconciliation')
            if not found:
                if not shutil.which(command[0]):raise FileNotFoundError('Runtime executable absent')
                if service.get('required_file') and not Path(service['required_file']).exists():raise FileNotFoundError('Required deployment artifact absent')
                root=Path(manifest['state_root']);root.mkdir(parents=True,exist_ok=True)
                env=dict(os.environ,**service.get('environment',{}))
                log=root/(service['id']+'.log')
                with log.open('ab') as stream:
                    log.chmod(0o600)
                    child=subprocess.Popen(command,cwd=service['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,start_new_session=True)
                found=[child.pid];row['action']='STARTED'
            else:row['action']='ADOPTED'
            row['pid']=found[0]
            for attempt in range(3):
                try:row['readback']=readback(service);break
                except Exception:
                    if attempt==2:raise
                    time.sleep(.1)
            row['state']='READY' if service['probe'].get('readiness',True) else 'RESPONDING'
        except Exception as exc:row.update(state='UNRESOLVED',reason=type(exc).__name__+': '+str(exc))
        results.append(row)
    for service in (manifest.get('additional_services',[]) if include_additional else []):
        row={'id':service['id'],'state':'CONFIGURED'}
        if service['kind']=='docker_family':
            try:
                subprocess.run(['docker','info','--format','{{.ServerVersion}}'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
                result=subprocess.run(service['command'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=180)
                if result.returncode:raise RuntimeError('Existing family launcher failed; inspect its owner state')
                row['state']='ACTIVATED_BY_OWNER_LAUNCHER'
            except Exception as exc:row.update(state='UNRESOLVED',reason=type(exc).__name__)
        elif service['kind']=='bundle':
            if not Path(service['artifact']).exists():row.update(state='UNRESOLVED',reason='Deployment bundle absent in current environment')
        results.append(row)
    if not include_additional:
        results.extend({'id':service['id'],'state':'NOT_CHECKED_BY_WATCHER',
                        'scope':'Owner family bootstrap is an explicit operation, not a watchdog heartbeat'}
                       for service in manifest.get('additional_services',[]))
    result={'schema':'keddeh.service-activation-receipt.v1','observed_at':time.time(),'services':results}
    state=Path(manifest['state_root']);state.mkdir(parents=True,exist_ok=True)
    temp=state/'readback.pending';temp.write_text(json.dumps(result,indent=2));temp.chmod(0o600);temp.replace(state/'readback.json')
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--watch',action='store_true');args=parser.parse_args()
    state=Path(json.loads(args.manifest.read_text())['state_root']);state.mkdir(parents=True,exist_ok=True)
    with (state/('watcher.lock' if args.watch else 'activation.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stopping=False
        def halt(*unused):
            nonlocal stopping
            stopping=True
        signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
        while not stopping:
            if args.watch:
                with (state/'activation.lock').open('a') as mutation:
                    fcntl.flock(mutation,fcntl.LOCK_EX)
                    result=activate(args.manifest, include_additional=False)
            else:result=activate(args.manifest)
            print(json.dumps(result),flush=True)
            if not args.watch:break
            for _ in range(100):
                if stopping:break
                time.sleep(.1)

if __name__=='__main__':main()
