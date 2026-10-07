import json
from pathlib import Path
from urllib.error import HTTPError


def run(context):
    observations, failures = [], []
    for label, transport, path, payload in [('owner-vfs', context.hub_transport, '/ready', None),
                                            ('mesh-subscription', context.mesh, '/subscription', {'instance': context.deployment()['instances'][0]['instance']})] if context.deployment()['instances'] else [('owner-vfs', context.hub_transport, '/ready', None)]:
        try:
            response = transport.request(path, payload)
            observations.append({'service': label, 'operation': path, 'readback': response.get('ready', response.get('state')), 'observed': True})
        except HTTPError as error:
            failures.append({'service': label, 'operation': path, 'status': error.code, 'body': error.read().decode(errors='replace')})
        except Exception as error:
            failures.append({'service': label, 'operation': path, 'exception': type(error).__name__, 'reason': str(error)})
    process_observations = []
    for path in sorted(context.runtime.glob('*.pid')):
        pid = int(path.read_text())
        alive = Path('/proc/' + str(pid)).exists()
        process_observations.append({'service': path.stem, 'pid': pid, 'alive': alive})
        if not alive:
            failures.append({'service': path.stem, 'kind': 'PROCESS_NOT_ALIVE', 'pid': pid})
    pending = context.runtime / 'state/ci/website-outbox.json'
    return {'state': 'OBSERVED' if not failures else 'FAILURES_OBSERVED', 'services': observations, 'processes': process_observations,
            'failures': failures, 'result_outbox_pending': pending.exists(), 'root_cause': 'Only recorded when supported by service evidence; HTTP status alone is not a cause.'}
