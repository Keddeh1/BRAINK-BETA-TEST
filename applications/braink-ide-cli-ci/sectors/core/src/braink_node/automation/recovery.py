import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from uuid import uuid4

from braink_node.canonical import canonical_bytes
from braink_node.storage import atomic_write
from braink_node.owner_vfs.store import VFSStore


def checkpoint(context):
    directory = context.root / 'checkpoints' / uuid4().hex
    directory.mkdir(parents=True)
    def copy_group(original, output):
        paths = [p for p in original.rglob('*') if p.is_file() and not p.name.endswith(('-wal', '-shm', '.lock'))]
        # Back up index databases before their VFS databases, then copy immutable objects.
        for path in sorted(paths, key=lambda p: (p.suffix not in ('.sqlite3', '.db'), len(p.parts), str(p))):
            destination = output / path.relative_to(original)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix in ('.sqlite3', '.db'):
                with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as source, sqlite3.connect(destination) as target:
                    source.backup(target)
            else:
                shutil.copy2(path, destination)
        for path in original.rglob('objects/*/*/*'):
            if path.is_file():
                destination = output / path.relative_to(original)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copy2(path, destination)
    original = context.state / 'instances'
    if original.exists():
        manifest_path = original / 'deployment.json'
        if manifest_path.exists():
            (directory / 'instances').mkdir()
            shutil.copy2(manifest_path, directory / 'instances/deployment.json')
        for instance in sorted(original.iterdir()):
            if instance.is_dir() and (instance / 'ceremony.json').exists():
                with (instance / 'ceremony.lock').open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    copy_group(instance, directory / 'instances' / instance.name)
    original = context.state / 'protocol-mesh'
    if original.exists():
        copy_group(original, directory / 'protocol-mesh')
    manifest = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob('*')) if p.is_file()}
    atomic_write(directory / 'checkpoint.json', canonical_bytes({'schema': 'braink.runtime-checkpoint.v1', 'files': manifest}))
    return directory


def restore(checkpoint_root, destination):
    checkpoint_root, destination = Path(checkpoint_root), Path(destination)
    manifest = json.loads((checkpoint_root / 'checkpoint.json').read_text())
    for relative, expected in manifest['files'].items():
        path = (checkpoint_root / relative).resolve()
        if not path.is_relative_to(checkpoint_root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Checkpoint content differs')
    destination.mkdir(parents=True, exist_ok=False)
    for relative in manifest['files']:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(checkpoint_root / relative, target)
    verified = 0
    for ceremony in (destination / 'instances').glob('*/ceremony.json'):
        state = json.loads(ceremony.read_text())
        store = VFSStore(ceremony.parent / 'vfs')
        if not store.verify_receipt_chain()['verified']:
            raise RuntimeError('Restored receipt chain differs')
        store.read_content(state['steps']['INSTANTIATE_VFS']['digest'])
        state['reconstruction'] = {'original_vfs_root': state['steps']['INSTANTIATE_VFS']['root'], 'checkpoint': checkpoint_root.name}
        state['steps']['INSTANTIATE_VFS']['root'] = str(ceremony.parent / 'vfs')
        atomic_write(ceremony, canonical_bytes(state))
        verified += 1
    return {'verified_instance_stores': verified, 'files_verified': len(manifest['files']), 'destination': str(destination)}


def run(context):
    source = checkpoint(context)
    reconstructed = context.root / 'reconstructed' / source.name
    evidence = restore(source, reconstructed)
    original_deployment = context.deployment()
    restored_deployment = json.loads((reconstructed / 'instances/deployment.json').read_text()) if (reconstructed / 'instances/deployment.json').exists() else {'instances': []}
    if original_deployment != restored_deployment:
        raise RuntimeError('Reconstructed deployment differs')
    restored_mesh = reconstructed / 'protocol-mesh'
    network_readback = None
    if restored_mesh.exists():
        import threading
        from braink_node.protocol.mesh import MeshStore, mesh_server, owner_state
        from braink_node.protocol.transport import JSONTransport
        token = Path(context.config['mesh_token_file']).read_text().strip()
        mesh = MeshStore(restored_mesh, owner_state(context.config['owner_export']))
        for row in restored_deployment['instances']:
            mesh.subscription(row['instance'])
        server = mesh_server(mesh, '127.0.0.1', 0, token)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            if restored_deployment['instances']:
                probe = restored_deployment['instances'][0]['instance']
                observed = JSONTransport('http://127.0.0.1:' + str(server.server_port), token).request('/subscription', {'instance': probe})
                network_readback = {'instance': probe, 'state': observed['state'], 'verified_restored_subscriptions': len(restored_deployment['instances'])}
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    return {'state': 'RECONSTRUCTION_VERIFIED', 'restored_network_readback': network_readback, 'checkpoint': source.name, **evidence,
            'host_loss_exercised': False, 'host_reboot_exercised': False,
            'observation': 'Clean destination reconstruction with actual SQLite backups, content hashes and instance receipt-chain verification.'}
