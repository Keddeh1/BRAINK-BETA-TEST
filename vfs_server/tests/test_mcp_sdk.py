"""Qualify the real SDK stdio transport against the existing HTTP VFS server."""
import asyncio
import base64
import sys
import tempfile
import threading
import unittest
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    raise unittest.SkipTest('Install the optional MCP SDK extra to qualify its transport')

from vfs_server.server import create_server


class MCPSDKTests(unittest.TestCase):
    def test_sdk_transport_retry_conflict_auth_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            token = root / 'token'
            token.write_text('qualification-token')
            wrong = root / 'wrong-token'
            wrong.write_text('wrong-token')
            server = create_server(root / 'vfs', port=0, token_file=str(token))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                async def qualify(token_file, authorized):
                    parameters = StdioServerParameters(command=sys.executable, args=[
                        '-m', 'braink.mcp_service', '--vfs-url',
                        f'http://127.0.0.1:{server.server_port}',
                        '--token-file', str(token_file)])
                    async with stdio_client(parameters) as (reader, writer):
                        async with ClientSession(reader, writer) as session:
                            await session.initialize()
                            tools = await session.list_tools()
                            self.assertEqual({t.name for t in tools.tools}, {
                                'vfs_status', 'vfs_write', 'vfs_resolve',
                                'vfs_binding_history', 'vfs_verify', 'runtime_status'})
                            arguments = dict(path='/mcp/context', source='source://sdk',
                                content_b64=base64.b64encode(b'shared bytes').decode(),
                                continuation_id='sdk-retry', expected_version=0)
                            first = await session.call_tool('vfs_write', arguments)
                            if not authorized:
                                self.assertTrue(first.isError)
                                self.assertIn('401', first.content[0].text)
                                status = await session.call_tool('runtime_status')
                                self.assertEqual(status.structuredContent['operation_count'], 0)
                                return
                            self.assertFalse(first.isError)
                            retry = await session.call_tool('vfs_write', arguments)
                            self.assertEqual(first.structuredContent, retry.structuredContent)
                            changed = await session.call_tool('vfs_write', dict(arguments, source='changed'))
                            self.assertTrue(changed.isError)
                            self.assertIn('409', changed.content[0].text)
                            history = await session.call_tool('vfs_binding_history', {'path':'/mcp/context'})
                            self.assertFalse(history.isError, history.content)
                            self.assertEqual(len(history.structuredContent['history']), 1)
                            resolved = await session.call_tool('vfs_resolve', {'path':'/mcp/context'})
                            self.assertEqual(resolved.structuredContent['artifact']['source'], 'source://sdk')
                            verified = await session.call_tool('vfs_verify', {
                                'digest': first.structuredContent['artifact']['digest']})
                            self.assertTrue(verified.structuredContent['verified'])
                asyncio.run(qualify(token, True))
                asyncio.run(qualify(wrong, False))
                self.assertEqual(server.RequestHandlerClass.store.verify_receipt_chain()['count'], 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
