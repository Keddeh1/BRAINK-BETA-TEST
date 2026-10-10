"""Add SDK instances to the existing supervisor, canary first; preserve all owners."""
import asyncio
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from diagnostic_probe import probe


def atomic(path,value):
    temp=path.with_suffix('.pending')
    with temp.open('w') as output:
        json.dump(value,output,indent=2);output.flush();os.fsync(output.fileno())
    temp.replace(path)
    dfd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(dfd)
    finally:os.close(dfd)


def main():
    source=Path(__file__).resolve().parent
    repo=next(parent for parent in source.parents if (parent/'.git').exists())
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    runtime=Path('/workspace/braink-setup/families/SERVERSPACE/runtime')
    software=runtime/'software'/revision
    if not software.exists():
        shutil.copytree(source,software,ignore=shutil.ignore_patterns('__pycache__'))
        core=repo/'applications/braink-ide-cli-ci/sectors/core/src/braink_node'
        shutil.copytree(core,software/'dependencies/braink_node',ignore=shutil.ignore_patterns('__pycache__'))
    activation=Path('/workspace/braink-setup/service-activation')
    manifest_path=activation/'source/services.json'
    rollback=runtime/('pre-resolve-services-'+revision+'.json')
    if not rollback.exists():shutil.copy2(manifest_path,rollback)
    instances=[]
    for name,port in (('auth-canary',19091),('replica',19092),('primary',19093)):
        service_id='serverspace-resolve-'+name
        root=runtime/('resolve-'+name)
        identity='serverspace/resolve-'+name
        with (activation/'activation.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            manifest=json.loads(manifest_path.read_text())
            existing=next((s for s in manifest['services'] if s['id']==service_id),None)
            if existing is None:
                with socket.socket() as check:check.bind(('127.0.0.1',port))
                service={'id':service_id,'command':[sys.executable,str(software/'resolve_mcp.py'),
                    '--root',str(root),'--substrate-root',str(runtime/('substrate-'+name)),
                    '--identity',identity,'--port',str(port)],'cwd':str(software),
                    'environment':{'PYTHONPATH':str(software/'dependencies')},
                    'probe':{'kind':'http','url':'http://127.0.0.1:'+str(port)+'/health'}}
                manifest['services'].append(service)
                atomic(manifest_path,manifest)
            elif existing['command'][1]!=str(software/'resolve_mcp.py'):
                raise RuntimeError('Existing RESOLVE owner differs; preserved for reconciliation')
        for _ in range(150):
            try:
                result=probe('http://127.0.0.1:'+str(port)+'/health')
                assert result['http_status']==200 and result['response_json']['readiness_mask']==7
                break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('New instance not ready; rollout stops before next instance')
        from qualify_resolve_mcp import qualify
        url='http://127.0.0.1:'+str(port)+'/mcp'
        asyncio.run(qualify(url,identity))
        instances.append({'identity':identity,'root':str(root),'url':url})
    result={'source_commit':revision,'software':str(software),'rollback_manifest':str(rollback),
            'instances':instances,'scope':'Loopback official SDK services; independent VFS, retained substrate nodes'}
    atomic(runtime/'resolve-deployment.json',result)
    print(json.dumps(result))


if __name__=='__main__':main()
