"""Read-only live qualification while the existing canonical writer runs."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import time

from hci import RuntimePanel, render


def qualify(name):
    root = Path('/workspace/braink-setup/families/SERVERSPACE/runtime/substrate-' + name)
    identity = 'serverspace/substrate-' + name
    panel = RuntimePanel(root, identity)
    before = panel.read()
    with ThreadPoolExecutor(max_workers=8) as executor:
        frames = list(executor.map(lambda _: panel.dispatch('R'), range(32)))
    for frame in frames:
        assert frame['readiness_mask'] == 7
        assert frame['authentication']['mutual']
        assert frame['state']['I'] == identity
        for width in (20, 80, 83):
            assert all(len(line) == width for line in render(frame, width).splitlines())
    rejected = 0
    for command in ('M', 'A', 'PURGE'):
        try: panel.dispatch(command)
        except ValueError: rejected += 1
    after = panel.read()
    assert after['state']['I'] == before['state']['I']
    assert after['state']['q'] >= before['state']['q']
    api = json.loads((root/'api.json').read_text())
    connection = http.client.HTTPConnection(api['host'], api['port'], timeout=3)
    connection.request('GET', '/api/substrate')
    response = connection.getresponse()
    body = json.loads(response.read())
    connection.close()
    assert response.status == 200 and body['readiness_mask'] == 7
    return {'identity': identity, 'root': str(root), 'refreshes': len(frames),
            'tested_widths': [20,80,83], 'rejected_mutation_controls': rejected,
            'before_q': before['state']['q'], 'after_q': after['state']['q'],
            'mutual_authentication': True, 'readiness_mask': after['readiness_mask'],
            'state_digest': after['state_digest'], 'crc32': after['crc32'],
            'api': {'host': api['host'], 'port': api['port'],
                    'path': '/api/substrate', 'http_status': response.status}}


if __name__ == '__main__':
    evidence = {'schema': 'keddeh.hci-live-qualification.v1',
                'observed_at': time.time(),
                'scope': 'Authenticated read-only diagnostics; no consensus or mutation admission claim',
                'instances': [qualify(name) for name in ('auth-canary','replica','primary')]}
    source = Path(__file__).parent/'reference/supplied-web4-hci.txt'
    evidence['supplied_source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    print(json.dumps(evidence, indent=2))
