"""Observed host lifecycle derived from the supplied HCF provisioning sequence."""
import json,os,shutil,subprocess,time
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit
from braink_node.storage import atomic_write
from braink_node.canonical import canonical_bytes
from ollama_node import retain


def observe(endpoint):
    try:
        with urlopen(endpoint.rstrip('/')+'/api/version',timeout=5) as response:version=json.load(response)
        with urlopen(endpoint.rstrip('/')+'/api/tags',timeout=5) as response:inventory=json.load(response)
        if not isinstance(version.get('version'),str) or not isinstance(inventory.get('models'),list):
            return {'state':'INVALID_PROVIDER_RESPONSE'}
        return {'state':'SERVICE_OBSERVED','version':version['version'],'models':inventory['models']}
    except Exception as error:
        return {'state':'SERVICE_UNAVAILABLE','error_type':type(error).__name__}


def start(root,models_root,actor,endpoint='http://127.0.0.1:11434',executable='ollama',startup_timeout=30):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    observed=observe(endpoint)
    if observed['state']=='SERVICE_OBSERVED':
        receipt=retain(root/'vfs','/host/observation.json',observed,actor)
        return {**observed,'process_ownership':'EXISTING_SERVICE','model_store_binding':'NOT_OBSERVED','receipt':receipt}
    binary=shutil.which(executable)
    if binary is None:
        failure={'state':'EXECUTABLE_ABSENT','executable':executable}
        return {**failure,'receipt':retain(root/'vfs','/host/observation.json',failure,actor)}
    parsed=urlsplit(endpoint)
    if parsed.scheme!='http' or not parsed.hostname or parsed.path not in ('','/'):
        raise ValueError('Ollama serve requires an HTTP listener binding')
    models=Path(models_root).resolve();models.mkdir(parents=True,exist_ok=True)
    environment=os.environ.copy();environment['OLLAMA_HOST']=parsed.netloc;environment['OLLAMA_MODELS']=str(models)
    with (root/'ollama.log').open('ab') as log:
        child=subprocess.Popen([binary,'serve'],stdin=subprocess.DEVNULL,stdout=log,stderr=log,
            cwd=root,env=environment,start_new_session=True)
    process={'actor':actor,'pid':child.pid,'executable':str(Path(binary).resolve()),'models_root':str(models),
        'endpoint':endpoint,'state':'PROCESS_CREATED'}
    atomic_write(root/'host-process.json',canonical_bytes(process))
    deadline=time.monotonic()+startup_timeout
    while time.monotonic()<deadline:
        if child.poll() is not None:
            process.update(state='PROCESS_EXITED',exit_code=child.returncode);break
        observed=observe(endpoint)
        if observed['state']=='SERVICE_OBSERVED':
            process.update(state='SERVICE_OBSERVED',version=observed['version'],models=observed['models']);break
        time.sleep(0.25)
    else:
        process['state']='PROCESS_RUNNING_SERVICE_UNVERIFIED'
    atomic_write(root/'host-process.json',canonical_bytes(process))
    receipt=retain(root/'vfs','/host/observation.json',process,actor)
    return {**process,'receipt':receipt}


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--models-root',type=Path,required=True);parser.add_argument('--actor',required=True)
    parser.add_argument('--endpoint',default='http://127.0.0.1:11434');parser.add_argument('--executable',default='ollama')
    args=parser.parse_args();result=start(args.root,args.models_root,args.actor,args.endpoint,args.executable)
    print(json.dumps(result));return 0 if result['state']=='SERVICE_OBSERVED' else 1

if __name__=='__main__':raise SystemExit(main())
