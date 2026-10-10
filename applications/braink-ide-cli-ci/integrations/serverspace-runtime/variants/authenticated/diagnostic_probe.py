"""Live loopback probes and bounded incident receipts; never clears substrate state."""
import argparse
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.parse import urlsplit

MAX_BYTES = 5 * 1024 * 1024
MAX_TICKETS = 200


def seal(record):
    # Required concatenation; an integrity digest, not a digital signature.
    return hashlib.sha256(''.join(str(record[k]) for k in
        ('incidentId', 'requestedUri', 'timestamp', 'clientIp')).encode()).hexdigest()


def incident(uri, category, detail):
    category = ''.join(c for c in category.upper() if c.isascii() and (c.isalnum() or c == '_'))
    timestamp = str(time.time_ns())
    hash8 = hashlib.sha256((uri + ':' + category + ':' + detail).encode()).hexdigest()[:8]
    value = {'incidentId': 'KEX-404-INC-' + category + '-' + hash8,
             'requestedUri': uri, 'timestamp': timestamp, 'clientIp': '127.0.0.1',
             'detail': detail, 'state_policy': 'retained; diagnostic does not mutate substrate'}
    value['seal'] = seal(value)
    value['record_digest'] = hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return value


def persist(directory, record):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / 'IT_INCIDENT_DISPATCH_LEDGER.ndjson'
    line = json.dumps(record, sort_keys=True).encode() + b'\n'
    if len(line) > MAX_BYTES:
        raise ValueError('Incident exceeds ledger ceiling')
    with open(directory / '.ledger.lock', 'a+b') as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        records = []
        if path.exists():
            # Existing oversize ledgers are refused rather than silently erased.
            if path.stat().st_size > MAX_BYTES:
                raise ValueError('Existing ledger exceeds ceiling; reconciliation required')
            records = path.read_bytes().splitlines(keepends=True)
            for old in records: json.loads(old)
        records = (records + [line])[-MAX_TICKETS:]
        size = sum(map(len, records))
        while size > MAX_BYTES:
            size -= len(records.pop(0))
        fd, name = tempfile.mkstemp(dir=directory, prefix='.incident-')
        try:
            with os.fdopen(fd, 'wb') as target:
                target.writelines(records)
                target.flush()
                os.fsync(target.fileno())
            os.replace(name, path)
            dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        finally:
            if os.path.exists(name): os.unlink(name)
    return str(path)


def probe(uri):
    parsed = urlsplit(uri)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.username:
        raise ValueError('This probe accepts explicit HTTP loopback endpoints only')
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=3)
    try:
        connection.request('GET', parsed.path + ('?' + parsed.query if parsed.query else '') or '/')
        response = connection.getresponse()
        body = response.read(1024 * 1024 + 1)
        if len(body) > 1024 * 1024: raise ValueError('Probe body exceeds 1MiB')
        result = {'uri':uri, 'http_status': response.status, 'body_sha256':hashlib.sha256(body).hexdigest(),
                  'body_bytes':len(body)}
        try: result['response_json'] = json.loads(body)
        except (ValueError, UnicodeError): pass
        return result
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ledger-dir', required=True)
    parser.add_argument('--url', action='append')
    parser.add_argument('--runtime-root', action='append', default=[])
    args = parser.parse_args()
    snapshots = []
    from hci import RuntimePanel
    for root in args.runtime_root:
        metadata = json.loads((Path(root)/'daemon.json').read_text())
        snapshots.append(RuntimePanel(root, metadata['identity']).read())
    urls = args.url or ['http://127.0.0.1:19100/', 'http://127.0.0.1:3000/serverspace-app/',
                        'http://127.0.0.1:19100/api/health', 'http://127.0.0.1:19100/api/telemetry']
    results = []
    for uri in urls:
        try:
            value = probe(uri)
            if value['http_status'] != 200:
                fault = incident(uri, 'HTTP_' + str(value['http_status']), 'Endpoint returned non-200')
                value['incident'] = fault
                persist(args.ledger_dir, fault)
        except Exception as exc:
            fault = incident(uri, 'PROBE_FAILURE', type(exc).__name__ + ': ' + str(exc))
            persist(args.ledger_dir, fault)
            value = {'uri':uri, 'incident':fault}
        results.append(value)
    print(json.dumps({'observed_at':time.time(), 'results':results,
                      'retained_runtime_snapshots':snapshots,
                      'scope':'Live HTTP readback; SHA256 receipts do not certify consensus, hardware or endpoint cryptography'},indent=2))
    return 1 if any('incident' in value for value in results) else 0


if __name__ == '__main__': raise SystemExit(main())
