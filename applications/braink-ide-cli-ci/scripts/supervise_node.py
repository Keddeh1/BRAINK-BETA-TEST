"""Supervise this application's IDE and CI relay on the owner host."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--checkout', type=Path)
    parser.add_argument('--automation-config', type=Path)
    parser.add_argument('--owner-export', type=Path)
    parser.add_argument('--mesh-token-file', type=Path)
    parser.add_argument('--mesh-port', type=int, default=8766)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    lock = (root / 'supervisor.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    secret = json.loads((root / 'worker-credential.json').read_text())
    python = root / 'venv/bin/python'
    environment = os.environ.copy()
    environment.update(BRAINK_CI_AGENT_TOKEN=secret['agent'], BRAINK_WORKSPACE=str(root/'workspace'), BRAINK_CI_PYTHON=str(python))
    common = [str(python), '-m', 'braink_cli.cli', '--workspace', str(root/'workspace'), '--state-dir', str(root/'state')]
    definitions = {'node': common+['serve','--port',str(args.port)], 'relay': common+['ci','relay','--source',str(args.source.resolve(strict=True))]}
    if args.checkout:
        definitions['branch-trigger'] = [str(python), str(Path(__file__).resolve().parent/'watch_branch.py'), '--runtime-root',str(root),'--checkout',str(args.checkout)]
    if args.owner_export and args.mesh_token_file:
        definitions['protocol-mesh'] = common + ['protocol', 'mesh', '--owner-export', str(args.owner_export), '--mesh-token-file', str(args.mesh_token_file), '--port', str(args.mesh_port)]
    if args.automation_config:
        environment['BRAINK_AUTOMATION_CONFIG'] = str(args.automation_config.resolve(strict=True))
        definitions['architecture-automation'] = common + ['automate', 'serve']
        definitions['architecture-host'] = common + ['automate', 'host-server']
    processes = {}
    stopping = False
    activation = None
    def stop(*unused):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping:
            request = root / 'activation-request.json'
            if request.exists() and not (root/'state/ci/website-active.json').exists() and not (root/'state/ci/website-outbox.json').exists():
                candidate = json.loads(request.read_text())
                if candidate['state'] == 'READY_TO_RESTART':
                    activation = candidate
                    stopping = True
                    break
            for name, command in definitions.items():
                process = processes.get(name)
                if process is None or process.poll() is not None:
                    with (root/(name+'.log')).open('ab') as log:
                        processes[name] = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
                    (root/(name+'.pid')).write_text(str(processes[name].pid))
                    print(json.dumps({'service':name,'pid':processes[name].pid,'event':'started'}), flush=True)
            time.sleep(1)
    finally:
        for process in processes.values():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes.values():
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(process.pid, signal.SIGKILL)
        for name in definitions:(root/(name+'.pid')).unlink(missing_ok=True)
    if activation:
        (root/'activation-history').mkdir(exist_ok=True)
        (root/'activation-request.json').replace(root/'activation-history'/ (activation['source_commit']+'.json'))
        (root/'state/automation/activation-prepared.json').unlink(missing_ok=True)
        lock.close()
        import sys
        executable = str(Path(activation['qualified_source'])/'scripts/supervise_node.py')
        os.execv(sys.executable, [sys.executable, executable, *sys.argv[1:]])


if __name__ == '__main__':
    main()
