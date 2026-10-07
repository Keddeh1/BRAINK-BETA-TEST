"""Own-runtime continuous integration trigger for the dedicated GitHub branch."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--branch', default='feat/braink-application-node')
    parser.add_argument('--website', default='https://www.keddeh.com')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    checkout = args.checkout.resolve(strict=True)
    agent = json.loads((root/'worker-credential.json').read_text())['agent']
    state = root/'branch-trigger.json'
    def git(*argv):return subprocess.check_output(['git',*argv],cwd=checkout,text=True).strip()
    while True:
        try:
            git('fetch','origin',args.branch)
            desired = git('rev-parse','FETCH_HEAD')
            previous = json.loads(state.read_text()) if state.exists() else {'commit':git('rev-parse','HEAD'),'jobs':[]}
            if previous['commit'] != desired and not (root/'branch-trigger-pending.json').exists():
                if git('status','--porcelain'):
                    raise RuntimeError('Source checkout has local edits; remote update retains them')
                git('merge','--ff-only',desired)
                changes = git('diff','--name-only',previous['commit'],desired).splitlines()
                prefix='applications/braink-ide-cli-ci/'
                changed=[p[len(prefix):] for p in changes if p.startswith(prefix)]
                sectors=set()
                for p in changed:
                    if p.startswith('sectors/core/') or p.startswith(('scripts/','tests/')):sectors.update(['core','cli','ide','ci'])
                    elif p.startswith('sectors/') and p.split('/')[1] in {'cli','ide','ci'}:sectors.add(p.split('/')[1])
                pending={'commit':desired,'jobs':[{'id':uuid.uuid4().hex,'sector':sector} for sector in sorted(sectors)]}
                # Persist IDs before transmission so replay cannot duplicate submissions.
                (root/'branch-trigger-pending.json').write_text(json.dumps(pending))
            pending_path=root/'branch-trigger-pending.json'
            if pending_path.exists():
                pending=json.loads(pending_path.read_text())
                for job in pending['jobs']:
                    request=urllib.request.Request(args.website.rstrip('/')+'/api/braink-development/worker',data=json.dumps({'op':'submit',**job,'operation':'qualify','parameters':{'source_commit':pending['commit']}}).encode(),headers={'User-Agent':'BRAINK-CI/0.1','Authorization':'Bearer '+agent,'Content-Type':'application/json'})
                    with urllib.request.urlopen(request,timeout=30) as response:
                        if response.status not in {200,202}:raise RuntimeError('CI submission failed')
                state.write_text(json.dumps(pending));pending_path.unlink()
                print(json.dumps({'event':'branch-ci-submitted','commit':pending['commit'],'sectors':[j['sector'] for j in pending['jobs']]}),flush=True)
            elif not state.exists():state.write_text(json.dumps(previous))
        except Exception as error:
            print(json.dumps({'event':'branch-ci-retry','reason':type(error).__name__}),flush=True)
            if args.once:raise
        if args.once:return
        time.sleep(15)


if __name__=='__main__':main()
