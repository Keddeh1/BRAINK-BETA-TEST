import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

from braink_node.canonical import canonical_bytes
from braink_node.protocol.catalogue import compile_catalogue
from braink_node.storage import atomic_write


def activate(context, revision, rows):
    artifacts = context.runtime / 'releases' / revision / 'wheels'
    artifacts.mkdir(parents=True, exist_ok=True)
    wheels = []
    prefixes = {'core': 'braink_node_core-', 'cli': 'braink_cli_node-', 'ide': 'braink_ide_node-', 'ci': 'braink_ci_node-'}
    for row in rows:
        if row['detail'].get('source_commit') != revision:
            raise ValueError('Qualified build source revision differs')
        artifact = next(item for item in row['detail']['artifacts'] if Path(item['path']).name.startswith(prefixes[row['sector']]) and item['path'].endswith('.whl'))
        content = context.website({'op': 'artifact', 'id': row['id'], 'path': artifact['path']}, binary=True)
        if hashlib.sha256(content).hexdigest() != artifact['sha256']:
            raise ValueError('Qualified wheel download differs')
        path = artifacts / Path(artifact['path']).name
        atomic_write(path, content)
        wheels.append((row['sector'], path))
    source = artifacts.parent / 'source'
    if not source.exists():
        repository = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=context.desired_source, text=True).strip()
        prefix = subprocess.check_output(['git', 'rev-parse', '--show-prefix'], cwd=context.desired_source, text=True).strip().rstrip('/')
        archive = subprocess.check_output(['git', 'archive', revision + (':' + prefix if prefix else '')], cwd=repository)
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(source, filter='data')
    catalogue = compile_catalogue(source)
    for sector, path in wheels:
        with zipfile.ZipFile(path) as wheel:
            for family in catalogue['families']:
                if family['sector'] == sector:
                    filename = family['source_path'].split('/src/', 1)[1]
                    if hashlib.sha256(wheel.read(filename)).hexdigest() != family['source_sha256']:
                        raise ValueError('Installed family source differs from qualified revision')
    subprocess.run([str(context.runtime / 'venv/bin/python'), '-m', 'pip', 'install', '--no-deps', '--force-reinstall',
                    *[str(path) for _, path in wheels]], check=True, capture_output=True, text=True)
    config = {**context.config, 'source': str(source), 'active_revision': revision}
    config_path = Path(context.config['config_path'])
    atomic_write(config_path, canonical_bytes(config))
    config_path.chmod(0o600)
    activation = {'source_commit': revision, 'qualified_source': str(source), 'state': 'PREPARED',
                  'wheels': [{'sector': sector, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for sector, path in wheels]}
    atomic_write(context.root / 'activation-prepared.json', canonical_bytes(activation))
    return activation


def run(context):
    desired = compile_catalogue(context.desired_source)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=context.desired_source, text=True).strip()
    if desired['definition_sha256'] == context.catalogue()['definition_sha256']:
        revision = context.config.get('active_revision', revision)
    jobs = []
    for sector in ('core', 'cli', 'ide', 'ci'):
        def submit(identity):
            return context.website({'op': 'submit', 'id': identity, 'sector': sector, 'operation': 'qualify', 'parameters': {'source_commit': revision}})
        jobs.append({'sector': sector, **context.action('clean-build', {'revision': revision, 'sector': sector}, submit)})
    statuses = {row['id']: row for row in context.website({'op': 'list'})['jobs']}
    results = [{'sector': row['sector'], 'job': row['id'], 'status': statuses.get(row['id'], {}).get('status', 'queued')} for row in jobs]
    qualified = all(row['status'] == 'passed' for row in results)
    activation = None
    if qualified and revision != context.config.get('active_revision'):
        activation = context.action('activate-qualified-revision', revision, lambda key: activate(context, revision, [statuses[row['id']] for row in jobs]))
    return {'state': 'QUALIFIED' if qualified else 'AWAITING_BUILD_RESULTS', 'source_commit': revision, 'jobs': results, 'activation': activation}
