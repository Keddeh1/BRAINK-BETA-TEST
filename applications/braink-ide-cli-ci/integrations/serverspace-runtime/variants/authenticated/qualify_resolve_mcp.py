"""Official SDK client exercises online services, durable replay and isolation."""
import asyncio
import json
from pathlib import Path
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client


def unpack(result):
    assert not result.isError
    return json.loads(result.content[0].text)


async def existing_status():
    root=Path('/workspace/braink-setup/service-activation/source')
    parameters=StdioServerParameters(command='python',args=[str(root/'mcp_service.py'),'--manifest',str(root/'services.json')])
    async with stdio_client(parameters) as (reader,writer):
        async with ClientSession(reader,writer) as client:
            initialized=await client.initialize()
            result=unpack(await client.call_tool('service_status',{}))
            return {'sdk_server':initialized.serverInfo.name,'observed_services':len(result['services'])}


async def qualify(url,identity):
    async with streamable_http_client(url) as (reader,writer,_):
        async with ClientSession(reader,writer) as client:
            initialized=await client.initialize()
            tools=await client.list_tools()
            args={'request_id':'qualification-v1','levels':[1,2,3,4],
                  'environment':'owner-local-qualification','family':'SERVERSPACE/RESOLVE',
                  'custody':'source://795479a/consilience'}
            first=unpack(await client.call_tool('resolve_q32',args))
            replay=unpack(await client.call_tool('resolve_q32',args))
            assert replay['replayed'] and replay['artifact_digest']==first['artifact_digest']
            simultaneous=await asyncio.gather(*[client.call_tool('resolve_q32',args) for _ in range(16)])
            assert all(unpack(item)['artifact_digest']==first['artifact_digest'] and unpack(item)['replayed'] for item in simultaneous)
            readback=unpack(await client.call_tool('read_resolve_receipt',{'artifact_digest':first['artifact_digest']}))
            assert readback['result']==first['result'] and readback['chain']['verified']
            assert first['result']['arithmetic']['raw_q32']==13649637264
            assert first['result']['request']['instance']==identity
            conflict=await client.call_tool('resolve_q32',{**args,'levels':[4]})
            assert conflict.isError
            absent=await client.call_tool('resolve_q32',{**args,'request_id':'invalid-zero','levels':[0]})
            assert absent.isError
            for invalid in (True,2.0,'2'):
                rejected=await client.call_tool('resolve_q32',{**args,'request_id':'invalid-type','levels':[invalid]})
                assert rejected.isError
            return {'url':url,'identity':identity,'server':initialized.serverInfo.name,
                    'tools':[tool.name for tool in tools.tools],'artifact_digest':first['artifact_digest'],
                    'receipt_chain':readback['chain'],'durable_replay':True,'concurrent_replays':len(simultaneous),
                    'conflict_rejected':True,'zero_warrant_rejected':True,'coercion_rejected':True}


async def main():
    config=json.loads(Path('/workspace/braink-setup/families/SERVERSPACE/runtime/resolve-deployment.json').read_text())
    rows=[await qualify(row['url'],row['identity']) for row in config['instances']]
    assert len({row['artifact_digest'] for row in rows})==len(rows)
    print(json.dumps({'observed_at':time.time(),'existing_mcp':await existing_status(),
                      'instances':rows,'independent_contexts_retained':True},indent=2))


if __name__=='__main__':asyncio.run(main())
