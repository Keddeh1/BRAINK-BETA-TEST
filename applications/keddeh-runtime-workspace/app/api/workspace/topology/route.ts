import {env} from 'cloudflare:workers';
import {protect} from '@/lib/20260927T0036Z__KEDDEH-COM__BRAINK__ACCESS';
import {topologyStore} from '@/lib/workspace-topology-store.mjs';
export const dynamic='force-dynamic';
export const GET=protect(async(request)=>{
 const response=await topologyStore(env.DB,env.BUCKET,{op:'topology-status'});
 if(!response.ok)return response;
 const document=await response.json() as {instances:Array<Record<string,unknown>>;nodes:Array<{id:string}>;[key:string]:unknown};
 const id=new URL(request.url).searchParams.get('instance');
 if(id){const instance=document.instances.find(row=>row.id===id);if(!instance)return Response.json({error:'INSTANCE_NOT_FOUND'},{status:404});return Response.json({instance,definition:document.nodes.find(node=>node.id===instance.definition_id),observed_at:document.observed_at,transport_digest:document.transport_digest})}
 return Response.json({...document,instances:document.instances.map(({id,definition_id,occurrence,state})=>({id,definition_id,occurrence,state}))});
});
