import {env} from 'cloudflare:workers';
import {protect} from '@/lib/20260927T0036Z__KEDDEH-COM__BRAINK__ACCESS';
import {cloudRegistry,cloudAgentDispatch,cloudAgentReceipt} from '@/lib/cloud-agent-controls';
import {architectureStore} from '@/lib/braink-architecture-store.mjs';
export const dynamic='force-dynamic';
export const GET=protect(async(request)=>{
 try {
  if(!env.DB)return Response.json({error:'STORAGE_UNAVAILABLE'},{status:503});
  const url=new URL(request.url);
  if(url.searchParams.has('receipt'))return Response.json(await cloudAgentReceipt(url.searchParams.get('receipt')!));
  if(url.searchParams.get('view')==='architecture')return architectureStore(env.DB,env.BUCKET,{op:'architecture-status'});
  const registry=await cloudRegistry();
  const [namespaces,records]=await Promise.all([
   env.DB.prepare('SELECT id,foundry_id,version,snapshot_digest,last_command,updated_at FROM agent_namespaces ORDER BY updated_at DESC LIMIT 200').all(),
   env.DB.prepare("SELECT id,state,created_at,updated_at FROM mcp_commands WHERE state LIKE 'AGENT_%' ORDER BY created_at DESC LIMIT 100").all()
  ]);
  return Response.json({...registry,namespaces:namespaces.results,records:records.results});
 }catch(error){return Response.json({error:error instanceof Error?error.message:'WORKSPACE_READ_FAILED'},{status:503})}
});
export const POST=protect(async(request)=>{
 try {
  const value=await request.json();
  if(!value||typeof value!=='object'||Array.isArray(value))return Response.json({error:'INPUT_OBJECT_REQUIRED'},{status:400});
  const result=await cloudAgentDispatch(value as Record<string,unknown>,{source:'OWNER_AUTHENTICATED_WORKSPACE',scope:'KEDDEH_AGENT_DISPATCH'});
  return Response.json(result);
 }catch(error){return Response.json({error:error instanceof Error?error.message:'EXECUTION_FAILED'},{status:400})}
});
