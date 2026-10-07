import json
import os
import shutil
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secrets import compare_digest

from braink_node.canonical import canonical_bytes
from braink_node.protocol.catalogue import digest
from .context import Context


def capacity(context):
    memory = {}
    with open('/proc/meminfo') as source:
        for line in source:
            key, value = line.split(':', 1)
            if key in {'MemTotal', 'MemAvailable'}:
                memory[key] = int(value.strip().split()[0]) * 1024
    return {'host': socket.gethostname(), 'host_id': digest({'hostname': socket.gethostname(), 'runtime_root': str(context.runtime)}),
            'cpus_available': len(os.sched_getaffinity(0)), 'load': list(os.getloadavg()), 'memory': memory,
            'storage_available': shutil.disk_usage(context.runtime).free, 'catalogue_sha256': context.catalogue()['definition_sha256']}


def server(config, host, port):
    context = Context(config)
    token = json.loads((context.runtime / 'worker-credential.json').read_text())['agent']
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, document):
            data = canonical_bytes(document)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if not compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                return self.send(401, {'error': 'Unauthorized'})
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
                if self.path == '/capacity':
                    result = capacity(context)
                elif self.path == '/place':
                    if payload['catalogue_sha256'] != context.catalogue()['definition_sha256']:
                        return self.send(409, {'error': 'Installed source revision differs'})
                    if payload['sector'] not in {'core', 'cli', 'ide', 'ci'}:
                        raise ValueError('Unknown colony sector')
                    result = context.manager.deploy(context.catalogue(), (payload['sector'],))
                else:
                    return self.send(404, {'error': 'Unknown operation'})
                self.send(200, result)
            except (ValueError, KeyError) as error:
                self.send(400, {'error': str(error)})
            except Exception as error:
                self.send(500, {'error': type(error).__name__, 'reason': str(error)})
    return ThreadingHTTPServer((host, port), Handler)
