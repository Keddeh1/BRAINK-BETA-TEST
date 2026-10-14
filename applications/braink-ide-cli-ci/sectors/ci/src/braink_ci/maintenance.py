"""Release disposable tools from completed successful CI runs, retaining evidence."""
import json
from pathlib import Path
import shutil


def reclaim_qualified_environments(root):
    active = []
    for process in Path('/proc').glob('[0-9]*'):
        try:
            active.append((process / 'cmdline').read_bytes())
            active.append(str((process / 'cwd').resolve(strict=True)).encode())
        except OSError:
            continue
    removed = []
    for run in (root / 'runs').glob('*'):
        target = run / 'qualification-venv'
        if run.is_symlink() or target.is_symlink() or not (target / 'pyvenv.cfg').is_file():
            continue
        try:
            report = json.loads((run / 'report.json').read_text())
            if report.get('status') != 'passed' or not report.get('finished'):
                continue
            if any(str(run).encode() in command for command in active):
                continue
            shutil.rmtree(target)
            removed.append(run.name)
        except (OSError, ValueError):
            # Preserve uncertain cases; a later cycle can retry operational failures.
            continue
    return {'removed': removed, 'retained': 'source, artifacts, logs, manifests and terminal receipts'}
