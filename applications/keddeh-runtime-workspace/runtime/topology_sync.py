"""Mirror actual resident definitions, instance stores and recorded ceremonies."""
import argparse
import fcntl
import hashlib
import json
import sqlite3
import time
import urllib.request
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def summary(value):
    if not isinstance(value, dict):
        return None
    return {key: value[key] for key in ('state', 'status', 'receipt_id', 'receipt_digest', 'artifact_digest', 'digest', 'at', 'path', 'prefix', 'subscriber', 'cursor', 'updated_at', 'definition_id', 'definition_sha256', 'instance', 'vfs_prefix', 'relations') if key in value}


def read_instance(root, row):
    directory = root / row['instance']
    ceremony = json.loads((directory / 'ceremony.json').read_text())
    step = ceremony['steps']['INSTANTIATE_VFS']
    digest = step['digest']
    body = (directory / 'vfs/objects' / digest[:2] / digest[2:4] / digest).read_bytes()
    if hashlib.sha256(body).hexdigest() != digest:
        raise ValueError('INSTANCE_DEFINITION_DIGEST_MISMATCH: ' + row['instance'])
    definition = json.loads(body)
    declared = dict(definition)
    declared_digest = declared.pop('definition_sha256')
    if hashlib.sha256(canonical(declared)).hexdigest() != declared_digest or declared_digest != ceremony['definition_sha256']:
        raise ValueError('DEFINITION_REVISION_MISMATCH: ' + row['instance'])
    if definition['id'] != row['definition_id'] or ceremony['occurrence'] != row['occurrence']:
        raise ValueError('INSTANCE_IDENTITY_MISMATCH: ' + row['instance'])
    with sqlite3.connect('file:' + str(directory / 'vfs/vfs.sqlite3') + '?mode=ro', uri=True) as db:
        objects = [dict(zip(('path', 'digest', 'size', 'created_at'), values)) for values in db.execute('SELECT a.path,a.digest,a.size,a.created_at FROM paths p JOIN artifacts a ON a.digest=p.digest ORDER BY a.path')]
    steps = {}
    for name, value in ceremony['steps'].items():
        steps[name] = summary(value) or {}
        for key in ('actor', 'observer'):
            nested = value.get(key)
            if nested:
                steps[name][key] = summary(nested)
                for child in ('receipt', 'actor_receipt', 'artifact'):
                    if child in nested:
                        steps[name][key][child] = summary(nested[child])
    kind = definition['id'].split('://')[0]
    node = {'id': definition['id'], 'kind': kind, 'sector': definition.get('sector'), 'definition_sha256': definition['definition_sha256'], 'implementation': definition.get('implementation'), 'contract': definition.get('contract'), 'members': definition.get('modules', definition.get('families', definition.get('variants', [])))}
    instance = {'id': row['instance'], 'definition_id': row['definition_id'], 'definition_sha256': ceremony['definition_sha256'], 'occurrence': row['occurrence'], 'state': ceremony['state'], 'vfs': {'store': str(directory / 'vfs'), 'definition_digest': digest, 'objects': [obj for obj in objects if not obj['path'].startswith('/topology/')]}, 'ceremony': steps}
    return node, instance


def capture(runtime_root):
    root = runtime_root / 'state/instances'
    manifest_path = root / 'deployment.json'
    before = manifest_path.read_bytes()
    manifest = json.loads(before)
    nodes, instances = {}, []
    for row in manifest['instances']:
        node, instance = read_instance(root, row)
        if node['id'] in nodes and nodes[node['id']]['definition_sha256'] != node['definition_sha256']:
            raise ValueError('INCONSISTENT_DEFINITION_REVISION')
        nodes[node['id']] = node
        instances.append(instance)
    if manifest_path.read_bytes() != before:
        raise ValueError('DEPLOYMENT_CHANGED_DURING_CAPTURE')
    return {'schema': 'keddeh.runtime-topology.v1', 'observed_at': time.time(), 'source': {'kind': 'RESIDENT_INSTANCE_READBACK', 'manifest_sha256': hashlib.sha256(before).hexdigest(), 'catalogue_sha256': manifest['catalogue_sha256'], 'subscription_observation': 'RECORDED_CEREMONY; capture does not actively probe network subscriptions'}, 'nodes': sorted(nodes.values(), key=lambda n: n['id']), 'instances': instances}


def publish(snapshot, credential_path, endpoint):
    credential = json.loads(credential_path.read_text())['agent']
    document = canonical(snapshot).decode()
    digest = hashlib.sha256(document.encode()).hexdigest()
    payload = canonical({'op': 'topology-observation', 'document': document, 'digest': digest})
    request = urllib.request.Request(endpoint, data=payload, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + credential})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    if result.get('digest') != digest or not result.get('current'):
        raise ValueError('HOSTED_TOPOLOGY_READBACK_NOT_CURRENT')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--service-root', type=Path, required=True)
    parser.add_argument('--endpoint', default='https://keddeh-systems-runtime.aboudy65097.chatgpt.site/api/braink-ci/worker')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', type=float, default=60)
    args = parser.parse_args()
    args.service_root.mkdir(parents=True, exist_ok=True)
    with (args.service_root / 'sync.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous_fingerprint = None
        previous_result = {}
        while True:
            try:
                snapshot = capture(args.runtime_root)
                own_manifest = args.service_root / 'state/instances/deployment.json'
                if own_manifest.exists():
                    own = capture(args.service_root)
                    snapshot['nodes'].extend(own['nodes'])
                    snapshot['instances'].extend(own['instances'])
                    snapshot['source'] = {'resident': snapshot['source'], 'mirror_node': own['source']}
                fingerprint = hashlib.sha256(canonical({key: value for key, value in snapshot.items() if key != 'observed_at'})).hexdigest()
                if fingerprint != previous_fingerprint:
                    result = publish(snapshot, args.runtime_root / 'worker-credential.json', args.endpoint)
                    if own_manifest.exists():
                        from braink_node.owner_vfs.store import VFSStore
                        from braink_node.owner_vfs.model import ArtifactWrite
                        manifest = json.loads(own_manifest.read_text())
                        family = next(row for row in manifest['instances'] if row['definition_id'].startswith('family://'))
                        store = VFSStore(args.service_root / 'state/instances' / family['instance'] / 'vfs')
                        record, _ = store.write(ArtifactWrite('/topology/latest.json', canonical(snapshot), family['instance'], media_type='application/json'))
                        store.verify(record.digest)
                    previous_fingerprint, previous_result = fingerprint, result
                else:
                    result = previous_result
                state = {'at': time.time(), 'status': 'CURRENT', **result}
            except Exception as error:
                state = {'at': time.time(), 'status': 'ERROR', 'error': type(error).__name__}
                if args.once:
                    raise
            temporary = args.service_root / 'sync-status.tmp'
            temporary.write_text(json.dumps(state, indent=2))
            temporary.replace(args.service_root / 'sync-status.json')
            print(json.dumps(state), flush=True)
            if args.once:
                break
            time.sleep(args.interval)


if __name__ == '__main__':
    main()
