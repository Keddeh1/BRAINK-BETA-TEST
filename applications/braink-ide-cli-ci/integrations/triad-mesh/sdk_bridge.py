"""Official MCP client; no transport or signature substitutes."""
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def _exchange(url,request,identity):
    async with streamable_http_client(url) as (reader,writer,_):
        async with ClientSession(reader,writer) as client:
            initialized=await client.initialize()
            args={'request_id':'triad-'+request.request_id,'levels':list(request.warrant_levels),
                  'environment':identity,'family':'TRIAD/GRPC','custody':'git:'+request.target_git_revision}
            result=await client.call_tool('resolve_q32',args)
            if result.isError:raise RuntimeError('RESOLVE_REJECTED')
            value=json.loads(result.content[0].text)
            read=await client.call_tool('read_resolve_receipt',{'artifact_digest':value['artifact_digest']})
            if read.isError:raise RuntimeError('RESOLVE_READBACK_REJECTED')
            verified=json.loads(read.content[0].text)
            if verified['result']!=value['result'] or not verified['chain']['verified']:
                raise RuntimeError('RESOLVE_RECEIPT_DIFFERS')
            return {'protocol_version':initialized.protocolVersion,'artifact_digest':value['artifact_digest'],
                    'receipt_chain':verified['chain'],'substrate_identity':value['result']['substrate_identity']}


def exchange(url,request,identity):
    return asyncio.run(asyncio.wait_for(_exchange(url,request,identity),timeout=15))
