"""Own-host sector CI: execute real checks and retain their actual outputs in the native VFS."""
import argparse, subprocess, sys
from pathlib import Path
from uuid import uuid4
from ollama_node import retain


def run(root):
    source=Path(__file__).resolve().parent
    assets=source.parent if list(source.parent.glob('*.test.mjs')) else source
    console_tests=sorted(assets.glob('*.test.mjs'))
    if not (source/'test_ollama_node.py').is_file() or not console_tests:
        raise FileNotFoundError('Sector qualification sources are missing')
    checks=[('native', [sys.executable,'-m','unittest','discover','-s',str(source),'-p','test_*.py']),
        ('console',[ 'node','--test', *[str(path) for path in console_tests]])]
    actor=Path(root).parent.name
    run_id=uuid4().hex
    results=[]
    for name,command in checks:
        result=subprocess.run(command,capture_output=True,text=True)
        document={'check':name,'command':command,'exit_code':result.returncode,
            'stdout':result.stdout,'stderr':result.stderr}
        receipt=retain(root,'/ci/'+run_id+'/'+name+'.json',document,actor)
        results.append({'check':name,'exit_code':result.returncode,'receipt':receipt})
    report={'run_id':run_id,'checks':results,'passed':all(row['exit_code']==0 for row in results),
        'live_inference_qualified':False}
    retain(root,'/ci/'+run_id+'/report.json',report,actor)
    return report


def main():
    import json
    parser=argparse.ArgumentParser();parser.add_argument('--vfs-root',type=Path,required=True)
    args=parser.parse_args();report=run(args.vfs_root);print(json.dumps(report))
    return 0 if report['passed'] else 1

if __name__=='__main__':sys.exit(main())
