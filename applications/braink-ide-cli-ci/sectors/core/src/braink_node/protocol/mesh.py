"""Durable network subscriptions to canonical IL-LLM rows, preserving source identity."""
import hashlib
import importlib.util
import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import compare_digest

from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore


def owner_state(export_source):
    """Call the owner implementation; record its actual source and exported state hashes."""
    path = Path(export_source).resolve(strict=True)
    spec = importlib.util.spec_from_file_location('braink_owner_il_llm_export', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = module.il_llm_export()
    if state.get('schema') != 'braink.il-llm.canonical-state.v1':
        raise ValueError('Owner export schema differs')
    return {'state': state, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'state_sha256': hashlib.sha256(canonical_bytes(state)).hexdigest()}


class MeshStore:
    def __init__(self, root, canonical_state):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state = canonical_state
        self.vfs = VFSStore(self.root / 'vfs')
        self.database = self.root / 'mesh.sqlite3'
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS subscriptions(instance TEXT PRIMARY KEY, definition TEXT NOT NULL, document TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS message_ids(id TEXT PRIMARY KEY,sequence INTEGER NOT NULL,digest TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS messages(sequence INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL, recipient TEXT NOT NULL, digest TEXT NOT NULL)')

    def connect(self):
        db = sqlite3.connect(self.database, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        return db

    def subscribe(self, document):
        instance = document['instance']
        definition = document['definition_sha256']
        with self.lock, self.connect() as db:
            old = db.execute('SELECT definition FROM subscriptions WHERE instance=?', (instance,)).fetchone()
            if old and old['definition'] != definition:
                raise ValueError('Instance definition changed; instantiate a new revision')
            payload = {**document, 'schema': 'braink.il-llm.mesh-subscription.v1', 'owner_state': self.state,
                       'relations': document.get('relations', []), 'state': 'SUBSCRIBED'}
            record, actor = self.vfs.write(ArtifactWrite('/subscriptions/' + instance, canonical_bytes(payload), instance,
                                                        media_type='application/json'))
            observer = self.vfs.verify(record.digest)
            result = {**payload, 'artifact_digest': record.digest, 'actor': actor.as_dict(), 'observer': observer}
            db.execute('INSERT INTO subscriptions VALUES(?,?,?) ON CONFLICT(instance) DO UPDATE SET document=excluded.document',
                       (instance, definition, json.dumps(result)))
        return self.subscription(instance)

    def subscription(self, instance):
        with self.connect() as db:
            row = db.execute('SELECT document FROM subscriptions WHERE instance=?', (instance,)).fetchone()
        if not row:
            raise KeyError(instance)
        document = json.loads(row['document'])
        self.vfs.read_content(document['artifact_digest'])
        return document

    def exchange(self, sender, recipient, row, message_id=None):
        self.subscription(sender)
        self.subscription(recipient)
        if row.get('type') != 'RELATIONAL_ANCHOR':
            raise ValueError('Expected the owner governance RELATIONAL_ANCHOR contract')
        required = {'source', 'definition', 'relation', 'uncertainty', 'contradiction', 'next_route'}
        if not required.issubset(row):
            raise ValueError('Missing relational anchor fields')
        payload = {'sender': sender, 'recipient': recipient, 'row': row}
        with self.lock, self.connect() as db:
            digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
            old = db.execute('SELECT sequence,digest FROM message_ids WHERE id=?', (message_id,)).fetchone() if message_id else None
            if old:
                if old['digest'] != digest:
                    raise ValueError('Message identity replay differs')
                return {'sequence': old['sequence'], 'digest': digest, 'replayed': True, 'observer': self.vfs.verify(digest)}
            record, actor = self.vfs.write(ArtifactWrite('/messages/' + hashlib.sha256(canonical_bytes(payload)).hexdigest(),
                                                        canonical_bytes(payload), sender, media_type='application/json'))
            observer = self.vfs.verify(record.digest)
            cursor = db.execute('INSERT INTO messages(sender,recipient,digest) VALUES(?,?,?)', (sender, recipient, record.digest))
            sequence = cursor.lastrowid
            if message_id:
                db.execute('INSERT INTO message_ids VALUES(?,?,?)', (message_id, sequence, record.digest))
        return {'sequence': sequence, 'digest': record.digest, 'actor': actor.as_dict(), 'observer': observer}

    def inbox(self, instance, after=0):
        self.subscription(instance)
        with self.connect() as db:
            rows = db.execute('SELECT sequence,digest FROM messages WHERE recipient=? AND sequence>? ORDER BY sequence', (instance, after)).fetchall()
        return [{'sequence': row['sequence'], 'digest': row['digest'], 'document': json.loads(self.vfs.read_content(row['digest']))} for row in rows]


def mesh_server(store, host, port, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, document):
            content = canonical_bytes(document)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            supplied = self.headers.get('Authorization', '')
            if token and not compare_digest(supplied, 'Bearer ' + token):
                return self.send(401, {'error': 'Unauthorized'})
            try:
                document = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
                if self.path == '/subscribe':
                    result = store.subscribe(document)
                elif self.path == '/subscription':
                    result = store.subscription(document['instance'])
                elif self.path == '/exchange':
                    result = store.exchange(document['sender'], document['recipient'], document['row'], document.get('message_id'))
                elif self.path == '/inbox':
                    result = store.inbox(document['instance'], document.get('after', 0))
                else:
                    return self.send(404, {'error': 'Unknown operation'})
                self.send(200, result)
            except KeyError as error:
                self.send(404, {'error': str(error)})
            except (ValueError, TypeError) as error:
                self.send(409, {'error': str(error)})
            except Exception as error:
                from uuid import uuid4
                request_id = uuid4().hex
                print(json.dumps({'event': 'mesh-service-error', 'request_id': request_id, 'operation': self.path,
                                  'exception': type(error).__name__, 'reason': str(error)}), flush=True)
                self.send(500, {'error': type(error).__name__, 'request_id': request_id})
    return ThreadingHTTPServer((host, port), Handler)
