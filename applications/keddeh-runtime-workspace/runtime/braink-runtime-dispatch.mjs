import {ownerCI,workerCI} from './braink-ci-store.mjs';
import {topologyStore} from './workspace-topology-store.mjs';
import {architectureStore} from './braink-architecture-store.mjs';
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'private,no-store'}});
export async function verifyRuntimeTransport(db,bucket){
 if(!db||!bucket)return json({error:'STORAGE_UNAVAILABLE'},503);
 const id=crypto.randomUUID(),key='braink-runtime-probes/'+id,body=JSON.stringify({schema:'braink.runtime-probe.v1',id});
 let databaseVerified=false,objectVerified=false;
 try{
  await db.prepare('CREATE TABLE IF NOT EXISTS braink_runtime_probes(id TEXT PRIMARY KEY,document TEXT NOT NULL)').run();
  await db.prepare('INSERT INTO braink_runtime_probes VALUES(?,?)').bind(id,body).run();
  databaseVerified=(await db.prepare('SELECT document FROM braink_runtime_probes WHERE id=?').bind(id).first())?.document===body;
  await bucket.put(key,body);const object=await bucket.get(key);
  objectVerified=!!object&&new TextDecoder().decode(await object.arrayBuffer())===body;
  return json({schema:'braink.runtime-readiness.v1',runtime:'Keddeh Systems Runtime',database_readback:databaseVerified,object_readback:objectVerified,ready:databaseVerified&&objectVerified},databaseVerified&&objectVerified?200:503);
 }catch{return json({error:'RUNTIME_READBACK_FAILED',database_readback:databaseVerified,object_readback:objectVerified},503)}
 finally{await Promise.allSettled([db.prepare('DELETE FROM braink_runtime_probes WHERE id=?').bind(id).run(),bucket.delete(key)])}
}
export async function runtimeWebsite(request,env){
 if(!env.BRAINK_CI_WEBSITE_TOKEN||request.headers.get('Authorization')!=='Bearer '+env.BRAINK_CI_WEBSITE_TOKEN)return json({error:'UNAUTHORIZED'},401);
 try{
  if(request.method==='POST'){
   const value=await request.clone().json();
   if(value.op==='verify-transport')return verifyRuntimeTransport(env.DB,env.BUCKET);
   if(value.op==='worker'){
    if(!value.value||typeof value.value!=='object'||Array.isArray(value.value))return json({error:'INVALID_RUNTIME_REQUEST'},400);
    const forwarded=new Request(request.url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value.value)});
    return dispatchWorker(forwarded,env);
   }
   if(value.op==='architecture-status')return architectureStore(env.DB,env.BUCKET,value);
  }
  return ownerCI(request,env.DB,env.BUCKET);
 }catch{return json({error:'INVALID_RUNTIME_REQUEST'},400)}
}
export async function runtimeWorker(request,env){
 if(!env.BRAINK_CI_AGENT_TOKEN||request.headers.get('Authorization')!=='Bearer '+env.BRAINK_CI_AGENT_TOKEN)return json({error:'UNAUTHORIZED'},401);
 if(request.method!=='POST')return json({error:'METHOD_NOT_ALLOWED'},405);
 return dispatchWorker(request,env);
}
async function dispatchWorker(request,env){
 try{
  const value=await request.clone().json();
  if(value.op==='topology-observation')return topologyStore(env.DB,env.BUCKET,value);
  if(['architecture-status','architecture-observation'].includes(value.op))return architectureStore(env.DB,env.BUCKET,value);
  if(['submit','list','artifact'].includes(value.op)){
   const url=new URL(request.url);if(value.op==='artifact'){url.searchParams.set('job',value.id);url.searchParams.set('artifact',value.path)}
   const forwarded=new Request(url,{method:value.op==='submit'?'POST':'GET',headers:{'Content-Type':'application/json'},body:value.op==='submit'?JSON.stringify(value):undefined});
   return ownerCI(forwarded,env.DB,env.BUCKET);
  }
  return workerCI(request,env.DB,env.BUCKET);
 }catch{return json({error:'INVALID_RUNTIME_REQUEST'},400)}
}
