import fcntl
import importlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError

from .context import Context

TARGETS = {
    'reconciliation': 'Architecture reconciliation',
    'evolution': 'Function and dependency evolution',
    'continuity': 'VFS subscription continuity',
    'feedback': 'IL-LLM relational feedback',
    'ceremonies': 'Ceremony recovery and replay',
    'delivery': 'Self-hosted sector delivery',
    'diagnostics': 'Service diagnosis and recovery',
    'placement': 'Colony placement and resource adaptation',
    'recovery': 'Host recovery and reconstruction',
    'development': 'Architecture-driven development cycles',
}
ORDER = ('evolution', 'ceremonies', 'reconciliation', 'continuity', 'diagnostics', 'feedback', 'delivery', 'placement', 'recovery', 'development')


class AutomationEngine:
    def __init__(self, config):
        self.context = Context(config)

    def run(self, target='all'):
        selected = ORDER if target == 'all' else tuple(target) if isinstance(target, (list, tuple)) else (target,)
        if any(name not in TARGETS for name in selected):
            raise ValueError('Unknown architecture target')
        lock = (self.context.root / 'cycle.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            self.context._catalogue = None
            results = []
            for name in selected:
                try:
                    module = importlib.import_module('braink_node.automation.' + name)
                    from braink_node.protocol.binding import FunctionBindings
                    from braink_node.protocol.catalogue import module_identity
                    catalogue = self.context.catalogue()
                    module_id = module_identity('braink_node.automation.' + name, 'run')
                    definition = catalogue['modules'][module_id]
                    occurrence = ['colony://braink-development/core', 'variant://braink-development/core', definition['family'], module_id]
                    instance = self.context.manager.instantiate(definition, occurrence)
                    bindings = FunctionBindings(catalogue)
                    bindings.bind(module_id, instance['instance'], module.run)
                    result = self.context.manager.invoke(instance['instance'], bindings, [self.context], context=instance['instance'])
                    result['module_instance'] = instance['instance']
                except Exception as error:
                    result = {'state': 'EXECUTION_ERROR', 'exception': type(error).__name__, 'reason': str(error)}
                    if isinstance(error, HTTPError):
                        result['service_response'] = {'status': error.code, 'endpoint': error.url, 'body': error.read().decode(errors='replace')}
                results.append(self.context.record(name, result))
            from braink_node.storage import atomic_write
            from braink_node.canonical import canonical_bytes
            if (self.context.root / 'activation-prepared.json').exists():
                activation = json.loads((self.context.root / 'activation-prepared.json').read_text())
                activation['state'] = 'READY_TO_RESTART'
                atomic_write(self.context.runtime / 'activation-request.json', canonical_bytes(activation))
            return {'schema': 'braink.automation-cycle.v1', 'results': results, 'completed': not any(row['state'] == 'EXECUTION_ERROR' for row in results)}
        finally:
            lock.close()

    def status(self):
        return {'schema': 'braink.automation-status.v1', 'targets': [{'id': name, 'title': title, 'evidence': self.context.latest(name)} for name, title in TARGETS.items()]}

    def serve(self, stop):
        while not stop.is_set():
            self.context.flush_evidence()
            due = []
            for target in ORDER:
                prior = self.context.latest(target)
                interval = self.context.config['target_intervals_seconds'][target]
                if prior is None or prior['state'] in {'EXECUTION_ERROR', 'RETRY_REQUIRED'} or time.time() - prior['created'] >= interval:
                    due.append(target)
            if due:
                result = self.run(due)
                print(json.dumps({'event': 'architecture-cycle', 'completed': result['completed'], 'targets': [{'target': row['target'], 'state': row['state']} for row in result['results']]}), flush=True)
            stop.wait(self.context.config['cycle_interval_seconds'])
