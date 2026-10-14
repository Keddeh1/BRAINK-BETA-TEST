"""Qualify installed wheels; retain evidence, release disposable tools on success."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
from braink_node.storage import atomic_write


def release_environment(run):
    target = run / 'qualification-venv'
    if target.is_symlink() or not (target / 'pyvenv.cfg').is_file():
        raise ValueError('Refuse cleanup of an unrecognised qualification environment')
    if not target.resolve().is_relative_to(run.resolve()):
        raise ValueError('Qualification environment escapes its run')
    shutil.rmtree(target)


def qualify(artifacts, run, sector='all'):
    artifacts = artifacts.resolve(strict=True)
    run = run.resolve(strict=True)
    wheels = list(artifacts.glob("*/*.whl"))
    if not wheels:
        raise SystemExit("Expected independently built sector wheels")
    venv.create(run / "qualification-venv", with_pip=True)
    python = run / "qualification-venv/bin/python"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps"] + [str(wheel) for wheel in wheels], check=True, env=environment)
    sectors = ["core", "cli", "ide", "ci"] if sector == "all" else [sector]
    for target in sectors:
        subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", f"test_{target}.py", "-v"], check=True, env=environment)
    if sector in {"all", "core"}:
        subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", "test_protocol.py", "-v"], check=True, env=environment)
    if sector in {"all", "core"}:
        subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", "test_automation.py", "-v"], check=True, env=environment)
    common = [str(python), "-m", "braink_cli.cli", "--workspace", str(run / "smoke-workspace"),
              "--state-dir", str(run / "smoke-state")]
    if sector in {"all", "cli"}:
        for command in (["init"], ["check", "--fail-on", "warn"], ["verify-ledger"]):
            subprocess.run(common + command, check=True, env=environment)
    evidence = {'schema': 'braink.installed-qualification.v1', 'status': 'passed',
                'sector': sector, 'wheels': [{'name': wheel.name,
                'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest()} for wheel in wheels],
                'interpreter': subprocess.check_output([str(python), '--version'], text=True).strip()}
    # Publish evidence before removing tools. Failed tests never reach cleanup.
    atomic_write(artifacts / 'installed-qualification.json', json.dumps(evidence, sort_keys=True).encode())
    release_environment(run)
    print(json.dumps({**evidence, 'disposable_environment_removed': True}))
    return evidence


if __name__ == '__main__':
    qualify(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'all')
