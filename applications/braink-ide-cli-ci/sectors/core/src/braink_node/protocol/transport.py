"""Transport for existing owner VFS and the deployment mesh subscription service."""
import base64
import json
import hashlib
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from braink_node.canonical import canonical_bytes


class JSONTransport:
    def __init__(self, endpoint, token=None, timeout=30):
        self.endpoint = endpoint.rstrip('/')
        self.token = token
        self.timeout = timeout

    def request(self, path, payload=None):
        headers = {'Content-Type': 'application/json', 'User-Agent': 'BRAINK-Protocol/1'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        request = Request(self.endpoint + path, data=None if payload is None else canonical_bytes(payload), headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            return json.load(response)


class HubSubscription:
    def __init__(self, transport):
        self.transport = transport

    def subscribe(self, instance, prefix):
        try:
            old = self.transport.request('/subscriptions/' + instance)
        except HTTPError as error:
            detail = json.load(error)
            if error.code not in (400, 404) or 'unknown_subscriber' not in detail.get('error', ''):
                raise
            old = {'cursor': 0}
        row = self.transport.request('/subscriptions', {'subscriber': instance, 'prefix': prefix, 'cursor': old['cursor']})
        observed = self.transport.request('/subscriptions/' + instance)
        if observed['prefix'] != prefix or observed['cursor'] != row['cursor']:
            raise RuntimeError('VFS subscription readback differs')
        return observed

    def readback(self, digest, path):
        observed = self.transport.request('/verify', {'digest': digest})
        fetched = self.transport.request('/artifacts/' + digest)
        content = base64.b64decode(fetched['content_b64'], validate=True)
        resolved = self.transport.request('/paths' + path)
        if not observed['verified'] or resolved['artifact']['digest'] != digest or hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError('VFS resumed publication readback differs')
        return observed

    def publish(self, instance, path, document):
        content = canonical_bytes(document)
        result = self.transport.request('/artifacts', {'path': path, 'content_b64': base64.b64encode(content).decode(),
                                                     'source': instance, 'media_type': 'application/json'})
        # The existing owner service supplies actor and observer receipts independently.
        artifact = result['artifact']
        observed = self.transport.request('/verify', {'digest': artifact['digest']})
        fetched = self.transport.request('/artifacts/' + artifact['digest'])
        if not observed['verified'] or base64.b64decode(fetched['content_b64']) != content:
            raise RuntimeError('VFS publication readback differs')
        return {'actor': result, 'observer': observed}
