import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore
from braink_node.protocol.catalogue import compile_catalogue, digest
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.transport import HubSubscription, JSONTransport
from braink_node.storage import atomic_write


class Context:
    def __init__(self, config):
        self.config = config
        self.source = Path(config['source']).resolve(strict=True)
        self.desired_source = Path(config.get('desired_source', config['source'])).resolve(strict=True)
        self.runtime = Path(config['runtime_root']).resolve(strict=True)
        self.state = self.runtime / 'state'
        self.root = self.state / 'automation'
        self.root.mkdir(parents=True, exist_ok=True)
        self.vfs = VFSStore(self.root / 'vfs')
        self.db = self.root / 'automation.sqlite3'
        self.hub_transport = JSONTransport(config['vfs_url'], Path(config['vfs_token_file']).read_text().strip())
        self.hub = HubSubscription(self.hub_transport)
        self.mesh = JSONTransport(config['mesh_url'], Path(config['mesh_token_file']).read_text().strip())
        self.manager = InstanceManager(self.state / 'instances', self.hub, self.mesh)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,target TEXT,created REAL,digest TEXT,document TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY,kind TEXT,document TEXT)')
        self._catalogue = None

    def connect(self):
        db = sqlite3.connect(self.db, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        return db

    def catalogue(self):
        if self._catalogue is None:
            self._catalogue = compile_catalogue(self.source)
        return self._catalogue

    def deployment(self):
        path = self.state / 'instances/deployment.json'
        return json.loads(path.read_text()) if path.exists() else {'instances': [], 'sectors': [], 'catalogue_sha256': None}

    def definitions(self):
        catalogue = self.catalogue()
        rows = dict(catalogue['modules'])
        for kind in ('families', 'variants', 'colonies'):
            rows.update({row['id']: row for row in catalogue[kind]})
        return rows

    def record(self, target, document):
        identity = uuid4().hex
        payload = {'schema': 'braink.automation-evidence.v1', 'id': identity, 'target': target, 'created': time.time(), **document}
        artifact, actor = self.vfs.write(ArtifactWrite('/evidence/' + identity, canonical_bytes(payload), target, media_type='application/json'))
        observed = self.vfs.verify(artifact.digest)
        result = {**payload, 'artifact_digest': artifact.digest, 'actor': actor.as_dict(), 'observer': observed}
        with self.connect() as db:
            db.execute('INSERT INTO evidence VALUES(?,?,?,?,?)', (identity, target, payload['created'], artifact.digest, json.dumps(result)))
        atomic_write(self.root / (target + '.json'), canonical_bytes(result))
        pending = self.root / 'website-outbox'
        pending.mkdir(exist_ok=True)
        atomic_write(pending / (identity + '.json'), canonical_bytes({'op': 'architecture-observation', 'evidence': result, 'artifact_body': canonical_bytes(payload).decode()}))
        self.flush_evidence()
        return result

    def flush_evidence(self):
        for path in sorted((self.root / 'website-outbox').glob('*.json')):
            try:
                value = json.loads(path.read_text())
                receipt = self.website(value)
                if receipt.get('artifact_digest') != value['evidence']['artifact_digest'] or not receipt.get('stored'):
                    raise RuntimeError('Website evidence readback differs')
                path.unlink()
            except Exception as error:
                atomic_write(self.root / 'website-publication-error.json', canonical_bytes({'exception': type(error).__name__, 'reason': str(error), 'pending': path.name}))
                break

    def latest(self, target):
        with self.connect() as db:
            row = db.execute('SELECT document FROM evidence WHERE target=? ORDER BY created DESC LIMIT 1', (target,)).fetchone()
        if row:
            result = json.loads(row['document'])
            self.vfs.read_content(result['artifact_digest'])
            return result
        return None

    def website(self, payload, binary=False):
        import urllib.request
        token = json.loads((self.runtime / 'worker-credential.json').read_text())['agent']
        request = urllib.request.Request(self.config['website'].rstrip('/') + '/api/braink-development/worker',
            data=canonical_bytes(payload), headers={'Content-Type': 'application/json', 'User-Agent': 'BRAINK-CI/0.1', 'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read() if binary else json.load(response)

    def action(self, kind, identity, execute):
        """Persist intent before executing an idempotent owner operation, then its readback."""
        key = digest({'kind': kind, 'identity': identity})[:32]
        with self.connect() as db:
            old = db.execute('SELECT document FROM actions WHERE id=?', (key,)).fetchone()
            if old and json.loads(old['document']).get('state') == 'COMPLETED':
                return json.loads(old['document'])
            db.execute('INSERT INTO actions VALUES(?,?,?) ON CONFLICT(id) DO NOTHING', (key, kind, json.dumps({'state': 'DECLARED'})))
        result = {'state': 'COMPLETED', 'id': key, 'result': execute(key)}
        with self.connect() as db:
            db.execute('UPDATE actions SET document=? WHERE id=?', (json.dumps(result), key))
        return result
