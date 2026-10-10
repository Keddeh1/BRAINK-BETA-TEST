"""MCP SDK stdio adapter over the existing authenticated VFS HTTP contract."""
import argparse
import json
from typing import Any
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from mcp.server.fastmcp import FastMCP

from braink.core.rings import Ring, RingLevel
from braink.runtime.executor import RuntimeExecutor


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, new_url):
        return None


class VFSHTTPBackend:
    def __init__(self, base_url, token=None):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/')):
            raise ValueError('invalid_vfs_origin')
        if parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
            raise ValueError('remote_vfs_requires_https')
        self.base_url = base_url.rstrip('/')
        self.token = token

    def request(self, method, path, body=None):
        headers = {'Accept': 'application/json'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with build_opener(NoRedirect()).open(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            # Preserve backend conflict/authentication semantics without exposing credentials.
            try:
                detail = json.load(error).get('error', 'backend_error')
            except (ValueError, AttributeError):
                detail = 'backend_error'
            raise ValueError(f'VFS HTTP {error.code}: {detail}') from None


def create_mcp(backend, executor=None):
    executor = executor or RuntimeExecutor(Ring(RingLevel.RING_2))
    service = FastMCP('BRAINK VFS Runtime')

    def invoke(method, path, body=None):
        return executor.execute(backend.request, method, path, body,
                                target_ring=RingLevel.RING_2)

    @service.tool()
    def vfs_status() -> dict[str, Any]:
        """Read the existing VFS service status."""
        return invoke('GET', '/status')

    @service.tool()
    def vfs_resolve(path: str) -> dict[str, Any]:
        """Resolve a contextual path binding, rather than digest-only provenance."""
        return invoke('GET', '/paths/' + quote(path.lstrip('/'), safe='/'))

    @service.tool()
    def vfs_binding_history(path: str) -> dict[str, Any]:
        """Read verified contextual binding versions and receipt references."""
        return invoke('GET', '/bindings/' + quote(path.lstrip('/'), safe='/'))

    @service.tool()
    def vfs_write(path: str, content_b64: str, source: str,
                  predecessor: str | None = None,
                  media_type: str = 'application/octet-stream',
                  continuation_id: str | None = None,
                  expected_version: int | None = None) -> dict[str, Any]:
        """Commit through VFS; reuse a continuation ID only for identical retry inputs."""
        return invoke('POST', '/artifacts', dict(
            path=path, content_b64=content_b64, source=source,
            predecessor=predecessor, media_type=media_type,
            continuation_id=continuation_id, expected_version=expected_version))

    @service.tool()
    def vfs_verify(digest: str) -> dict[str, Any]:
        """Run the existing observer readback and return its receipt."""
        return invoke('POST', '/verify', {'digest': digest})

    @service.tool()
    def runtime_status() -> dict[str, Any]:
        """Read this adapter's existing executor ring and successful operation count."""
        return {'ring': executor.current_ring.level.name,
                'operation_count': executor.operation_count}

    return service


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vfs-url', default='http://127.0.0.1:8787')
    parser.add_argument('--token-file', required=True)
    args = parser.parse_args()
    token = Path(args.token_file).read_text(encoding='utf-8').strip()
    if not token:
        raise ValueError('empty_token_file')
    create_mcp(VFSHTTPBackend(args.vfs_url, token)).run(transport='stdio')


if __name__ == '__main__':
    main()
